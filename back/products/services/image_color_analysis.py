import json
import logging
import math
from collections import Counter
from io import BytesIO
from types import SimpleNamespace

import openai
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from diagnosis.ai_clients.openai_compatible import (
    AIClientConfigurationError,
    AIClientParseError,
    AIClientResponseError,
    OpenAICompatibleClient,
)
from diagnosis.domain.tone_profiles import build_tone_result_payload
from diagnosis.services.primary import get_primary_diagnosis_for_user
from products.models import Product, ProductImageAnalysis, ProductImageAnalysisOption
from products.services.color_metrics import build_color_metrics, normalize_hex, public_grade_from_score
from products.services.recommendation import build_user_tone_profile, calculate_option_match


logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_FORMATS = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'WEBP': 'image/webp',
}
PENDING_REASON = 'Color verification needed'
ANALYSIS_DISCLAIMER = (
    'This result is based on the uploaded chart image. Actual appearance may vary by lighting, '
    'display, and product finish.'
)
FALLBACK_WARNING = {
    'code': 'AI_VISION_UNAVAILABLE_FALLBACK_USED',
    'message': 'AI vision was unavailable, so colors were extracted locally from the image.',
}
LOCAL_ANALYSIS_TYPE = 'IMAGE_COLOR_CHART'
LOCAL_PRODUCT_SOURCE = 'uploaded_image'
LOCAL_PROCESSING_MAX_SIDE = 1200
LOCAL_MIN_CANDIDATES = 5
LOCAL_MAX_CANDIDATES = 20

PRODUCT_IMAGE_ANALYSIS_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'product_name': {'type': 'string'},
        'brand_name': {'type': 'string'},
        'chart_labels': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'warm_label': {'type': 'string'},
                'cool_label': {'type': 'string'},
                'light_label': {'type': 'string'},
                'deep_label': {'type': 'string'},
                'best_region_labels': {'type': 'array', 'items': {'type': 'string'}},
                'season_labels': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['warm_label', 'cool_label', 'light_label', 'deep_label', 'best_region_labels', 'season_labels'],
        },
        'options': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'option_name': {'type': 'string'},
                    'display_name': {'type': 'string'},
                    'confidence': {'type': 'number'},
                    'ai_estimated_hex': {'type': 'string'},
                    'blob_box': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'x': {'type': 'number'},
                            'y': {'type': 'number'},
                            'width': {'type': 'number'},
                            'height': {'type': 'number'},
                        },
                        'required': ['x', 'y', 'width', 'height'],
                    },
                },
                'required': ['option_name', 'display_name', 'confidence', 'ai_estimated_hex', 'blob_box'],
            },
        },
    },
    'required': ['product_name', 'brand_name', 'chart_labels', 'options'],
}


class NoColorCandidatesFoundError(RuntimeError):
    pass


class ProductImageAnalysisPersonalizationError(RuntimeError):
    pass


