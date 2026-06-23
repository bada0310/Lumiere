from copy import deepcopy

from diagnosis.domain.tone_key_normalizer import ToneKeyError, normalize_tone_key
from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS, build_tone_name, split_tone_key


LEGACY_TONE_ALIASES = {
    'SPRING_LIGHT': 'spring_warm_light',
    'SPRING_BRIGHT': 'spring_warm_bright',
    'SPRING_MUTE': 'spring_warm_mute',
    'SPRING_DEEP': 'spring_warm_deep',
    'SUMMER_LIGHT': 'summer_cool_light',
    'SUMMER_BRIGHT': 'summer_cool_bright',
    'SUMMER_MUTE': 'summer_cool_mute',
    'SUMMER_DEEP': 'summer_cool_deep',
    'AUTUMN_LIGHT': 'autumn_warm_light',
    'AUTUMN_BRIGHT': 'autumn_warm_bright',
    'AUTUMN_MUTE': 'autumn_warm_mute',
    'AUTUMN_DEEP': 'autumn_warm_deep',
    'FALL_LIGHT': 'autumn_warm_light',
    'FALL_BRIGHT': 'autumn_warm_bright',
    'FALL_MUTE': 'autumn_warm_mute',
    'FALL_DEEP': 'autumn_warm_deep',
    'WINTER_LIGHT': 'winter_cool_light',
    'WINTER_BRIGHT': 'winter_cool_bright',
    'WINTER_MUTE': 'winter_cool_mute',
    'WINTER_DEEP': 'winter_cool_deep',
}

TONE_AXIS_BASE = {
    'bright': {'brightness': 78, 'saturation': 82, 'depth': 22, 'softness': 22, 'contrast': 68},
    'light': {'brightness': 82, 'saturation': 38, 'depth': 18, 'softness': 58, 'contrast': 24},
    'mute': {'brightness': 60, 'saturation': 32, 'depth': 42, 'softness': 78, 'contrast': 26},
    'deep': {'brightness': 36, 'saturation': 58, 'depth': 78, 'softness': 38, 'contrast': 78},
}

SEASON_ADJUSTMENTS = {
    'spring': {'brightness': 4, 'saturation': 6, 'contrast': -2},
    'summer': {'brightness': 0, 'saturation': -8, 'softness': 8, 'contrast': -8},
    'autumn': {'brightness': -10, 'saturation': -2, 'depth': 10, 'softness': 8},
    'winter': {'brightness': -4, 'saturation': 8, 'contrast': 12},
}

COLOR_FAMILIES = {
    'warm': {
        'recommended': ['CORAL', 'PEACH', 'WARM_PINK', 'BEIGE', 'BROWN'],
        'caution': ['BLUE_PINK', 'LAVENDER', 'BURGUNDY', 'ASH'],
    },
    'cool': {
        'recommended': ['BLUE_PINK', 'ROSE', 'MAUVE', 'LAVENDER', 'BERRY'],
        'caution': ['ORANGE', 'TERRACOTTA', 'YELLOW_BROWN', 'CAMEL'],
    },
}


def normalize_profile_tone_key(value, default='summer_cool_light'):
    raw = str(value or '').strip()
    if not raw:
        return default

    upper = raw.upper().replace('-', '_').replace(' ', '_')
    if upper in LEGACY_TONE_ALIASES:
        return LEGACY_TONE_ALIASES[upper]

    try:
        return normalize_tone_key(raw, allow_close_match=True)
    except ToneKeyError:
        return default


def get_tone_profile(tone_key):
    normalized = normalize_profile_tone_key(tone_key)
    return deepcopy(TONE_PROFILE_MAP[normalized])


def build_tone_result_payload(tone_key, second_tone_key=None):
    primary = get_tone_profile(tone_key)
    secondary_key = normalize_profile_tone_key(second_tone_key or _default_second_tone(primary['tone_key']))
    secondary = get_tone_profile(secondary_key)
    return {
        'tone_key': primary['tone_key'],
        'tone_label': primary['tone_label'],
        'second_tone_key': secondary['tone_key'],
        'second_tone_label': secondary['tone_label'],
        'axis_profile': primary['axis_profile'],
        'range_profile': primary['range_profile'],
        'recommended_color_families': primary['recommended_color_families'],
        'caution_color_families': primary['caution_color_families'],
    }


def _build_profile(tone_key):
    season, temperature, tone = split_tone_key(tone_key)
    axis = dict(TONE_AXIS_BASE[tone])
    axis.update({key: axis.get(key, 0) + value for key, value in SEASON_ADJUSTMENTS[season].items()})
    axis['coolness'] = 18 if temperature == 'warm' else 82
    axis['warmth'] = 100 - axis['coolness']
    axis = {key: _clamp(value) for key, value in axis.items()}

    best_margin = {
        'brightness': 10,
        'saturation': 20,
        'coolness': 18,
        'warmth': 18,
        'depth': 18,
        'softness': 20,
        'contrast': 18,
    }
    good_margin = {key: value + 10 for key, value in best_margin.items()}
    families = COLOR_FAMILIES[temperature]

    return {
        'tone_key': tone_key,
        'tone_label': build_tone_name(tone_key),
        'axis_profile': axis,
        'range_profile': {
            'best': _range_profile(axis, best_margin),
            'good': _range_profile(axis, good_margin),
        },
        'recommended_color_families': families['recommended'],
        'caution_color_families': families['caution'],
    }


def _range_profile(axis, margins):
    return {
        key: [_clamp(axis[key] - margin), _clamp(axis[key] + margin)]
        for key, margin in margins.items()
    }


def _default_second_tone(tone_key):
    season, temperature, tone = split_tone_key(tone_key)
    order = ['light', 'bright', 'mute', 'deep']
    index = order.index(tone) if tone in order else 0
    next_tone = order[(index + 1) % len(order)]
    return f'{season}_{temperature}_{next_tone}'


def _clamp(value):
    return max(0, min(100, round(value)))


TONE_PROFILE_MAP = {tone_key: _build_profile(tone_key) for tone_key in CANONICAL_TONE_KEYS}

TONE_PROFILE_MAP['spring_warm_light']['axis_profile'] = {
    'brightness': 82,
    'saturation': 38,
    'coolness': 18,
    'warmth': 82,
    'depth': 18,
    'softness': 58,
    'contrast': 24,
}
TONE_PROFILE_MAP['spring_warm_light']['range_profile'] = {
    'best': {
        'brightness': [72, 95],
        'saturation': [25, 65],
        'coolness': [0, 35],
        'warmth': [65, 100],
        'depth': [0, 35],
        'softness': [35, 75],
        'contrast': [10, 45],
    },
    'good': {
        'brightness': [60, 100],
        'saturation': [15, 75],
        'coolness': [0, 45],
        'warmth': [55, 100],
        'depth': [0, 45],
        'softness': [25, 85],
        'contrast': [5, 55],
    },
}
TONE_PROFILE_MAP['spring_warm_light']['recommended_color_families'] = ['CORAL', 'PEACH', 'WARM_PINK', 'BEIGE']
TONE_PROFILE_MAP['spring_warm_light']['caution_color_families'] = ['BLUE_PINK', 'LAVENDER', 'BURGUNDY', 'ASH']
