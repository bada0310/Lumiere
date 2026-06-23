import colorsys
import math
import re


NAMED_COLOR_FALLBACKS = {
    '코랄': '#f28f7c',
    'coral': '#f28f7c',
    '피치': '#f4a27f',
    'peach': '#f4a27f',
    '핑크': '#e88da4',
    'pink': '#e88da4',
    '로즈': '#c96b7c',
    'rose': '#c96b7c',
    '레드': '#c9474d',
    'red': '#c9474d',
    '베리': '#a94f70',
    'berry': '#a94f70',
    '모브': '#b87e98',
    'mauve': '#b87e98',
    '라벤더': '#b995cf',
    'lavender': '#b995cf',
    '베이지': '#d6aa8d',
    'beige': '#d6aa8d',
    '브라운': '#9b6047',
    'brown': '#9b6047',
    '누드': '#d49a82',
    'nude': '#d49a82',
    '오렌지': '#e97945',
    'orange': '#e97945',
}


def normalize_hex(value):
    if not value:
        return ''
    match = re.search(r'#?([0-9a-fA-F]{6})\b', str(value))
    return f'#{match.group(1).upper()}' if match else ''


def hex_to_rgb(value):
    hex_value = normalize_hex(value)
    if not hex_value:
        return None
    return tuple(int(hex_value[index:index + 2], 16) for index in (1, 3, 5))


def rgb_to_hex(rgb):
    r, g, b = [_clamp_channel(value) for value in rgb]
    return f'#{r:02X}{g:02X}{b:02X}'


def fallback_hex_from_name(name):
    normalized = str(name or '').lower()
    for token, hex_value in NAMED_COLOR_FALLBACKS.items():
        if token.lower() in normalized:
            return hex_value
    return ''


def build_color_metrics(rgb):
    r, g, b = [_clamp_channel(value) for value in rgb]
    red, green, blue = r / 255, g / 255, b / 255
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    hue_degrees = hue * 360
    channel_spread = max(r, g, b) - min(r, g, b)

    brightness = _clamp(lightness * 100)
    saturation_score = _clamp(saturation * 100)
    coolness = _coolness_from_hue(hue_degrees, saturation_score, r, b)
    contrast = _clamp(channel_spread / 255 * 100)
    softness = _clamp(100 - saturation_score * 0.55 - contrast * 0.2)
    depth = _clamp(100 - brightness)

    metrics = {
        'hex_code': rgb_to_hex((r, g, b)),
        'rgb': [r, g, b],
        'rgb_r': r,
        'rgb_g': g,
        'rgb_b': b,
        'brightness': brightness,
        'saturation': saturation_score,
        'coolness': coolness,
        'warmth': 100 - coolness,
        'depth': depth,
        'softness': softness,
        'contrast': contrast,
        'lightness': brightness,
        'chroma': saturation_score,
        'warm_cool_score': round((coolness - 50) / 50, 2),
        'light_deep_score': round((brightness - 50) / 50, 2),
        'chart_x': coolness,
        'chart_y': _clamp(100 - brightness),
    }
    metrics['color_family'] = infer_color_family(hue_degrees, saturation_score, brightness)
    metrics['analyzed_tone_tag'] = infer_tone_tag(metrics)
    return metrics


def infer_tone_tag(metrics):
    temperature = 'cool' if metrics.get('coolness', 50) >= 50 else 'warm'
    if temperature == 'warm':
        season = 'spring' if metrics.get('brightness', 0) >= 58 else 'autumn'
    else:
        season = 'summer' if metrics.get('brightness', 0) >= 58 else 'winter'

    if metrics.get('brightness', 0) >= 70 and metrics.get('saturation', 0) < 70:
        tone = 'light'
    elif metrics.get('saturation', 0) >= 68 and metrics.get('contrast', 0) >= 35:
        tone = 'bright'
    elif metrics.get('depth', 0) >= 62:
        tone = 'deep'
    else:
        tone = 'mute'
    return f'{season}_{temperature}_{tone}'


def infer_color_family(hue_degrees, saturation, brightness):
    if saturation < 12:
        return 'GRAY'
    if 330 <= hue_degrees or hue_degrees < 12:
        return 'RED'
    if 12 <= hue_degrees < 38:
        return 'CORAL' if brightness >= 48 else 'BROWN'
    if 38 <= hue_degrees < 72:
        return 'BEIGE' if saturation < 45 else 'CORAL'
    if 280 <= hue_degrees < 330:
        return 'LAVENDER' if brightness >= 55 else 'BERRY'
    if 250 <= hue_degrees < 280:
        return 'LAVENDER'
    if 160 <= hue_degrees < 250:
        return 'ETC'
    return 'BROWN' if brightness < 45 else 'BEIGE'


def public_grade_from_score(score):
    try:
        number = float(score)
    except (TypeError, ValueError):
        return ''
    if number >= 85:
        return 'BEST'
    if number >= 55:
        return 'GOOD'
    return 'CAUTION'


def _coolness_from_hue(hue_degrees, saturation, red, blue):
    if saturation < 10:
        base = 50
    elif hue_degrees <= 20 or hue_degrees >= 340:
        base = 48
    elif 20 < hue_degrees < 80:
        base = 20
    elif 80 <= hue_degrees < 160:
        base = 45
    elif 160 <= hue_degrees < 300:
        base = 78
    else:
        base = 70

    blue_bias = blue - red
    if math.fabs(blue_bias) > 12:
        base += max(-12, min(12, blue_bias / 5))
    return _clamp(base)


def _clamp(value):
    try:
        number = round(float(value))
    except (TypeError, ValueError):
        number = 0
    return max(0, min(100, number))


def _clamp_channel(value):
    try:
        number = round(float(value))
    except (TypeError, ValueError):
        number = 0
    return max(0, min(255, number))