class ProductImageAnalysisPipeline:
    def __init__(self, analysis):
        self.analysis = analysis
        self.model_name = resolve_product_image_analysis_model()

    def run(self):
        logger.info(
            'Product image analysis started. analysis_id=%s model=%r category=%s',
            self.analysis.id,
            self.model_name,
            self.analysis.category,
        )
        image_bytes, image_format, image = validate_analysis_image(self.analysis.uploaded_image)
        local_candidates = extract_color_blobs_from_image(image)
        logger.info(
            'Product image local extraction complete. analysis_id=%s candidates=%s',
            self.analysis.id,
            len(local_candidates),
        )
        if not local_candidates:
            raise NoColorCandidatesFoundError('No usable color candidates were found in the uploaded image.')

        ai_payload, ai_used, warning, ai_error = self._maybe_extract_chart_structure(image_bytes, image_format)
        merged_options = merge_detected_options(ai_payload.get('options') or [], local_candidates) if ai_payload else local_candidates
        if not merged_options:
            merged_options = local_candidates

        self.analysis.raw_ai_response = build_analysis_record(
            ai_payload=ai_payload,
            ai_used=ai_used,
            warning=warning,
            ai_error=ai_error,
            local_candidate_count=len(local_candidates),
        )
        self.analysis.product_name = (
            self.analysis.product_name
            or clean_text((ai_payload or {}).get('product_name'))
            or 'Uploaded image analysis'
        )
        self.analysis.brand_name = self.analysis.brand_name or clean_text((ai_payload or {}).get('brand_name'))
        self.analysis.save(update_fields=['raw_ai_response', 'product_name', 'brand_name', 'updated_at'])
        logger.info(
            'Product image analysis metadata saved. analysis_id=%s ai_used=%s warning=%s',
            self.analysis.id,
            ai_used,
            warning['code'] if warning else None,
        )

        user_profile, user_tone = user_profile_payload(self.analysis.user)
        try:
            replace_analysis_options(
                self.analysis,
                merged_options,
                user_profile=user_profile,
                category=self.analysis.category,
                image=image,
                mark_all_user_edited=False,
            )
            logger.info(
                'Product image options saved. analysis_id=%s option_count=%s personalized=%s',
                self.analysis.id,
                len(merged_options),
                bool(user_profile),
            )
            payload = build_product_image_analysis_payload(self.analysis, user_profile=user_profile, user_tone=user_tone)
        except ProductImageAnalysisPersonalizationError as exc:
            logger.warning(
                'Product image personalization failed; retrying without personalization. analysis_id=%s error=%s',
                self.analysis.id,
                exc,
            )
            replace_analysis_options(
                self.analysis,
                merged_options,
                user_profile=None,
                category=self.analysis.category,
                image=image,
                mark_all_user_edited=False,
            )
            payload = build_product_image_analysis_payload(self.analysis, user_profile=None, user_tone=None)
        logger.info(
            'Product image analysis completed. analysis_id=%s response_options=%s ai_used=%s personalized=%s',
            self.analysis.id,
            len(payload.get('options') or []),
            payload.get('ai_used'),
            payload.get('personalized'),
        )
        return payload

    def _maybe_extract_chart_structure(self, image_bytes, image_format):
        if not getattr(settings, 'PRODUCT_IMAGE_ANALYSIS_ENABLE_AI', True):
            logger.info('Product image AI disabled; skipping vision step. analysis_id=%s', self.analysis.id)
            return None, False, None, None
        logger.info(
            'Product image AI vision attempt. analysis_id=%s model=%r base_url=%s',
            self.analysis.id,
            self.model_name,
            getattr(settings, 'OPENAI_BASE_URL', None),
        )
        try:
            payload = self._extract_chart_structure(image_bytes, image_format)
        except (
            openai.OpenAIError,
            AIClientConfigurationError,
            AIClientParseError,
            AIClientResponseError,
            TimeoutError,
            OSError,
            RuntimeError,
        ) as exc:
            logger.warning(
                'Product image AI vision failed; using local extraction fallback. analysis_id=%s model=%r error=%s',
                self.analysis.id,
                self.model_name,
                exc,
            )
            return None, False, FALLBACK_WARNING, {'type': exc.__class__.__name__, 'message': str(exc)}
        logger.info(
            'Product image AI vision succeeded. analysis_id=%s detected_options=%s',
            self.analysis.id,
            len((payload or {}).get('options') or []),
        )
        return payload, True, None, None

    def _extract_chart_structure(self, image_bytes, image_format):
        prompt = build_image_analysis_prompt()
        mime_type = SUPPORTED_IMAGE_FORMATS[image_format]
        return OpenAICompatibleClient(model=self.model_name).create_vision_json(
            image_bytes=image_bytes,
            mime_type=mime_type,
            prompt=prompt,
            schema=PRODUCT_IMAGE_ANALYSIS_SCHEMA,
            schema_name='product_color_chart_analysis',
            system_prompt=(
                'You analyze cosmetic product shade chart images. '
                'Return only valid JSON. '
                'Read visible option names and locate the color blob for each option. '
                'Use the image structure for boxes and text extraction, not for final color math.'
            ),
            temperature=0.1,
            response_format_type='json_object',
            validate_schema=True,
            debug_label='product image',
        )


def resolve_product_image_analysis_model():
    return (
        getattr(settings, 'PRODUCT_IMAGE_ANALYSIS_MODEL', None)
        or getattr(settings, 'AI_DIAGNOSIS_MODEL', None)
        or getattr(settings, 'OPENAI_MODEL', None)
    )


