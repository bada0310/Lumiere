from copy import deepcopy
from logging import getLogger

from django.conf import settings

from diagnosis.domain.palette_seed_data import ROLE_KEYS, validate_palette_payload
from diagnosis.domain.tone_key_normalizer import ToneKeyError, normalize_tone_key

logger = getLogger(__name__)

FALLBACK_PALETTE_STATUS = 'preparing'

FALLBACK_PALETTE = {
    'toneKey': 'summer_cool_mute',
    'toneName': '팔레트 준비 중',
    'season': 'summer',
    'temperature': 'cool',
    'brightness': 'medium',
    'chroma': 'low_to_medium',
    'contrast': 'low',
    'description': '선택된 퍼스널컬러 타입의 상세 팔레트가 준비 중입니다. 임시로 부드러운 중명도 컬러를 표시합니다.',
    'keywords': ['soft', 'neutral', 'pending'],
    'bestColors': [
        {
            'name': 'Soft Rose',
            'nameKo': '소프트 로즈',
            'hex': '#CFA0AC',
            'usage': 'lip_cheek',
            'description': '상세 팔레트가 준비될 때까지 표시되는 부드러운 로즈 컬러입니다.',
        },
        {
            'name': 'Neutral Beige',
            'nameKo': '뉴트럴 베이지',
            'hex': '#D8CDC8',
            'usage': 'base',
            'description': '상세 팔레트가 준비될 때까지 표시되는 중립 베이스 컬러입니다.',
        },
    ],
    'worstColors': [],
    'makeupPalette': {
        'base': {'tone': 'neutral_base', 'guide': '상세 베이스 가이드가 준비 중입니다.'},
        'lip': {'recommended': ['soft rose'], 'avoid': []},
        'cheek': {'recommended': ['soft rose'], 'avoid': []},
        'eye': {'recommended': ['neutral taupe'], 'avoid': []},
    },
    'baseMakeupGuide': '상세 베이스 메이크업 가이드가 준비 중입니다.',
    'lipGuide': '상세 립 가이드가 준비 중입니다.',
    'cheekGuide': '상세 치크 가이드가 준비 중입니다.',
    'eyeGuide': '상세 아이 메이크업 가이드가 준비 중입니다.',
    'stylingKeywords': ['준비 중'],
    'recommendedProductToneRange': {
        'hue': ['neutral', 'rose'],
        'brightness': ['medium'],
        'chroma': ['low', 'medium_low'],
        'temperature': 'neutral',
    },
}


def get_palette_for_tone_key(tone_key):
    from diagnosis.models import PersonalColorPalette

    try:
        normalized = normalize_tone_key(tone_key, allow_close_match=True)
    except ToneKeyError:
        normalized = ''

    palette = PersonalColorPalette.objects.filter(tone_key=normalized).first() if normalized else None
    if palette and not palette.is_placeholder:
        palette_data = serialize_palette(palette)
        errors = validate_palette_payload(normalized, palette_data)
        if not errors:
            return palette_data, 'ready'
        logger.error('Invalid personal color palette payload for toneKey=%s: %s', normalized, errors)

    if settings.DEBUG:
        logger.warning('Missing ready personal color palette for toneKey=%s', normalized or tone_key)
        fallback = deepcopy(FALLBACK_PALETTE)
        fallback['requestedToneKey'] = normalized or tone_key
        return fallback, FALLBACK_PALETTE_STATUS

    return {'toneKey': normalized or tone_key, 'toneName': '팔레트 미등록', 'isPlaceholder': True}, 'missing'


