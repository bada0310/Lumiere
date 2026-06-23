from diagnosis.domain.tone_profiles import get_tone_profile, normalize_profile_tone_key
from diagnosis.domain.tone_keys import split_tone_key
from products.models import Product, ProductOptionToneScore


ADJACENT_TONES = {
    'light': {'bright', 'mute'},
    'bright': {'light'},
    'mute': {'light', 'deep'},
    'deep': {'mute'},
}


def build_user_tone_profile(tone_key=None, second_tone_key=None, axis_profile=None, range_profile=None):
    profile = get_tone_profile(tone_key)
    if second_tone_key:
        profile['second_tone_key'] = normalize_profile_tone_key(second_tone_key)
    else:
        profile['second_tone_key'] = profile['tone_key']
    if axis_profile:
        profile['axis_profile'] = {
            **profile['axis_profile'],
            **{key: _clamp(value) for key, value in axis_profile.items()},
        }
    if range_profile:
        profile['range_profile'] = range_profile
    return profile


def calculate_option_match(option, user_profile, category=None):
    category = category or getattr(getattr(option, 'product', None), 'category', '')
    axis = user_profile.get('axis_profile') or {}
    if category == Product.Category.BASE:
        score = _base_score(option, axis, user_profile)
    else:
        score = _color_score(option, axis, user_profile)

    score = _clamp(score)
    grade = grade_from_score(score)
    return {
        'match_score': score,
        'grade': grade,
        'reason': build_reason(option, axis, grade),
    }


def grade_from_score(score):
    score = _clamp(score)
    if score >= 85:
        return ProductOptionToneScore.Grade.BEST
    if score >= 70:
        return ProductOptionToneScore.Grade.GOOD
    if score >= 55:
        return ProductOptionToneScore.Grade.OK
    return ProductOptionToneScore.Grade.CAUTION


def tone_fit_score(option_tone, user_profile):
    option_key = normalize_profile_tone_key(option_tone)
    primary = normalize_profile_tone_key(user_profile.get('tone_key'))
    secondary = normalize_profile_tone_key(user_profile.get('second_tone_key') or primary)

    if option_key == primary:
        return 35
    if option_key == secondary:
        return 28

    option_season, _, option_tone_detail = split_tone_key(option_key)
    primary_season, _, primary_tone_detail = split_tone_key(primary)
    if option_season == primary_season:
        if option_tone_detail in ADJACENT_TONES.get(primary_tone_detail, set()):
            return 20
        return 14
    return 5


def _color_score(option, axis, user_profile):
    return (
        tone_fit_score(getattr(option, 'analyzed_tone_tag', ''), user_profile)
        + max(0, 15 - abs(_metric(axis, 'brightness') - _metric(option, 'brightness')) * 0.3)
        + max(0, 15 - abs(_metric(axis, 'saturation') - _metric(option, 'saturation')) * 0.3)
        + max(0, 20 - abs(_metric(axis, 'coolness') - _metric(option, 'coolness')) * 0.4)
        + max(0, 10 - abs(_metric(axis, 'softness') - _metric(option, 'softness')) * 0.2)
        + max(0, 5 - abs(_metric(axis, 'contrast') - _metric(option, 'contrast')) * 0.1)
    )


def _base_score(option, axis, user_profile):
    return (
        min(15, tone_fit_score(getattr(option, 'analyzed_tone_tag', ''), user_profile) * 15 / 35)
        + max(0, 30 - abs(_metric(axis, 'brightness') - _metric(option, 'brightness')) * 0.45)
        + max(0, 30 - abs(_metric(axis, 'coolness') - _metric(option, 'coolness')) * 0.5)
        + max(0, 10 - abs(_metric(axis, 'saturation') - _metric(option, 'saturation')) * 0.2)
        + max(0, 10 - abs(_metric(axis, 'softness') - _metric(option, 'softness')) * 0.2)
        + max(0, 5 - abs(_metric(axis, 'contrast') - _metric(option, 'contrast')) * 0.1)
    )


def build_reason(option, axis, grade):
    diffs = {
        'brightness': abs(_metric(axis, 'brightness') - _metric(option, 'brightness')),
        'saturation': abs(_metric(axis, 'saturation') - _metric(option, 'saturation')),
        'coolness': abs(_metric(axis, 'coolness') - _metric(option, 'coolness')),
        'softness': abs(_metric(axis, 'softness') - _metric(option, 'softness')),
        'contrast': abs(_metric(axis, 'contrast') - _metric(option, 'contrast')),
    }
    best_axis = min(diffs, key=diffs.get)
    labels = {
        'brightness': 'brightness',
        'saturation': 'saturation',
        'coolness': 'warm-cool balance',
        'softness': 'softness',
        'contrast': 'contrast',
    }
    return f'{grade} match based on {labels[best_axis]} similarity.'


def best_option_for_product(product, user_profile):
    options = list(getattr(product, '_prefetched_objects_cache', {}).get('options', []) or product.options.all())
    if not options:
        return None
    return max(
        options,
        key=lambda option: calculate_option_match(option, user_profile, product.category)['match_score'],
    )


def _metric(source, key):
    if isinstance(source, dict):
        return _clamp(source.get(key, 0))
    return _clamp(getattr(source, key, 0))


def _clamp(value):
    try:
        number = round(float(value))
    except (TypeError, ValueError):
        number = 0
    return max(0, min(100, number))
