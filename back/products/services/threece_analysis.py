import html
import json
import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote_plus, urljoin, urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import status

from engagements.models import UrlAnalysisRecord
from products.models import Product
from products.services.color_extraction import ColorExtractionError, dominant_color_from_image_url
from products.services.color_metrics import (
    build_color_metrics,
    hex_to_rgb,
    normalize_hex,
    public_grade_from_score,
    rgb_to_hex,
)
from products.services.product_page_parser import parse_product_page
from products.services.recommendation import calculate_option_match

logger = logging.getLogger(__name__)

THREE_CE_HOSTS = {'3cecosmetics.co.kr', 'www.3cecosmetics.co.kr'}
THREE_CE_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
)
THREE_CE_SAFE_ERROR_MESSAGE = '상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.'
THREE_CE_PARSE_ERROR_MESSAGE = 'Could not extract product options from the 3CE page.'
THREE_CE_SUCCESS_MESSAGE = '상품 정보를 분석했습니다.'
THREE_CE_PENDING_REASON = 'Color HEX analysis is pending.'
PENDING_STATUS = 'PENDING_COLOR_ANALYSIS'
DONE_STATUS = 'DONE'
PENDING_GRADE = 'PENDING'
UNRATED_GRADE = 'UNRATED'
PRODUCT_ANALYSIS_DISCLAIMER = (
    '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다. '
    'AI 분석 결과는 참고용이며 실제 발색은 피부톤, 조명, 모니터 환경에 따라 달라질 수 있습니다.'
)

GUMMY_OIL_TINT_OPTIONS = [
    'BAGEL PEACH',
    'MELTING GUMMY',
    'GLOWY',
    'ROSE GUMMY',
    'MAUVE JELLY',
    'SUMMER BITE',
    'DEW ON',
    'TAUPE DROP',
    'SWEETEN',
    'HONEY BEAR',
    'PEARL CLOUD',
]
SELECTED_OPTION_ALIASES = {
    '\ubca0\uc774\uae00 \ud53c\uce58': 'BAGEL PEACH',
    '\ud1a0\ud504 \ub4dc\ub86d': 'TAUPE DROP',
    '베이글 피치': 'BAGEL PEACH',
}


@dataclass
class ThreeCEOptionCandidate:
    option_name: str
    display_name: str = ''
    hex_code: str = ''
    swatch_image_url: str = ''
    image_url: str = ''
    source: str = ''