def serialize_palette(palette):
    if palette.data:
        data = deepcopy(palette.data)
        data['toneKey'] = data.get('toneKey') or palette.tone_key
        data['label'] = data.get('label') or palette.tone_name
        data['toneName'] = data.get('toneName') or data['label']
        data['season'] = data.get('season') or palette.season
        data['temperature'] = data.get('temperature') or palette.temperature
        data['brightness'] = data.get('brightness') or palette.brightness
        data['chroma'] = data.get('chroma') or palette.chroma
        data['contrast'] = data.get('contrast') or palette.contrast
        data['bestColors'] = data.get('bestColors') or data.get('palettes', {}).get('best', [])
        data['neutralColors'] = data.get('neutralColors') or data.get('palettes', {}).get('neutral', [])
        data['accentColors'] = data.get('accentColors') or data.get('palettes', {}).get('accent', [])
        data['tryColors'] = data.get('tryColors') or data.get('palettes', {}).get('try', [])
        data['worstColors'] = data.get('worstColors') or data.get('palettes', {}).get('worst', [])
        data['makeupPalette'] = data.get('makeupPalette') or _legacy_makeup_palette_from_guide(data.get('makeupColorGuide') or {})
        data['baseMakeupGuide'] = data.get('baseMakeupGuide') or data.get('makeupColorGuide', {}).get('base', {}).get('guide', '')
        data['lipGuide'] = data.get('lipGuide') or data.get('makeupColorGuide', {}).get('lip', {}).get('guide', '')
        data['cheekGuide'] = data.get('cheekGuide') or data.get('makeupColorGuide', {}).get('blush', {}).get('guide', '')
        data['eyeGuide'] = data.get('eyeGuide') or data.get('makeupColorGuide', {}).get('eye', {}).get('guide', '')
        data['stylingKeywords'] = data.get('stylingKeywords') or data.get('keywords', [])
        data['recommendedProductToneRange'] = data.get('recommendedProductToneRange') or {}
        data['isPlaceholder'] = palette.is_placeholder
        data['is_placeholder'] = palette.is_placeholder
        return data

    legacy = {
        'toneKey': palette.tone_key,
        'label': palette.tone_name,
        'toneName': palette.tone_name,
        'season': palette.season,
        'temperature': palette.temperature,
        'brightness': palette.brightness,
        'chroma': palette.chroma,
        'contrast': palette.contrast,
        'description': palette.description,
        'keywords': palette.keywords,
        'bestColors': palette.best_colors,
        'worstColors': palette.worst_colors,
        'makeupPalette': palette.makeup_palette,
        'baseMakeupGuide': palette.base_makeup_guide,
        'lipGuide': palette.lip_guide,
        'cheekGuide': palette.cheek_guide,
        'eyeGuide': palette.eye_guide,
        'stylingKeywords': palette.styling_keywords,
        'recommendedProductToneRange': palette.recommended_product_tone_range,
        'palettes': {
            'best': palette.best_colors,
            'neutral': [],
            'accent': [],
            'try': [],
            'worst': palette.worst_colors,
        },
        'makeupColorGuide': {},
        'isPlaceholder': palette.is_placeholder,
        'is_placeholder': palette.is_placeholder,
    }
    return legacy


def apply_palette_snapshot_to_diagnosis(diagnosis, palette_data):
    from diagnosis.models import DiagnosisColorPalette, DiagnosisRepresentativeColor

    DiagnosisRepresentativeColor.objects.filter(diagnosis=diagnosis).delete()
    DiagnosisColorPalette.objects.filter(diagnosis=diagnosis).delete()

    groups = _palette_groups(palette_data)
    best_colors = groups.get('best') or []

    DiagnosisRepresentativeColor.objects.bulk_create(
        [
            DiagnosisRepresentativeColor(
                diagnosis=diagnosis,
                name=item.get('nameKo') or item.get('name') or f'Color {index + 1}',
                hex=item.get('hex') or '#E7D8D7',
                order=index + 1,
            )
            for index, item in enumerate(best_colors[:6])
        ]
    )

    palette_objects = []
    for group, items in groups.items():
        for index, item in enumerate(items):
            palette_objects.append(
                DiagnosisColorPalette(
                    diagnosis=diagnosis,
                    group=group,
                    name=item.get('nameKo') or item.get('name') or f'Color {index + 1}',
                    hex=item.get('hex') or '#E7D8D7',
                    order=index + 1,
                )
            )
    DiagnosisColorPalette.objects.bulk_create(palette_objects)