def validate_analysis_image(uploaded_image):
    if not uploaded_image:
        raise ValidationError('An image file is required.')
    try:
        uploaded_image.open('rb')
        image_bytes = uploaded_image.read()
        uploaded_image.seek(0)
        image = Image.open(BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError('The uploaded image could not be opened.') from exc

    image_format = (image.format or '').upper()
    image = image.convert('RGBA')
    if image_format not in SUPPORTED_IMAGE_FORMATS:
        raise ValidationError('Only JPG, PNG, and WEBP images are supported.')
    if image.width < 80 or image.height < 80:
        raise ValidationError('The uploaded image is too small.')
    return image_bytes, image_format, image


def extract_color_blobs_from_image(image):
    cv2 = _load_cv2()
    if cv2 is not None:
        candidates = _extract_color_blobs_with_cv2(image, cv2)
        if candidates:
            return candidates[:LOCAL_MAX_CANDIDATES]
    return _extract_color_blobs_with_pillow(image)[:LOCAL_MAX_CANDIDATES]


def build_analysis_record(*, ai_payload, ai_used, warning, ai_error, local_candidate_count):
    payload = ai_payload or {
        'product_name': '',
        'brand_name': '',
        'chart_labels': {},
        'options': [],
    }
    payload['analysis_meta'] = {
        'analysis_type': LOCAL_ANALYSIS_TYPE,
        'ai_used': ai_used,
        'warning': warning,
        'ai_error': ai_error,
        'local_candidate_count': local_candidate_count,
    }
    return payload


def build_detected_options(raw_options):
    normalized = []
    seen_keys = set()
    for index, raw in enumerate(raw_options, start=1):
        option_name = clean_text(raw.get('option_name') or raw.get('display_name') or f'Option {index}')
        display_name = clean_text(raw.get('display_name') or option_name)
        key = f'{option_name.casefold()}|{display_name.casefold()}'
        if key in seen_keys:
            continue
        seen_keys.add(key)
        blob_box = normalize_blob_box(raw.get('blob_box') or {})
        normalized.append(
            {
                'option_name': option_name,
                'display_name': display_name,
                'confidence': normalize_confidence(raw.get('confidence')),
                'ai_estimated_hex': normalize_hex(raw.get('ai_estimated_hex')),
                'blob_box': blob_box,
                'sort_key': (blob_box['y'], blob_box['x']),
            }
        )
    normalized.sort(key=lambda item: item['sort_key'])
    return normalized


def merge_detected_options(raw_ai_options, local_options):
    ai_options = build_detected_options(raw_ai_options)
    if not ai_options:
        return local_options

    merged = []
    matched_local_indexes = set()

    for ai_option in ai_options:
        match_index = find_best_local_match(ai_option, local_options, matched_local_indexes)
        if match_index is not None:
            matched_local_indexes.add(match_index)
            local_option = local_options[match_index]
            merged.append(
                {
                    **local_option,
                    'option_name': ai_option['option_name'],
                    'display_name': ai_option['display_name'],
                    'confidence': ai_option['confidence'] if ai_option['confidence'] is not None else local_option.get('confidence'),
                }
            )
        else:
            merged.append(
                {
                    'option_name': ai_option['option_name'],
                    'display_name': ai_option['display_name'],
                    'confidence': ai_option['confidence'],
                    'ai_estimated_hex': ai_option.get('ai_estimated_hex', ''),
                    'blob_box': ai_option['blob_box'],
                    'chart_x': clamp_percent(ai_option['blob_box']['x'] + math.floor(ai_option['blob_box']['width'] / 2)),
                    'chart_y': clamp_percent(ai_option['blob_box']['y'] + math.floor(ai_option['blob_box']['height'] / 2)),
                }
            )

    unmatched_local = [local_options[index] for index in range(len(local_options)) if index not in matched_local_indexes]
    for offset, local_option in enumerate(unmatched_local, start=1):
        option_number = len(merged) + offset
        merged.append(
            {
                **local_option,
                'option_name': f'Option {option_number}',
                'display_name': f'Option {option_number}',
            }
        )

    merged.sort(key=lambda item: item.get('sort_key') or (item.get('chart_y', 100), item.get('chart_x', 100)))
    return merged


def find_best_local_match(ai_option, local_options, matched_local_indexes):
    best_index = None
    best_score = 0
    ai_center_x = ai_option['blob_box']['x'] + ai_option['blob_box']['width'] / 2
    ai_center_y = ai_option['blob_box']['y'] + ai_option['blob_box']['height'] / 2

    for index, local_option in enumerate(local_options):
        if index in matched_local_indexes:
            continue
        local_box = local_option['blob_box']
        overlap = box_iou(ai_option['blob_box'], local_box)
        local_center_x = local_box['x'] + local_box['width'] / 2
        local_center_y = local_box['y'] + local_box['height'] / 2
        distance = math.dist((ai_center_x, ai_center_y), (local_center_x, local_center_y))
        distance_score = max(0, 1 - (distance / 28))
        score = overlap * 3 + distance_score
        if score > best_score and (overlap >= 0.02 or distance <= 18):
            best_score = score
            best_index = index
    return best_index


def box_iou(left_box, right_box):
    left = max(left_box['x'], right_box['x'])
    top = max(left_box['y'], right_box['y'])
    right = min(left_box['x'] + left_box['width'], right_box['x'] + right_box['width'])
    bottom = min(left_box['y'] + left_box['height'], right_box['y'] + right_box['height'])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    left_area = left_box['width'] * left_box['height']
    right_area = right_box['width'] * right_box['height']
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def _extract_color_blobs_with_cv2(image, cv2):
    import numpy as np

    processed = prepare_processing_image(image)
    rgb = np.array(processed.convert('RGB'))
    height, width = rgb.shape[:2]
    total_pixels = height * width

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype('float32')
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    border_pixels = _collect_border_pixels(lab, width, height)
    background_lab = border_pixels.mean(axis=0)
    distance = np.linalg.norm(lab - background_lab, axis=2)
    rgb_spread = rgb.max(axis=2) - rgb.min(axis=2)

    mask = (
        (distance > 28)
        & (saturation > 35)
        & (value < 245)
        & (rgb_spread > 12)
    ).astype('uint8') * 255

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    component_count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    min_area = max(180, int(total_pixels * 0.0022))
    candidates = []

    for index in range(1, component_count):
        x, y, width_px, height_px, area = [int(value) for value in stats[index]]
        if area < min_area:
            continue
        if _reject_component(x, y, width_px, height_px, area, width, height):
            continue

        component_mask = labels[y:y + height_px, x:x + width_px] == index
        pixels = rgb[y:y + height_px, x:x + width_px][component_mask]
        representative_rgb = _representative_component_rgb(pixels)
        if representative_rgb is None:
            continue
        metrics = build_color_metrics(representative_rgb)
        if metrics['saturation'] < 15:
            continue

        centroid_x, centroid_y = centroids[index]
        blob_box = {
            'x': clamp_percent(x / width * 100),
            'y': clamp_percent(y / height * 100),
            'width': max(1, clamp_percent(width_px / width * 100)),
            'height': max(1, clamp_percent(height_px / height * 100)),
        }
        chart_x = clamp_percent(centroid_x / width * 100)
        chart_y = clamp_percent(centroid_y / height * 100)
        candidate_number = len(candidates) + 1
        candidates.append(
            {
                'option_name': f'Option {candidate_number}',
                'display_name': f'Option {candidate_number}',
                'hex_code': metrics['hex_code'],
                'color_source': ProductImageAnalysisOption.ColorSource.IMAGE_EXTRACTED,
                'confidence': round(min(0.95, 0.35 + (area / total_pixels) * 6), 2),
                'blob_box': blob_box,
                'chart_x': chart_x,
                'chart_y': chart_y,
                'sort_key': (chart_y, chart_x),
            }
        )

    candidates.sort(key=lambda item: item['sort_key'])
    return candidates


def _extract_color_blobs_with_pillow(image):
    import numpy as np

    processed = prepare_processing_image(image)
    rgb_image = processed.convert('RGB')
    hsv_image = processed.convert('HSV')
    rgb = np.array(rgb_image)
    hsv = np.array(hsv_image)
    width, height = rgb_image.size
    total_pixels = width * height

    border = _collect_border_pixels_rgb(rgb, width, height)
    background_rgb = border.mean(axis=0)
    distance = np.linalg.norm(rgb.astype('float32') - background_rgb.astype('float32'), axis=2)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    mask = (
        (distance > 30)
        & (saturation > 40)
        & (value < 245)
        & ((rgb.max(axis=2) - rgb.min(axis=2)) > 12)
    )
    positions = np.argwhere(mask)
    if positions.size == 0:
        return []

    pixel_rows = []
    for y, x in positions:
        red, green, blue = rgb[y, x]
        bucket_rgb = tuple(int(channel // 12 * 12) for channel in (red, green, blue))
        pixel_rows.append((bucket_rgb, x, y))

    grouped = {}
    for bucket_rgb, x, y in pixel_rows:
        entry = grouped.setdefault(bucket_rgb, {'xs': [], 'ys': []})
        entry['xs'].append(int(x))
        entry['ys'].append(int(y))

    min_pixels = max(120, int(total_pixels * 0.001))
    candidates = []
    for bucket_rgb, values in grouped.items():
        if len(values['xs']) < min_pixels:
            continue
        left = min(values['xs'])
        top = min(values['ys'])
        right = max(values['xs'])
        bottom = max(values['ys'])
        chart_x = clamp_percent(sum(values['xs']) / len(values['xs']) / width * 100)
        chart_y = clamp_percent(sum(values['ys']) / len(values['ys']) / height * 100)
        blob_box = {
            'x': clamp_percent(left / width * 100),
            'y': clamp_percent(top / height * 100),
            'width': max(1, clamp_percent((right - left + 1) / width * 100)),
            'height': max(1, clamp_percent((bottom - top + 1) / height * 100)),
        }
        metrics = build_color_metrics(bucket_rgb)
        if metrics['saturation'] < 15:
            continue
        candidate_number = len(candidates) + 1
        candidates.append(
            {
                'option_name': f'Option {candidate_number}',
                'display_name': f'Option {candidate_number}',
                'hex_code': metrics['hex_code'],
                'color_source': ProductImageAnalysisOption.ColorSource.IMAGE_EXTRACTED,
                'confidence': round(min(0.85, 0.25 + len(values['xs']) / total_pixels * 8), 2),
                'blob_box': blob_box,
                'chart_x': chart_x,
                'chart_y': chart_y,
                'sort_key': (chart_y, chart_x),
            }
        )

    candidates.sort(key=lambda item: item['sort_key'])
    return candidates


def _collect_border_pixels(lab, width, height):
    import numpy as np

    border = max(10, min(width, height) // 25)
    return np.concatenate(
        [
            lab[:border, :, :].reshape(-1, 3),
            lab[-border:, :, :].reshape(-1, 3),
            lab[:, :border, :].reshape(-1, 3),
            lab[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )


def _collect_border_pixels_rgb(rgb, width, height):
    import numpy as np

    border = max(10, min(width, height) // 25)
    return np.concatenate(
        [
            rgb[:border, :, :].reshape(-1, 3),
            rgb[-border:, :, :].reshape(-1, 3),
            rgb[:, :border, :].reshape(-1, 3),
            rgb[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )


def _reject_component(x, y, width_px, height_px, area, image_width, image_height):
    touches_edges = sum(
        [
            x <= 1,
            y <= 1,
            x + width_px >= image_width - 1,
            y + height_px >= image_height - 1,
        ]
    )
    if area > image_width * image_height * 0.35:
        return True
    if touches_edges >= 2 and area > image_width * image_height * 0.05:
        return True
    if min(width_px, height_px) <= 4:
        return True
    fill_ratio = area / max(1, width_px * height_px)
    aspect_ratio = max(width_px, height_px) / max(1, min(width_px, height_px))
    if fill_ratio < 0.16 and aspect_ratio > 5:
        return True
    if fill_ratio < 0.08:
        return True
    return False


def _representative_component_rgb(pixels):
    if len(pixels) == 0:
        return None

    filtered = []
    for red, green, blue in pixels:
        if is_background_pixel(red, green, blue):
            continue
        if red > 245 and green > 245 and blue > 245:
            continue
        if red < 15 and green < 15 and blue < 15:
            continue
        if max(red, green, blue) - min(red, green, blue) < 10:
            continue
        filtered.append((bucket(red), bucket(green), bucket(blue)))

    if not filtered:
        filtered = [(bucket(red), bucket(green), bucket(blue)) for red, green, blue in pixels]
    if not filtered:
        return None
    rgb, _ = Counter(filtered).most_common(1)[0]
    return rgb


def _load_cv2():
    try:
        import cv2
    except ImportError:
        return None
    return cv2


def prepare_processing_image(image):
    processed = image.convert('RGBA')
    longest_side = max(processed.width, processed.height)
    if longest_side > LOCAL_PROCESSING_MAX_SIDE:
        scale = LOCAL_PROCESSING_MAX_SIDE / float(longest_side)
        new_size = (
            max(1, int(round(processed.width * scale))),
            max(1, int(round(processed.height * scale))),
        )
        processed = processed.resize(new_size, Image.Resampling.LANCZOS)
    return processed


def normalize_blob_box(raw_box):
    x = clamp_percent(raw_box.get('x'))
    y = clamp_percent(raw_box.get('y'))
    width = max(1, clamp_percent(raw_box.get('width')))
    height = max(1, clamp_percent(raw_box.get('height')))
    if x + width > 100:
        width = max(1, 100 - x)
    if y + height > 100:
        height = max(1, 100 - y)
    return {'x': x, 'y': y, 'width': width, 'height': height}


def normalize_confidence(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(1.0, parsed)), 2)


def clamp_percent(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = 0
    return max(0, min(100, round(parsed)))


def clean_text(value):
    return ' '.join(str(value or '').strip().split())


def build_image_analysis_prompt():
    schema_text = json.dumps(PRODUCT_IMAGE_ANALYSIS_SCHEMA, ensure_ascii=False)
    return f"""
Analyze the uploaded cosmetic shade chart image.

Rules:
- Return only JSON matching the schema.
- Extract option names exactly as visible when possible, including Korean or English shade names.
- For each option, locate the main color blob for that option and return a normalized blob_box in percentages of the full image.
- Use blob_box to cover the colored region, not the text label.
- Read axis labels such as Warm, Cool, Light, Deep when visible.
- Read region labels such as WARM BEST, COOL BEST, NEUTRAL BEST and season labels when visible.
- If product or brand name is not visible, return an empty string.
- If a color looks visible but precise sampling may be hard, provide ai_estimated_hex as an approximate 6-digit HEX string. Otherwise return an empty string.

JSON Schema:
{schema_text}
""".strip()


def user_profile_payload(user):
    try:
        diagnosis = get_primary_diagnosis_for_user(user)
    except Exception:
        diagnosis = None
    if not diagnosis:
        return None, None

    try:
        tone_payload = build_tone_result_payload(
            diagnosis.tone_key or diagnosis.personal_color_code,
            (diagnosis.diagnosis_json or {}).get('second_tone_key'),
        )
        tone_payload['diagnosis_id'] = diagnosis.id
        user_profile = build_user_tone_profile(
            tone_key=tone_payload.get('tone_key'),
            second_tone_key=tone_payload.get('second_tone_key'),
            axis_profile=tone_payload.get('axis_profile'),
            range_profile=tone_payload.get('range_profile'),
        )
    except Exception as exc:
        logger.warning(
            'Product image personalization setup failed; continuing without user tone. user_id=%s diagnosis_id=%s error=%s',
            getattr(user, 'id', None),
            diagnosis.id,
            exc,
        )
        return None, None
    return user_profile, {
        'diagnosis_id': tone_payload.get('diagnosis_id'),
        'tone_key': tone_payload.get('tone_key'),
        'tone_label': tone_payload.get('tone_label'),
        'tone_name': tone_payload.get('tone_label'),
        'second_tone_key': tone_payload.get('second_tone_key'),
        'second_tone_label': tone_payload.get('second_tone_label'),
        'axis_profile': tone_payload.get('axis_profile'),
        'range_profile': tone_payload.get('range_profile'),
        'recommended_color_families': tone_payload.get('recommended_color_families', []),
        'caution_color_families': tone_payload.get('caution_color_families', []),
    }


@transaction.atomic
def replace_analysis_options(
    analysis,
    option_payloads,
    *,
    user_profile,
    category,
    image=None,
    mark_all_user_edited=False,
):
    existing_by_id = {option.id: option for option in analysis.options.all()}
    ProductImageAnalysisOption.objects.filter(analysis=analysis).delete()

    for payload in option_payloads:
        existing = existing_by_id.get(payload.get('id'))
        row = build_option_row(
            payload,
            category=category,
            user_profile=user_profile,
            image=image,
            existing=existing,
            mark_user_edited=mark_all_user_edited,
        )
        ProductImageAnalysisOption.objects.create(analysis=analysis, **row)
    if hasattr(analysis, '_prefetched_objects_cache'):
        analysis._prefetched_objects_cache.pop('options', None)


def build_option_row(payload, *, category, user_profile, image=None, existing=None, mark_user_edited=False):
    option_name = clean_text(payload.get('option_name') or payload.get('display_name') or 'Option')
    display_name = clean_text(payload.get('display_name') or option_name)
    hex_code = normalize_hex(payload.get('hex_code') or payload.get('ai_estimated_hex'))
    blob_box = normalize_blob_box(payload.get('blob_box') or {})
    chart_x = payload.get('chart_x')
    chart_y = payload.get('chart_y')
    if chart_x is None:
        chart_x = clamp_percent(blob_box['x'] + math.floor(blob_box['width'] / 2))
    if chart_y is None:
        chart_y = clamp_percent(blob_box['y'] + math.floor(blob_box['height'] / 2))

    sampled_rgb = None
    if image is not None:
        sampled_rgb = sample_representative_rgb(image, blob_box)

    confidence = normalize_confidence(payload.get('confidence'))
    if sampled_rgb:
        metrics = build_color_metrics(sampled_rgb)
        color_source = ProductImageAnalysisOption.ColorSource.IMAGE_EXTRACTED
        metrics_hex = metrics.get('hex_code')
    elif hex_code:
        metrics = build_color_metrics(hex_to_rgb_strict(hex_code))
        color_source = ProductImageAnalysisOption.ColorSource.AI_ESTIMATED
        metrics_hex = hex_code
    else:
        metrics = None
        color_source = ProductImageAnalysisOption.ColorSource.PENDING
        metrics_hex = ''

    existing_signature = {
        'option_name': existing.option_name if existing else '',
        'display_name': existing.display_name if existing else '',
        'hex_code': normalize_hex(existing.hex_code) if existing else '',
        'chart_x': existing.chart_x if existing else None,
        'chart_y': existing.chart_y if existing else None,
    }
    next_signature = {
        'option_name': option_name,
        'display_name': display_name,
        'hex_code': metrics_hex,
        'chart_x': chart_x,
        'chart_y': chart_y,
    }
    if mark_user_edited and (existing is None or existing_signature != next_signature):
        color_source = ProductImageAnalysisOption.ColorSource.USER_EDITED if metrics else ProductImageAnalysisOption.ColorSource.PENDING

    row = {
        'option_name': option_name,
        'display_name': display_name,
        'hex_code': metrics_hex,
        'color_source': color_source,
        'confidence': confidence if  color_source != ProductImageAnalysisOption.ColorSource.USER_EDITED else (existing.confidence if existing else None),
        'chart_x': chart_x,
        'chart_y': chart_y,
    }

    if metrics:
        row.update(
            {
                'brightness': metrics['brightness'],
                'saturation': metrics['saturation'],
                'warmth': metrics['warmth'],
                'coolness': metrics['coolness'],
                'depth': metrics['depth'],
                'softness': metrics['softness'],
                'contrast': metrics['contrast'],
            }
        )
        match = calculate_metrics_match(metrics, user_profile, category)
        row.update(match)
    else:
        row.update(
            {
                'brightness': None,
                'saturation': None,
                'warmth': None,
                'coolness': None,
                'depth': None,
                'softness': None,
                'contrast': None,
                'match_score': None,
                'grade': ProductImageAnalysisOption.Grade.PENDING,
                'reason': PENDING_REASON,
            }
        )
    return row


def calculate_metrics_match(metrics, user_profile, category):
    if not user_profile:
        return {'match_score': None, 'grade': '', 'reason': ''}

    option_like = SimpleNamespace(
        product=SimpleNamespace(category=category or Product.Category.ETC),
        analyzed_tone_tag=metrics.get('analyzed_tone_tag', ''),
        brightness=metrics.get('brightness'),
        saturation=metrics.get('saturation'),
        coolness=metrics.get('coolness'),
        warmth=metrics.get('warmth'),
        depth=metrics.get('depth'),
        softness=metrics.get('softness'),
        contrast=metrics.get('contrast'),
    )
    try:
        match = calculate_option_match(option_like, user_profile, category or Product.Category.ETC)
    except Exception as exc:
        raise ProductImageAnalysisPersonalizationError(
            f'Option scoring failed for uploaded image analysis: {exc}'
        ) from exc
    return {
        'match_score': match['match_score'],
        'grade': public_grade_from_score(match['match_score']),
        'reason': match['reason'],
    }


def sample_representative_rgb(image, blob_box):
    left = max(0, math.floor(image.width * blob_box['x'] / 100))
    top = max(0, math.floor(image.height * blob_box['y'] / 100))
    right = min(image.width, math.ceil(image.width * (blob_box['x'] + blob_box['width']) / 100))
    bottom = min(image.height, math.ceil(image.height * (blob_box['y'] + blob_box['height']) / 100))
    if right - left < 2 or bottom - top < 2:
        return None

    crop = image.crop((left, top, right, bottom))
    inner = shrink_crop(crop)
    pixels = list(inner.getdata())
    candidates = bucket_pixels(pixels, center_only=True)
    if not candidates:
        candidates = bucket_pixels(pixels, center_only=False)
    if not candidates:
        return None
    (red, green, blue), _ = Counter(candidates).most_common(1)[0]
    return red, green, blue


def shrink_crop(image):
    margin_x = max(1, image.width // 8)
    margin_y = max(1, image.height // 8)
    if image.width - margin_x * 2 < 2 or image.height - margin_y * 2 < 2:
        return image
    return image.crop((margin_x, margin_y, image.width - margin_x, image.height - margin_y))


def bucket_pixels(pixels, *, center_only):
    bucketed = []
    total = len(pixels)
    for index, pixel in enumerate(pixels):
        red, green, blue, alpha = pixel
        if alpha < 48:
            continue
        if center_only:
            position = index / total if total else 0
            if position < 0.1 or position > 0.9:
                continue
        if is_background_pixel(red, green, blue):
            continue
        if is_text_like_pixel(red, green, blue):
            continue
        bucketed.append((bucket(red), bucket(green), bucket(blue)))
    return bucketed


def bucket(value):
    return min(255, max(0, int(round(value / 12)) * 12))


def is_background_pixel(red, green, blue):
    red, green, blue = int(red), int(green), int(blue)
    if red > 238 and green > 238 and blue > 238 and max(red, green, blue) - min(red, green, blue) < 18:
        return True
    if red < 20 and green < 20 and blue < 20:
        return True
    if abs(red - green) < 10 and abs(green - blue) < 10 and red > 205:
        return True
    return False


def is_text_like_pixel(red, green, blue):
    red, green, blue = int(red), int(green), int(blue)
    spread = max(red, green, blue) - min(red, green, blue)
    if spread < 12 and red < 120:
        return True
    return False


def hex_to_rgb_strict(value):
    value = normalize_hex(value)
    if not value:
        raise ValidationError('A valid HEX color is required.')
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def build_product_image_analysis_payload(analysis, *, user_profile=None, user_tone=None):
    if user_profile is None or user_tone is None:
        user_profile, user_tone = user_profile_payload(analysis.user)

    options = [
        serialize_analysis_option(option, index=index, personalized=bool(user_profile))
        for index, option in enumerate(analysis.options.all(), start=1)
    ]
    best_option = select_best_option(options)
    raw_payload = analysis.raw_ai_response or {}
    raw_labels = raw_payload.get('chart_labels') or {}
    raw_meta = raw_payload.get('analysis_meta') or {}
    confirmed = analysis.status == ProductImageAnalysis.Status.CONFIRMED
    return {
        'analysis_id': analysis.id,
        'success': True,
        'source': 'IMAGE_CHART',
        'analysis_type': raw_meta.get('analysis_type') or LOCAL_ANALYSIS_TYPE,
        'ai_used': bool(raw_meta.get('ai_used')),
        'warning': raw_meta.get('warning'),
        'confirmed': confirmed,
        'review_required': True,
        'analysis_status': 'CONFIRMED' if confirmed else 'DRAFT',
        'uploaded_image_url': analysis.uploaded_image.url if analysis.uploaded_image else '',
        'product': {
            'id': analysis.id,
            'brand_name': analysis.brand_name,
            'brand': analysis.brand_name,
            'product_name': analysis.product_name,
            'name': analysis.product_name,
            'category': analysis.category,
            'description': '',
            'thumbnail_url': analysis.uploaded_image.url if analysis.uploaded_image else '',
            'image_url': analysis.uploaded_image.url if analysis.uploaded_image else '',
            'uploaded_image_url': analysis.uploaded_image.url if analysis.uploaded_image else '',
            'source': LOCAL_PRODUCT_SOURCE,
        },
        'user_tone': user_tone,
        'personalized': bool(user_profile),
        'chart': {
            'axis': {'x': 'warmCool', 'y': 'lightDeep'},
            'zones': chart_zones(user_tone),
            'labels': {
                'warm': raw_labels.get('warm_label') or 'Warm',
                'cool': raw_labels.get('cool_label') or 'Cool',
                'light': raw_labels.get('light_label') or 'Light',
                'deep': raw_labels.get('deep_label') or 'Deep',
                'best_regions': raw_labels.get('best_region_labels') or [],
            },
            'season_regions': raw_labels.get('season_labels') or [],
        },
        'options': options,
        'best_option': best_option,
        'recommendation_groups': recommendation_groups(options),
        'ai_explanation_status': 'skipped',
        'disclaimer': ANALYSIS_DISCLAIMER,
    }


def serialize_analysis_option(option, *, index, personalized):
    metrics = None
    if option.hex_code:
        metrics = {
            'hex_code': option.hex_code,
            'rgb': list(hex_to_rgb_strict(option.hex_code)),
            'brightness': option.brightness,
            'saturation': option.saturation,
            'warmth': option.warmth,
            'coolness': option.coolness,
            'depth': option.depth,
            'softness': option.softness,
            'contrast': option.contrast,
            'chart_x': option.chart_x,
            'chart_y': option.chart_y,
        }
    grade = option.grade or (ProductImageAnalysisOption.Grade.PENDING if not option.hex_code else '')
    reason = option.reason or (PENDING_REASON if grade == ProductImageAnalysisOption.Grade.PENDING else '')
    option_no = f'{index:02d}'
    return {
        'id': option.id,
        'option_name': option.option_name,
        'display_name': option.display_name or option.option_name,
        'option_no': option_no,
        'hex_code': option.hex_code or None,
        'color_source': option.color_source,
        'confidence': option.confidence,
        'chart_x': option.chart_x,
        'chart_y': option.chart_y,
        'chart_position': {
            'x': option.chart_x,
            'y': option.chart_y,
        },
        'brightness': option.brightness,
        'saturation': option.saturation,
        'warmth': option.warmth,
        'coolness': option.coolness,
        'depth': option.depth,
        'softness': option.softness,
        'contrast': option.contrast,
        'color_metrics': metrics,
        'match_score': option.match_score if personalized and grade != ProductImageAnalysisOption.Grade.PENDING else None,
        'grade': grade if personalized or grade == ProductImageAnalysisOption.Grade.PENDING else '',
        'reason': reason,
        'analysis_status': 'PENDING_COLOR_ANALYSIS' if grade == ProductImageAnalysisOption.Grade.PENDING else 'DONE',
    }


def recommendation_groups(options):
    groups = {'BEST': [], 'GOOD': [], 'CAUTION': [], 'PENDING': []}
    for option in options:
        grade = str(option.get('grade') or '').upper()
        if grade == 'PENDING' or option.get('analysis_status') == 'PENDING_COLOR_ANALYSIS':
            groups['PENDING'].append(option.get('id'))
        elif grade in {'BEST', 'GOOD', 'CAUTION'}:
            groups[grade].append(option.get('id'))
    return groups


def select_best_option(options):
    scored = [option for option in options if option.get('match_score') is not None]
    if scored:
        return max(scored, key=lambda option: option.get('match_score') or 0)
    return options[0] if options else None


def chart_zones(user_tone):
    if not user_tone:
        return []
    range_profile = user_tone.get('range_profile') or {}
    return [
        {'type': 'GOOD', 'range': range_profile.get('good')},
        {'type': 'BEST', 'range': range_profile.get('best')},
    ]


@transaction.atomic
def update_analysis_from_review(analysis, data):
    if analysis.status == ProductImageAnalysis.Status.CONFIRMED:
        raise ValidationError('Confirmed image analysis results can no longer be edited.')

    for field in ['product_name', 'brand_name', 'category']:
        if field in data:
            setattr(analysis, field, data[field] or getattr(analysis, field))
    analysis.save(update_fields=['product_name', 'brand_name', 'category', 'updated_at'])

    user_profile, _ = user_profile_payload(analysis.user)
    existing = {option.id: option for option in analysis.options.all()}
    option_payloads = []
    for payload in data.get('options', []):
        if payload.get('removed'):
            continue
        payload_id = payload.get('id')
        existing_option = existing.get(int(payload_id)) if payload_id else None
        option_payloads.append(
            {
                'id': existing_option.id if existing_option else None,
                'option_name': payload.get('option_name') or payload.get('display_name') or (existing_option.option_name if existing_option else ''),
                'display_name': payload.get('display_name') or payload.get('option_name') or (existing_option.display_name if existing_option else ''),
                'hex_code': payload.get('hex_code'),
                'chart_x': payload.get('chart_x') if payload.get('chart_x') is not None else (existing_option.chart_x if existing_option else None),
                'chart_y': payload.get('chart_y') if payload.get('chart_y') is not None else (existing_option.chart_y if existing_option else None),
                'confidence': payload.get('confidence') if payload.get('confidence') is not None else (existing_option.confidence if existing_option else None),
                'blob_box': {
                    'x': payload.get('chart_x') if payload.get('chart_x') is not None else (existing_option.chart_x if existing_option else 50),
                    'y': payload.get('chart_y') if payload.get('chart_y') is not None else (existing_option.chart_y if existing_option else 50),
                    'width': 1,
                    'height': 1,
                },
            }
        )

    replace_analysis_options(
        analysis,
        option_payloads,
        user_profile=user_profile,
        category=analysis.category,
        image=None,
        mark_all_user_edited=True,
    )
    return build_product_image_analysis_payload(analysis, user_profile=user_profile)


def confirm_analysis(analysis):
    if analysis.status != ProductImageAnalysis.Status.CONFIRMED:
        analysis.status = ProductImageAnalysis.Status.CONFIRMED
        analysis.confirmed_at = timezone.now()
        analysis.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    return build_product_image_analysis_payload(analysis)