class ThreeCEAnalyzer:
    source = 'THREE_CE'

    def analyze(self, product_url, *, original_url='', user=None):
        from products.services.url_color_analysis import (
            ProductColorAnalysisError,
            _build_user_profile,
            _build_user_tone_response,
            _chart_zones,
            _primary_tone_payload,
            validate_public_url,
        )

        safe_url = validate_public_url(product_url)
        parsed_url = urlparse(safe_url)
        if (parsed_url.hostname or '').lower() not in THREE_CE_HOSTS:
            raise ProductColorAnalysisError(
                THREE_CE_SAFE_ERROR_MESSAGE,
                code='THREE_CE_UNSUPPORTED_HOST',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        selected_option = extract_selected_option(safe_url)
        logger.info('Starting 3CE product analysis url=%s selected_option=%s', safe_url, selected_option)

        try:
            html_text, final_url = fetch_threece_html(safe_url)
            primary_payload = _primary_tone_payload(user)
            user_profile = _build_user_profile(primary_payload)
            user_tone = _build_user_tone_response(primary_payload)
            analysis = parse_threece_page(
                html_text,
                final_url,
                selected_option=selected_option,
                user_profile=user_profile,
            )
        except ProductColorAnalysisError:
            raise
        except Exception as exc:
            logger.exception('3CE product analysis failed: %s', safe_url)
            raise ProductColorAnalysisError(
                THREE_CE_SAFE_ERROR_MESSAGE,
                code='THREE_CE_ANALYSIS_FAILED',
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

        result = {
            'success': True,
            'source': self.source,
            'original_url': original_url or safe_url,
            'normalized_url': safe_url,
            'final_url': final_url,
            'selected_option': analysis['selected_option'],
            'product': analysis['product'],
            'product_url': final_url,
            'user_tone': user_tone,
            'personalized': bool(user_tone),
            'analysis_status': analysis['analysis_status'],
            'chart': {
                'axis': {'x': 'warmCool', 'y': 'lightDeep'},
                'zones': _chart_zones(primary_payload),
            },
            'options': analysis['options'],
            'best_option': selected_or_best_option(analysis['options']),
            'recommendation_groups': recommendation_groups(analysis['options']),
            'ai_explanation_status': 'skipped',
            'message': analysis['message'],
            'disclaimer': PRODUCT_ANALYSIS_DISCLAIMER,
        }
        save_threece_analysis_record(user, final_url, analysis, result)
        return result


def is_threece_url(value):
    return (urlparse(str(value or '')).hostname or '').lower() in THREE_CE_HOSTS


def extract_selected_option(url):
    query = parse_qs(urlparse(str(url or '')).query)
    variant = (query.get('variant') or [''])[0]
    return clean_text(unquote_plus(str(variant or '')))


def fetch_threece_html(url):
    from products.services.url_color_analysis import ProductColorAnalysisError, validate_public_url

    timeout = int(getattr(settings, 'PRODUCT_ANALYSIS_FETCH_TIMEOUT', 10))
    max_bytes = int(getattr(settings, 'PRODUCT_COLOR_ANALYSIS_MAX_HTML_BYTES', 2_000_000))
    request = Request(url, headers=threece_headers())
    logger.info('Fetching 3CE product page: %s', url)

    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, 'status', None) or getattr(response, 'code', 200)
            if status_code != 200:
                logger.info('3CE fetch returned non-200 status=%s url=%s', status_code, url)
                raise ProductColorAnalysisError(
                    THREE_CE_SAFE_ERROR_MESSAGE,
                    code='THREE_CE_FETCH_FAILED',
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            payload = response.read(max_bytes + 1)
            content_type = response.headers.get('Content-Type', '')
            final_url = validate_public_url(response.geturl() or url)
    except ProductColorAnalysisError:
        raise
    except HTTPError as exc:
        logger.exception('3CE HTTP error status=%s url=%s', exc.code, url)
        raise ProductColorAnalysisError(
            THREE_CE_SAFE_ERROR_MESSAGE,
            code='THREE_CE_FETCH_FAILED',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        logger.exception('3CE fetch failed url=%s', url)
        raise ProductColorAnalysisError(
            THREE_CE_SAFE_ERROR_MESSAGE,
            code='THREE_CE_ANALYSIS_FAILED',
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    if len(payload) > max_bytes:
        raise ProductColorAnalysisError(
            THREE_CE_SAFE_ERROR_MESSAGE,
            code='THREE_CE_RESPONSE_TOO_LARGE',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    html_text = decode_response(payload, content_type)
    if not html_text.strip():
        raise ProductColorAnalysisError(
            THREE_CE_SAFE_ERROR_MESSAGE,
            code='THREE_CE_EMPTY_RESPONSE',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    logger.info('Fetched 3CE product page final_url=%s', final_url)
    return html_text, final_url


def threece_headers():
    return {
        'User-Agent': THREE_CE_USER_AGENT,
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/avif,image/webp,image/apng,*/*;q=0.8'
        ),
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.3cecosmetics.co.kr/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }


def parse_threece_page(html_text, final_url, *, selected_option='', user_profile=None):
    from products.services.url_color_analysis import ProductColorAnalysisError

    logger.info('Parsing 3CE product page: %s', final_url)
    generic = parse_product_page(html_text, final_url)
    parser = ThreeCEHTMLParser()
    parser.feed(html_text or '')
    logger.info(
        '3CE static parse diagnostics url=%s html_length=%s has_swatch_marker=%s '
        'parser_swatches=%s parser_available_color_texts=%s scripts=%s',
        final_url,
        len(html_text or ''),
        has_static_swatch_marker(html_text),
        len(parser.swatch_candidates),
        len(parser.available_color_texts),
        len(parser.script_texts),
    )
    json_product = extract_json_ld_product(parser.json_ld_scripts)

    product_name = (
        clean_text(json_product.get('name'))
        or generic.product_name
        or clean_title(parser.meta.get('og:title') or parser.meta.get('twitter:title') or parser.title)
    )
    description = (
        clean_text(json_product.get('description'))
        or generic.description
        or clean_text(parser.meta.get('og:description') or parser.meta.get('description'))
    )
    image_url = (
        extract_product_image(json_product)
        or parser.meta.get('og:image')
        or parser.meta.get('twitter:image')
        or first_image(parser.image_candidates)
        or generic.thumbnail_url
    )
    image_url = urljoin(final_url, image_url) if image_url else ''
    price = extract_price(json_product, html_text)
    category, texture = infer_category_and_texture(final_url)
    candidates = extract_option_candidates(
        parser,
        html_text,
        final_url,
        selected_option=selected_option,
        product_name=product_name,
    )
    logger.info(
        '3CE candidates after static/json/api extraction url=%s count=%s color_count=%s sources=%s',
        final_url,
        len(candidates),
        count_candidates_with_color(candidates),
        candidate_source_counts(candidates),
    )
    if should_use_rendered_dom_fallback(candidates, final_url):
        rendered_raw_candidates = extract_rendered_swatch_candidates(
            final_url,
            product_name=product_name,
        )
        rendered_candidates = normalize_candidates(rendered_raw_candidates, final_url, product_name=product_name)
        logger.info(
            '3CE rendered DOM extraction url=%s raw_count=%s normalized_count=%s color_count=%s',
            final_url,
            len(rendered_raw_candidates),
            len(rendered_candidates),
            count_candidates_with_color(rendered_candidates),
        )
        if rendered_candidates:
            candidates = merge_rendered_candidates(
                candidates,
                rendered_candidates,
                final_url,
                selected_option,
            )
            logger.info(
                '3CE candidates after rendered merge url=%s count=%s color_count=%s sources=%s',
                final_url,
                len(candidates),
                count_candidates_with_color(candidates),
                candidate_source_counts(candidates),
            )
    if not candidates:
        raise ProductColorAnalysisError(
            THREE_CE_PARSE_ERROR_MESSAGE,
            code='THREE_CE_PARSE_FAILED',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    options = build_option_payloads(
        candidates,
        category=category,
        product_image_url=image_url,
        selected_option=selected_option,
        user_profile=user_profile,
    )
    product_payload = {
        'url': final_url,
        'product_url': final_url,
        'brand_name': '3CE',
        'brand': '3CE',
        'product_name': product_name or '3CE 상품',
        'name': product_name or '3CE 상품',
        'description': description,
        'thumbnail_url': image_url,
        'image_url': image_url,
        'category': category,
        'texture': texture,
        'price': price,
        'selected_option': selected_option,
    }
    has_done_option = any(option.get('analysis_status') == DONE_STATUS for option in options)
    return {
        'product': product_payload,
        'options': options,
        'selected_option': selected_option,
        'analysis_status': 'COMPLETE' if has_done_option else 'PARTIAL',
        'message': THREE_CE_SUCCESS_MESSAGE,
    }


def extract_option_candidates(parser, html_text, final_url, *, selected_option='', product_name=''):
    raw_candidates = []
    raw_candidates.extend(parser.swatch_candidates)
    raw_candidates.extend(text_candidates(parser.available_color_texts, source='available-colors'))
    raw_candidates.extend(extract_script_color_candidates(parser.script_texts))
    raw_candidates.extend(extract_embedded_json_color_candidates(parser.script_texts))
    raw_candidates.extend(extract_api_color_candidates(parser.script_texts, final_url))

    normalized = normalize_candidates(raw_candidates, final_url, product_name=product_name)
    fallback_options = known_options_for_url(final_url)
    if fallback_options:
        return merge_known_options(fallback_options, normalized, selected_option)

    if selected_option and not any(option_matches(candidate.option_name, selected_option) for candidate in normalized):
        normalized.insert(
            0,
            ThreeCEOptionCandidate(
                option_name=selected_option,
                display_name=selected_option,
                source='selected-variant',
            ),
        )
    return normalized[:20]


def text_candidates(values, *, source):
    candidates = []
    for value in values:
        for piece in split_option_candidate(value):
            candidates.append({'name': piece, 'source': source})
    return candidates


def normalize_candidates(raw_candidates, final_url, *, product_name=''):
    candidates = []
    seen = set()
    for raw in raw_candidates:
        name = clean_option_name(raw.get('name') or raw.get('option_name') or '')
        display_name = clean_option_name(raw.get('display_name') or '')
        if not display_name:
            display_name = name
        if not looks_like_color_option(name, product_name=product_name):
            continue
        key = option_key(name)
        if key in seen:
            existing = next((candidate for candidate in candidates if option_key(candidate.option_name) == key), None)
            if existing:
                merge_candidate_data(existing, raw, final_url)
            continue
        seen.add(key)
        candidates.append(
            ThreeCEOptionCandidate(
                option_name=normalize_public_option_name(name),
                display_name=display_name,
                hex_code=extract_color_value(raw),
                swatch_image_url=absolute_url(final_url, raw.get('swatch_image_url') or raw.get('image_url') or ''),
                image_url=absolute_url(final_url, raw.get('image_url') or ''),
                source=raw.get('source') or '',
            )
        )
    return candidates


def merge_candidate_data(candidate, raw, final_url):
    if not candidate.hex_code:
        candidate.hex_code = extract_color_value(raw)
    if not candidate.swatch_image_url:
        candidate.swatch_image_url = absolute_url(final_url, raw.get('swatch_image_url') or raw.get('image_url') or '')
    if not candidate.image_url:
        candidate.image_url = absolute_url(final_url, raw.get('image_url') or '')


def merge_known_options(known_options, candidates, selected_option):
    by_key = {known_option_key(candidate.option_name): candidate for candidate in candidates}
    selected_key = known_option_key(selected_option)
    merged = []
    for option_name in known_options:
        key = option_key(option_name)
        candidate = by_key.get(key) or ThreeCEOptionCandidate(option_name=option_name, source='known-fallback')
        candidate.option_name = option_name
        if selected_key == key:
            candidate.display_name = selected_option or candidate.display_name or option_name
        else:
            candidate.display_name = candidate.display_name or option_name
        merged.append(candidate)
    return merged


def known_options_for_url(url):
    path = urlparse(str(url or '')).path.lower()
    if '3ce-gummy-oil-tint' in path:
        return GUMMY_OIL_TINT_OPTIONS
    return []


def has_static_swatch_marker(html_text):
    return bool(re.search(r'shade|swatch|available\s+colors?|data-option|color', html_text or '', flags=re.IGNORECASE))


def count_candidates_with_color(candidates):
    return sum(1 for candidate in candidates if normalize_css_color(getattr(candidate, 'hex_code', '')) or getattr(candidate, 'swatch_image_url', ''))


def candidate_source_counts(candidates):
    counts = {}
    for candidate in candidates:
        source = getattr(candidate, 'source', '') or 'unknown'
        counts[source] = counts.get(source, 0) + 1
    return counts


def should_use_rendered_dom_fallback(candidates, final_url):
    if not candidates:
        return True
    known = known_options_for_url(final_url)
    color_count = count_candidates_with_color(candidates)
    if known:
        return color_count < max(2, len(known) // 2)
    return color_count == 0


def merge_rendered_candidates(existing, rendered, final_url, selected_option):
    known = known_options_for_url(final_url)
    if known:
        return merge_known_options(known, merge_candidate_lists(existing, rendered), selected_option)
    return merge_candidate_lists(existing, rendered)


def merge_candidate_lists(existing, incoming):
    merged = list(existing)
    by_key = {known_option_key(candidate.option_name): candidate for candidate in merged}
    for candidate in incoming:
        key = known_option_key(candidate.option_name)
        if key in by_key:
            merge_candidate_object(by_key[key], candidate)
        else:
            merged.append(candidate)
            by_key[key] = candidate
    return merged


def merge_candidate_object(target, source):
    if not target.display_name and source.display_name:
        target.display_name = source.display_name
    if not target.hex_code and source.hex_code:
        target.hex_code = source.hex_code
    if not target.swatch_image_url and source.swatch_image_url:
        target.swatch_image_url = source.swatch_image_url
    if not target.image_url and source.image_url:
        target.image_url = source.image_url
    if (not target.source or target.source == 'known-fallback') and source.source:
        target.source = source.source


def build_option_payloads(candidates, *, category, product_image_url, selected_option='', user_profile=None):
    options = []
    for index, candidate in enumerate(candidates, start=1):
        resolved_hex = resolve_candidate_hex(candidate)
        selected = selected_option and option_matches(candidate.option_name, selected_option)
        if resolved_hex:
            payload = analyzed_option_payload(
                candidate,
                resolved_hex,
                index=index,
                category=category,
                selected=selected,
                user_profile=user_profile,
            )
        else:
            payload = pending_option_payload(
                candidate,
                index=index,
                selected=selected,
                product_image_url=product_image_url,
            )
        options.append(payload)
    return options


def analyzed_option_payload(candidate, hex_code, *, index, category, selected, user_profile=None):
    rgb = hex_to_rgb(hex_code)
    metrics = build_color_metrics(rgb) if rgb else {}
    if user_profile and metrics:
        option_object = SimpleNamespace(
            product=SimpleNamespace(category=category),
            analyzed_tone_tag=metrics['analyzed_tone_tag'],
            brightness=metrics['brightness'],
            saturation=metrics['saturation'],
            coolness=metrics['coolness'],
            warmth=metrics['warmth'],
            depth=metrics['depth'],
            softness=metrics['softness'],
            contrast=metrics['contrast'],
        )
        match = calculate_option_match(option_object, user_profile, category)
        match_score = match['match_score']
        grade = public_grade_from_score(match_score)
        reason = match['reason']
    else:
        match_score = None
        grade = UNRATED_GRADE
        reason = 'Set a primary personal color result to calculate a personalized recommendation score.'

    return {
        'id': f'3ce-option-{index:02d}',
        'option_no': f'{index:02d}',
        'option_name': candidate.option_name,
        'display_name': candidate.display_name or candidate.option_name,
        'swatch_image_url': candidate.swatch_image_url,
        'image_url': candidate.image_url or candidate.swatch_image_url,
        **metrics,
        'hex_code': metrics.get('hex_code') or hex_code,
        'color_metrics': metrics or None,
        'match_score': match_score,
        'grade': grade,
        'reason': reason,
        'shortReason': reason,
        'detailReason': reason,
        'usageTip': 'Actual color may vary by lighting, skin tone, and monitor settings.',
        'analysis_status': DONE_STATUS,
        'is_selected': bool(selected),
    }


def pending_option_payload(candidate, *, index, selected, product_image_url):
    return {
        'id': f'3ce-option-{index:02d}',
        'option_no': f'{index:02d}',
        'option_name': candidate.option_name,
        'display_name': candidate.display_name or candidate.option_name,
        'swatch_image_url': candidate.swatch_image_url,
        'image_url': candidate.image_url or candidate.swatch_image_url or product_image_url,
        'hex_code': None,
        'rgb': None,
        'brightness': None,
        'saturation': None,
        'coolness': None,
        'warmth': None,
        'depth': None,
        'softness': None,
        'contrast': None,
        'chart_x': None,
        'chart_y': None,
        'color_metrics': None,
        'match_score': None,
        'grade': PENDING_GRADE,
        'reason': THREE_CE_PENDING_REASON,
        'shortReason': THREE_CE_PENDING_REASON,
        'detailReason': 'The option was found, but no reliable swatch HEX value was available in the page data.',
        'usageTip': 'Color matching will become available after the swatch color is analyzed.',
        'analysis_status': PENDING_STATUS,
        'is_selected': bool(selected),
    }


def resolve_candidate_hex(candidate):
    direct_hex = normalize_css_color(candidate.hex_code)
    if direct_hex:
        return direct_hex

    image_url = candidate.swatch_image_url or candidate.image_url
    if not image_url:
        return ''

    try:
        from products.services.url_color_analysis import validate_public_url

        safe_url = validate_public_url(image_url)
        rgb = dominant_color_from_image_url(safe_url, timeout=5)
    except (ColorExtractionError, Exception) as exc:
        logger.info('3CE swatch image color extraction failed: %s', exc)
        return ''
    return rgb_to_hex(rgb)


def extract_color_value(raw):
    values = [
        raw.get('hex_code'),
        raw.get('color'),
        raw.get('style'),
        raw.get('data_color'),
        raw.get('data_hex'),
        raw.get('data_swatch_color'),
        raw.get('backgroundColor'),
        raw.get('background_color'),
        raw.get('swatchColor'),
        raw.get('swatch_color'),
    ]
    for value in values:
        color = normalize_css_color(value)
        if color:
            return color
    return ''


def normalize_css_color(value):
    if not value:
        return ''
    text = str(value)
    hex_value = normalize_hex(text)
    if hex_value and not is_ignored_swatch_color(hex_value):
        return hex_value
    match = re.search(
        r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*([0-9.]+))?',
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return ''
    alpha = match.group(4)
    if alpha is not None:
        try:
            if float(alpha) <= 0.05:
                return ''
        except ValueError:
            return ''
    rgb = tuple(int(match.group(index)) for index in range(1, 4))
    hex_code = rgb_to_hex(rgb)
    return '' if is_ignored_swatch_color(hex_code) else hex_code


def is_ignored_swatch_color(value):
    rgb = hex_to_rgb(value)
    if not rgb:
        return False
    red, green, blue = rgb
    if red > 238 and green > 238 and blue > 238 and max(rgb) - min(rgb) < 16:
        return True
    if abs(red - green) < 8 and abs(green - blue) < 8 and red > 215:
        return True
    return False


def extract_script_color_candidates(script_texts):
    candidates = []
    for script in script_texts:
        text = html.unescape(script or '')
        for match in re.finditer(
            r'"(?:availableColors|available_colou?rs|colorOptions|colourOptions|variants|options)"\s*:\s*(\[[^\]]+\])',
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            candidates.extend(extract_candidates_from_json_like_array(match.group(1), source='script-array'))
    return candidates


def extract_embedded_json_color_candidates(script_texts):
    candidates = []
    for script in script_texts:
        text = html.unescape(script or '')
        if not re.search(r'variant|shade|colou?r|swatch|option|product', text, flags=re.IGNORECASE):
            continue
        for payload in extract_json_payloads_from_script(text):
            candidates.extend(walk_color_payload(payload, source='embedded-json'))
    return candidates


def extract_api_color_candidates(script_texts, final_url):
    candidates = []
    for api_url in discover_same_origin_api_urls(script_texts, final_url)[:3]:
        try:
            payload = fetch_threece_json(api_url, final_url)
        except Exception as exc:
            logger.info('3CE API candidate fetch failed url=%s error=%s', api_url, exc)
            continue
        candidates.extend(walk_color_payload(payload, source='api-response'))
    if candidates:
        logger.info('3CE API response candidates count=%s url=%s', len(candidates), final_url)
    return candidates


def extract_json_payloads_from_script(text):
    payloads = []
    stripped = str(text or '').strip()
    if stripped.startswith(('{', '[')):
        try:
            payloads.append(json.loads(stripped))
        except json.JSONDecodeError:
            pass

    for match in re.finditer(
        r'"(?:variants?|shades?|colou?rs?|colorOptions|shadeOptions|options|swatches|product)"\s*:\s*([\[{])',
        stripped,
        flags=re.IGNORECASE,
    ):
        start = match.start(1)
        chunk = balanced_json_chunk(stripped, start)
        if not chunk:
            continue
        try:
            payloads.append(json.loads(chunk))
        except json.JSONDecodeError:
            continue
    return payloads


def balanced_json_chunk(text, start):
    opening = text[start:start + 1]
    closing = '}' if opening == '{' else ']'
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return ''


def walk_color_payload(payload, *, source):
    candidates = []
    if isinstance(payload, list):
        for item in payload:
            candidates.extend(walk_color_payload(item, source=source))
        return candidates
    if not isinstance(payload, dict):
        return candidates

    candidate = color_candidate_from_mapping(payload, source=source)
    if candidate:
        candidates.append(candidate)

    for value in payload.values():
        if isinstance(value, (dict, list)):
            candidates.extend(walk_color_payload(value, source=source))
    return candidates


def color_candidate_from_mapping(mapping, *, source):
    name = first_present(
        mapping,
        [
            'optionName',
            'option_name',
            'shadeName',
            'shade_name',
            'colorName',
            'color_name',
            'variantName',
            'variant_name',
            'displayName',
            'display_name',
            'label',
            'name',
            'title',
            'value',
        ],
    )
    color = first_color_present(
        mapping,
        [
            'hex',
            'hexCode',
            'hex_code',
            'color',
            'colour',
            'colorCode',
            'color_code',
            'swatchColor',
            'swatch_color',
            'backgroundColor',
            'background_color',
            'rgb',
            'rgba',
        ],
    )
    image = first_present(
        mapping,
        [
            'swatchImage',
            'swatch_image',
            'swatchImageUrl',
            'swatch_image_url',
            'image',
            'imageUrl',
            'image_url',
            'thumbnail',
            'thumbnailUrl',
            'mediaUrl',
            'src',
        ],
    )
    if not (name or color or image):
        return None
    return {
        'name': name,
        'display_name': name,
        'hex_code': color,
        'swatch_image_url': image,
        'image_url': image,
        'source': source,
    }


def first_color_present(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, dict):
            value = first_color_present(value, ['hex', 'hexCode', 'hex_code', 'rgb', 'rgba', 'value'])
        elif isinstance(value, list) and len(value) >= 3:
            value = rgb_to_hex(tuple(value[:3]))
        if value:
            return str(value)
    return ''


def discover_same_origin_api_urls(script_texts, final_url):
    parsed_final = urlparse(str(final_url or ''))
    discovered = []
    seen = set()
    for script in script_texts:
        for match in re.finditer(r'["\']([^"\']+(?:/api/|\.json(?:\?|$))[^"\']*)["\']', script or '', flags=re.IGNORECASE):
            candidate = urljoin(final_url, html.unescape(match.group(1)))
            parsed_candidate = urlparse(candidate)
            if parsed_candidate.scheme not in {'http', 'https'}:
                continue
            if parsed_candidate.hostname != parsed_final.hostname:
                continue
            key = candidate.split('#', 1)[0]
            if key in seen:
                continue
            seen.add(key)
            discovered.append(key)
    if discovered:
        logger.info('3CE discovered same-origin API URLs count=%s url=%s', len(discovered), final_url)
    return discovered


def fetch_threece_json(api_url, referer_url):
    from products.services.url_color_analysis import validate_public_url

    safe_url = validate_public_url(api_url)
    timeout = int(getattr(settings, 'PRODUCT_ANALYSIS_FETCH_TIMEOUT', 10))
    max_bytes = min(int(getattr(settings, 'PRODUCT_COLOR_ANALYSIS_MAX_HTML_BYTES', 2_000_000)), 1_000_000)
    request = Request(
        safe_url,
        headers={
            **threece_headers(),
            'Accept': 'application/json,text/plain,*/*',
            'Referer': referer_url,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
        content_type = response.headers.get('Content-Type', '')
    if len(payload) > max_bytes:
        raise ValueError('3CE API response too large.')
    text = decode_response(payload, content_type)
    return json.loads(text)


def extract_rendered_swatch_candidates(final_url, *, product_name=''):
    timeout = int(getattr(settings, 'PRODUCT_ANALYSIS_FETCH_TIMEOUT', 10))
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        logger.info('Playwright is not installed; skipping 3CE rendered DOM extraction: %s', exc)
        return []

    logger.info('Starting 3CE Playwright rendered DOM extraction url=%s', final_url)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ],
            )
            context = browser.new_context(
                user_agent=THREE_CE_USER_AGENT,
                locale='ko-KR',
                viewport={'width': 1365, 'height': 900},
            )
            page = context.new_page()
            page.goto(final_url, wait_until='domcontentloaded', timeout=timeout * 1000)
            try:
                page.wait_for_load_state('networkidle', timeout=min(timeout * 1000, 5000))
            except PlaywrightTimeoutError:
                logger.info('3CE Playwright networkidle wait timed out url=%s', final_url)
            try:
                page.wait_for_selector(
                    '[class*="shade"], [class*="swatch"], [class*="color"], [data-option-name], [aria-label]',
                    timeout=min(timeout * 1000, 5000),
                )
            except PlaywrightTimeoutError:
                logger.info('3CE Playwright swatch selector wait timed out url=%s', final_url)
            entries = page.evaluate(RENDERED_SWATCH_EVALUATE_SCRIPT)
            context.close()
            browser.close()
    except Exception as exc:
        logger.exception('3CE Playwright rendered DOM extraction failed url=%s', final_url)
        return []

    candidates = rendered_entries_to_candidates(entries, final_url, product_name=product_name)
    logger.info('3CE Playwright rendered DOM raw_entries=%s candidates=%s url=%s', len(entries or []), len(candidates), final_url)
    return candidates


RENDERED_SWATCH_EVALUATE_SCRIPT = """
() => {
  const normalize = value => (value || '').toString().replace(/\\s+/g, ' ').trim();
  const attr = (el, name) => el.getAttribute(name) || '';
  const datasetText = el => Object.entries(el.dataset || {}).map(([key, value]) => `${key}:${value}`).join(' ');
  const imageUrl = value => {
    const match = (value || '').match(/url\\(["']?([^"')]+)["']?\\)/i);
    return match ? match[1] : '';
  };
  const nearby = el => {
    const texts = [];
    if (el.previousElementSibling) texts.push(el.previousElementSibling.textContent);
    if (el.nextElementSibling) texts.push(el.nextElementSibling.textContent);
    if (el.parentElement) texts.push(el.parentElement.getAttribute('aria-label'), el.parentElement.getAttribute('title'));
    if (el.parentElement && el.parentElement.previousElementSibling) texts.push(el.parentElement.previousElementSibling.textContent);
    if (el.parentElement && el.parentElement.nextElementSibling) texts.push(el.parentElement.nextElementSibling.textContent);
    return normalize(texts.filter(Boolean).join(' '));
  };
  return Array.from(document.querySelectorAll('*'))
    .filter(el => {
      const cls = normalize(el.className).toLowerCase();
      const id = normalize(el.id).toLowerCase();
      const data = datasetText(el).toLowerCase();
      const role = normalize(attr(el, 'role')).toLowerCase();
      return cls.includes('shade') || cls.includes('swatch') || cls.includes('color') ||
        id.includes('shade') || id.includes('swatch') || id.includes('color') ||
        data.includes('shade') || data.includes('swatch') || data.includes('color') ||
        role === 'button';
    })
    .slice(0, 300)
    .map(el => {
      const style = getComputedStyle(el);
      return {
        tag: el.tagName,
        className: normalize(el.className),
        id: normalize(el.id),
        text: normalize(el.textContent),
        ariaLabel: normalize(attr(el, 'aria-label')),
        title: normalize(attr(el, 'title')),
        value: normalize(attr(el, 'value')),
        alt: normalize(attr(el, 'alt')),
        dataset: datasetText(el),
        nearbyText: nearby(el),
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
        borderColor: style.borderColor,
        outerHTML: el.outerHTML.slice(0, 500),
      };
    });
}
"""


def rendered_entries_to_candidates(entries, final_url, *, product_name=''):
    candidates = []
    known = known_options_for_url(final_url)
    color_entries = []
    for entry in entries or []:
        color = normalize_css_color(entry.get('backgroundColor') or '')
        image = image_url_from_css(entry.get('backgroundImage') or '', final_url)
        if not color and not image:
            continue
        if is_ignored_swatch_color(color):
            color = ''
        if color or image:
            color_entries.append({**entry, 'resolved_color': color, 'resolved_image': image})

    seen = set()
    for index, entry in enumerate(color_entries):
        name = first_rendered_label(entry, product_name=product_name)
        if not name and known and index < len(known):
            name = known[index]
        if not name:
            continue
        key = option_key(name)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                'name': name,
                'display_name': name,
                'hex_code': entry.get('resolved_color') or '',
                'swatch_image_url': entry.get('resolved_image') or '',
                'image_url': entry.get('resolved_image') or '',
                'source': 'rendered-dom',
            }
        )
    return candidates


def first_rendered_label(entry, *, product_name=''):
    values = [
        entry.get('ariaLabel'),
        entry.get('title'),
        entry.get('value'),
        entry.get('alt'),
        entry.get('dataset'),
        entry.get('text'),
        entry.get('nearbyText'),
    ]
    for value in values:
        for piece in split_option_candidate(value):
            cleaned = clean_option_name(piece)
            if looks_like_color_option(cleaned, product_name=product_name):
                return cleaned
    return ''


def image_url_from_css(value, final_url):
    match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', str(value or ''), flags=re.IGNORECASE)
    return absolute_url(final_url, match.group(1)) if match else ''


def extract_candidates_from_json_like_array(value, *, source):
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return [{'name': name, 'source': source} for name in re.findall(r'"([^"]{2,80})"', value or '')]

    candidates = []
    for item in payload:
        if isinstance(item, str):
            candidates.append({'name': item, 'source': source})
        elif isinstance(item, dict):
            name = first_present(item, ['optionName', 'option_name', 'name', 'title', 'value'])
            image = first_present(item, ['swatchImage', 'swatch_image', 'image', 'imageUrl', 'image_url', 'src'])
            candidates.append(
                {
                    'name': name,
                    'display_name': name,
                    'hex_code': first_present(item, ['hex', 'hexCode', 'hex_code', 'color']),
                    'swatch_image_url': image,
                    'image_url': image,
                    'source': source,
                }
            )
    return candidates


def first_present(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, dict):
            value = value.get('url') or value.get('src')
        if value:
            return str(value)
    return ''


def split_option_candidate(value):
    cleaned = clean_text(value)
    cleaned = re.sub(r'\bavailable\s+colors?\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:sold\s*out|select|choose|add\s+to\s+cart)\b', ' ', cleaned, flags=re.IGNORECASE)
    parts = re.split(r'\s{2,}|[\n\r\t|/•·]+|,\s*(?=[A-Za-z가-힣])', cleaned)
    if len(parts) == 1 and len(parts[0].split()) > 5:
        return re.findall(r'[A-Z가-힣][A-Za-z가-힣0-9&.\'-]*(?:\s+[A-Za-z가-힣0-9&.\'-]+){0,3}', parts[0])
    return parts


def clean_option_name(value):
    cleaned = clean_text(value)
    cleaned = re.sub(r'^\d+\s*[-.)]?\s*', '', cleaned)
    cleaned = re.sub(r'\([^)]*(?:sold\s*out|품절|재입고|할인)[^)]*\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip(' -_/|')


def looks_like_color_option(value, *, product_name=''):
    cleaned = clean_text(value)
    if len(cleaned) < 2 or len(cleaned) > 60:
        return False
    lower = cleaned.lower()
    blocked_exact = {
        'available colors',
        'main menu',
        '메인 메뉴',
        'new',
        'best seller',
        'all products',
        'eye',
        'eyes',
        'lip',
        'lips',
        'lip tint',
        'face',
        'others',
        'breadcrumb',
        '매장 위치',
        'store location',
        '3ce',
        'ce',
    }
    blocked_contains = [
        'gummy oil tint',
        'product details',
        'description',
        'ingredients',
        'shipping',
        'review',
        'add to cart',
        'shopping bag',
        'select option',
        'choose option',
        'sold out',
        'filter',
        'category',
    ]
    product_key = re.sub(r'[^a-z0-9]+', ' ', str(product_name or '').lower()).strip()
    if lower in blocked_exact or lower == product_key:
        return False
    if any(token in lower for token in blocked_contains):
        return False
    if re.fullmatch(r'[\d,.$₩%+\-/ ]+', cleaned):
        return False
    return bool(re.search(r'[A-Za-z가-힣]', cleaned))


def normalize_public_option_name(value):
    text = clean_option_name(value)
    if re.fullmatch(r'[A-Za-z0-9&.\'-]+(?:\s+[A-Za-z0-9&.\'-]+)*', text):
        return text.upper()
    alias = SELECTED_OPTION_ALIASES.get(text)
    return alias or text


def option_key(value):
    return re.sub(r'\s+', ' ', clean_text(value)).casefold()


def known_option_key(value):
    alias = SELECTED_OPTION_ALIASES.get(clean_text(value))
    return option_key(alias or value)


def option_matches(left, right):
    return known_option_key(left) == known_option_key(right)


def recommendation_groups(options):
    groups = {'BEST': [], 'GOOD': [], 'CAUTION': [], 'PENDING': []}
    for option in options:
        grade = str(option.get('grade') or '').upper()
        if option.get('analysis_status') == PENDING_STATUS or grade == PENDING_GRADE:
            groups['PENDING'].append(option.get('id'))
        elif grade in {'BEST', 'GOOD', 'CAUTION'}:
            groups[grade].append(option.get('id'))
    return groups


def selected_or_best_option(options):
    for option in options:
        if option.get('is_selected'):
            return option
    scored = [option for option in options if option.get('match_score') is not None]
    if scored:
        return max(scored, key=lambda option: option.get('match_score') or 0)
    return options[0] if options else None


def extract_json_ld_product(scripts):
    for script in scripts:
        try:
            payload = json.loads(html.unescape(script or ''))
        except (TypeError, json.JSONDecodeError):
            continue
        product = find_product_payload(payload)
        if product:
            return product
    return {}


def find_product_payload(payload):
    if isinstance(payload, list):
        for item in payload:
            found = find_product_payload(item)
            if found:
                return found
        return {}
    if not isinstance(payload, dict):
        return {}

    graph = payload.get('@graph')
    if graph:
        found = find_product_payload(graph)
        if found:
            return found

    payload_type = payload.get('@type')
    if isinstance(payload_type, list):
        is_product = any(str(item).lower() == 'product' for item in payload_type)
    else:
        is_product = str(payload_type or '').lower() == 'product'
    return payload if is_product else {}


def extract_product_image(product):
    image = product.get('image') if isinstance(product, dict) else ''
    if isinstance(image, list):
        return image[0] if image else ''
    if isinstance(image, dict):
        return image.get('url') or ''
    return image or ''


def extract_price(product, html_text):
    offers = product.get('offers') if isinstance(product, dict) else None
    prices = []
    if isinstance(offers, dict):
        prices.append(offers.get('price') or offers.get('lowPrice'))
    elif isinstance(offers, list):
        for offer in offers:
            if isinstance(offer, dict):
                prices.append(offer.get('price') or offer.get('lowPrice'))
    for price in prices:
        parsed = parse_price(price)
        if parsed:
            return parsed

    for pattern in [
        r'(?:₩|KRW)\s*([0-9][0-9,]*)',
        r'"price"\s*:\s*"?([0-9][0-9,]*)"?',
        r"'price'\s*:\s*'?([0-9][0-9,]*)'?",
    ]:
        match = re.search(pattern, html_text or '', flags=re.IGNORECASE)
        if match:
            parsed = parse_price(match.group(1))
            if parsed:
                return parsed
    return 0


def parse_price(value):
    digits = re.sub(r'\D+', '', str(value or ''))
    return int(digits) if digits else 0


def infer_category_and_texture(url):
    path = urlparse(str(url or '')).path.lower()
    if 'lip' in path:
        return Product.Category.LIP, '립'
    if 'eye' in path:
        return Product.Category.EYE, '아이'
    if 'cheek' in path or 'blush' in path:
        return Product.Category.CHEEK, '치크'
    if 'base' in path or 'foundation' in path or 'concealer' in path:
        return Product.Category.BASE, '베이스'
    return Product.Category.ETC, ''


def first_image(images):
    for item in images:
        src = item.get('src') if isinstance(item, dict) else ''
        if src and not re.search(r'(?:logo|header|icon)', src, flags=re.IGNORECASE):
            return src
    return ''


def clean_title(value):
    title = clean_text(value)
    if '|' in title:
        title = title.split('|', 1)[0]
    if ' - ' in title:
        title = title.split(' - ', 1)[0]
    return title


def clean_text(value):
    cleaned = re.sub(r'<[^>]+>', ' ', str(value or ''))
    cleaned = html.unescape(cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


def absolute_url(base_url, value):
    if not value:
        return ''
    return urljoin(base_url, clean_text(value))


def decode_response(payload, content_type):
    charset = ''
    for part in str(content_type or '').split(';'):
        part = part.strip()
        if part.lower().startswith('charset='):
            charset = part.split('=', 1)[1].strip()
            break
    try:
        return payload.decode(charset or 'utf-8', errors='replace')
    except LookupError:
        return payload.decode('utf-8', errors='replace')


def save_threece_analysis_record(user, source_url, analysis, result):
    if not user or not user.is_authenticated:
        return
    product = analysis.get('product') or {}
    options = analysis.get('options') or []
    try:
        UrlAnalysisRecord.objects.create(
            user=user,
            source_url=source_url,
            title=product.get('product_name') or source_url,
            brand=product.get('brand_name') or '3CE',
            product_name=product.get('product_name') or '',
            image_url=product.get('thumbnail_url') or '',
            colors=[
                {
                    'option_id': option.get('id'),
                    'option_name': option.get('option_name'),
                    'display_name': option.get('display_name'),
                    'hex_code': option.get('hex_code'),
                    'analysis_status': option.get('analysis_status'),
                }
                for option in options
            ],
            result_payload=result,
        )
    except Exception as exc:
        logger.warning('Failed to save 3CE product URL analysis record: %s', exc)


class ThreeCEHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.title_parts = []
        self.json_ld_scripts = []
        self.script_texts = []
        self.image_candidates = []
        self.available_color_texts = []
        self.swatch_candidates = []
        self.text_parts = []
        self._active_title = False
        self._active_script = False
        self._active_json_ld = False
        self._script_parts = []
        self._collecting_available_colors = False
        self._available_color_budget = 0
        self._candidate_stack = []

    @property
    def title(self):
        return clean_text(' '.join(self.title_parts))

    def handle_starttag(self, tag, attrs):
        attrs_dict = {str(key).lower(): value or '' for key, value in attrs}
        if self._candidate_stack:
            self._candidate_stack[-1]['depth'] += 1

        if tag == 'title':
            self._active_title = True
        elif tag == 'script':
            script_type = attrs_dict.get('type', '').lower()
            self._active_script = True
            self._active_json_ld = 'ld+json' in script_type
            self._script_parts = []
        elif tag == 'meta':
            key = (attrs_dict.get('property') or attrs_dict.get('name') or '').lower()
            content = attrs_dict.get('content') or ''
            if key and content:
                self.meta[key] = clean_text(content)
        elif tag == 'img':
            src = attrs_dict.get('src') or attrs_dict.get('data-src') or attrs_dict.get('data-original') or ''
            if src:
                self.image_candidates.append({'src': src, 'alt': attrs_dict.get('alt', '')})

        option_context = tag == 'option' or self._looks_like_option_context(attrs_dict)
        attr_text = self._option_label_from_attrs(attrs_dict)
        image_src = self._image_from_attrs(tag, attrs_dict)
        color_value = self._color_from_attrs(attrs_dict)

        if option_context and (attr_text or color_value or image_src):
            candidate = {
                'name': attr_text,
                'display_name': attr_text,
                'hex_code': color_value,
                'swatch_image_url': image_src,
                'image_url': image_src,
                'style': attrs_dict.get('style', ''),
                'source': 'swatch-element',
            }
            self.swatch_candidates.append(candidate)
            self._candidate_stack.append({'candidate': candidate, 'depth': 1})
        elif self._candidate_stack:
            candidate = self._candidate_stack[-1]['candidate']
            if not candidate.get('name') and attr_text:
                candidate['name'] = attr_text
                candidate['display_name'] = attr_text
            if not candidate.get('hex_code') and color_value:
                candidate['hex_code'] = color_value
            if not candidate.get('swatch_image_url') and image_src:
                candidate['swatch_image_url'] = image_src
                candidate['image_url'] = image_src

    def handle_endtag(self, tag):
        if tag == 'title':
            self._active_title = False
        elif tag == 'script' and self._active_script:
            script = ''.join(self._script_parts).strip()
            if script:
                self.script_texts.append(script)
                if self._active_json_ld:
                    self.json_ld_scripts.append(script)
            self._active_script = False
            self._active_json_ld = False
            self._script_parts = []

        if self._candidate_stack:
            self._candidate_stack[-1]['depth'] -= 1
            if self._candidate_stack[-1]['depth'] <= 0:
                self._candidate_stack.pop()

    def handle_data(self, data):
        if self._active_title:
            self.title_parts.append(data)
        if self._active_script:
            self._script_parts.append(data)
            return

        text = clean_text(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._candidate_stack:
            candidate = self._candidate_stack[-1]['candidate']
            if not candidate.get('name') and looks_like_color_option(text):
                candidate['name'] = text
                candidate['display_name'] = text

        if re.search(r'available\s+colors?', text, flags=re.IGNORECASE):
            self._collecting_available_colors = True
            self._available_color_budget = 24
            tail = re.sub(r'.*?available\s+colors?', '', text, flags=re.IGNORECASE).strip()
            if tail:
                self.available_color_texts.append(tail)
            return

        if self._collecting_available_colors:
            if is_available_color_boundary(text):
                self._collecting_available_colors = False
                self._available_color_budget = 0
                return
            self.available_color_texts.append(text)
            self._available_color_budget -= 1
            if self._available_color_budget <= 0:
                self._collecting_available_colors = False

    def _looks_like_option_context(self, attrs_dict):
        context = ' '.join(
            attrs_dict.get(key, '')
            for key in ['class', 'id', 'name', 'data-testid', 'data-test-id', 'data-option-name', 'data-option-value']
            if attrs_dict.get(key)
        ).lower()
        return any(token in context for token in ['color', 'colour', 'variant', 'option', 'swatch'])

    def _option_label_from_attrs(self, attrs_dict):
        return clean_text(
            ' '.join(
                attrs_dict.get(key, '')
                for key in ['data-option-name', 'data-option-value', 'data-value', 'data-name', 'title', 'aria-label', 'alt']
                if attrs_dict.get(key)
            )
        )

    def _image_from_attrs(self, tag, attrs_dict):
        if tag not in {'img', 'source'}:
            return ''
        return attrs_dict.get('src') or attrs_dict.get('data-src') or attrs_dict.get('data-original') or attrs_dict.get('srcset', '').split(' ', 1)[0]

    def _color_from_attrs(self, attrs_dict):
        return normalize_css_color(
            ' '.join(
                attrs_dict.get(key, '')
                for key in ['style', 'data-color', 'data-hex', 'data-swatch-color', 'data-bg', 'data-background']
                if attrs_dict.get(key)
            )
        )


def is_available_color_boundary(value):
    lower = clean_text(value).lower()
    boundaries = [
        'description',
        'ingredients',
        'how to',
        'shipping',
        'reviews',
        'add to cart',
        'product details',
    ]
    return any(token in lower for token in boundaries)