def build_makeup_color_guide(palette_data):
    guide = palette_data.get('makeupColorGuide') or {}
    if guide:
        base = guide.get('base') or {}
        eye = guide.get('eye') or {}
        roles = eye.get('roles') or {}
        lip = guide.get('lip') or {}
        blush = guide.get('blush') or {}
        return {
            'base': {
                'title': base.get('title') or '베이스 메이크업',
                'description': base.get('guide') or base.get('description') or '',
                'shadeRange': base.get('recommended') or [],
                'chips': [_chip(item) for item in base.get('chips') or []],
                'avoid': base.get('avoid') or [],
            },
            'eye': {
                'description': eye.get('guide') or eye.get('description') or '',
                'highlighter': _role_chips(roles, 'highlighter'),
                'base': _role_chips(roles, 'base'),
                'shading': _role_chips(roles, 'shading'),
                'point': _role_chips(roles, 'point'),
            },
            'lip': {
                'title': lip.get('title') or '립 메이크업',
                'description': lip.get('guide') or lip.get('description') or '',
                'chips': [_chip(item) for item in lip.get('chips') or []],
                'avoid': lip.get('avoid') or [],
            },
            'blush': {
                'title': blush.get('title') or '치크 메이크업',
                'description': blush.get('guide') or blush.get('description') or '',
                'chips': [_chip(item) for item in blush.get('chips') or []],
                'avoid': blush.get('avoid') or [],
            },
        }

    makeup = palette_data.get('makeupPalette') or {}

    def chips_for_usage(*usages):
        colors = []
        for item in palette_data.get('bestColors') or []:
            if item.get('usage') in usages:
                colors.append(_chip(item))
        return colors

    return {
        'base': {
            'title': '베이스 메이크업',
            'description': palette_data.get('baseMakeupGuide') or makeup.get('base', {}).get('guide', ''),
            'shadeRange': makeup.get('base', {}).get('recommended', []),
            'chips': chips_for_usage('base', 'foundation'),
            'avoid': makeup.get('base', {}).get('avoid', []),
        },
        'eye': {
            'description': palette_data.get('eyeGuide') or '',
            'highlighter': chips_for_usage('eye_highlighter'),
            'base': chips_for_usage('eye', 'eye_base'),
            'shading': chips_for_usage('eye_shading'),
            'point': chips_for_usage('eye_point', 'accent'),
        },
        'lip': {
            'title': '립 메이크업',
            'description': palette_data.get('lipGuide') or '',
            'chips': chips_for_usage('lip', 'lip_cheek'),
            'avoid': makeup.get('lip', {}).get('avoid', []),
        },
        'blush': {
            'title': '치크 메이크업',
            'description': palette_data.get('cheekGuide') or '',
            'chips': chips_for_usage('cheek', 'lip_cheek'),
            'avoid': makeup.get('cheek', {}).get('avoid', []),
        },
    }


def _chip(item):
    if isinstance(item, str):
        return {'name': item, 'hex': '#E7D8D7', 'description': ''}
    return {
        'name': item.get('nameKo') or item.get('name') or '',
        'hex': item.get('hex') or '#E7D8D7',
        'description': item.get('description') or item.get('reason') or '',
    }


def _role_chips(roles, key):
    item = roles.get(key)
    return [_chip(item)] if item else []


def _palette_groups(palette_data):
    palettes = palette_data.get('palettes') or {}
    return {
        'best': palettes.get('best') or palette_data.get('bestColors') or [],
        'neutral': palettes.get('neutral') or palette_data.get('neutralColors') or [],
        'accent': palettes.get('accent') or palette_data.get('accentColors') or [],
        'try': palettes.get('try') or palette_data.get('tryColors') or [],
        'worst': palettes.get('worst') or palette_data.get('worstColors') or [],
    }


def _legacy_makeup_palette_from_guide(guide):
    if not guide:
        return {}
    eye_roles = (guide.get('eye') or {}).get('roles') or {}
    return {
        'base': {
            'tone': (guide.get('base') or {}).get('tone', ''),
            'guide': (guide.get('base') or {}).get('guide', ''),
            'recommended': (guide.get('base') or {}).get('recommended', []),
            'avoid': (guide.get('base') or {}).get('avoid', []),
        },
        'lip': {
            'recommended': (guide.get('lip') or {}).get('recommended', []),
            'avoid': (guide.get('lip') or {}).get('avoid', []),
        },
        'cheek': {
            'recommended': (guide.get('blush') or {}).get('recommended', []),
            'avoid': (guide.get('blush') or {}).get('avoid', []),
        },
        'eye': {
            'recommended': [
                role.get('name')
                for key in ROLE_KEYS
                for role in [eye_roles.get(key)]
                if isinstance(role, dict) and role.get('name')
            ],
            'avoid': (guide.get('eye') or {}).get('avoid', []),
        },
    }
