CANONICAL_TONE_KEYS = [
    'spring_warm_bright',
    'spring_warm_light',
    'spring_warm_mute',
    'spring_warm_deep',
    'spring_cool_bright',
    'spring_cool_light',
    'spring_cool_mute',
    'spring_cool_deep',
    'summer_warm_bright',
    'summer_warm_light',
    'summer_warm_mute',
    'summer_warm_deep',
    'summer_cool_bright',
    'summer_cool_light',
    'summer_cool_mute',
    'summer_cool_deep',
    'autumn_warm_bright',
    'autumn_warm_light',
    'autumn_warm_mute',
    'autumn_warm_deep',
    'autumn_cool_bright',
    'autumn_cool_light',
    'autumn_cool_mute',
    'autumn_cool_deep',
    'winter_warm_bright',
    'winter_warm_light',
    'winter_warm_mute',
    'winter_warm_deep',
    'winter_cool_bright',
    'winter_cool_light',
    'winter_cool_mute',
    'winter_cool_deep',
]

TONE_KEY_CHOICES = [(key, key) for key in CANONICAL_TONE_KEYS]
TONE_KEY_SET = set(CANONICAL_TONE_KEYS)

SEASON_ALIASES = {
    'fall': 'autumn',
}

TONE_ALIASES = {
    'muted': 'mute',
    'soft': 'mute',
    'clear': 'bright',
    'vivid': 'bright',
    'dark': 'deep',
}

SEASON_KO = {
    'spring': '봄',
    'summer': '여름',
    'autumn': '가을',
    'winter': '겨울',
}

TEMPERATURE_KO = {
    'warm': '웜',
    'cool': '쿨',
}

TONE_KO = {
    'bright': '브라이트',
    'light': '라이트',
    'mute': '뮤트',
    'deep': '딥',
}


def split_tone_key(tone_key):
    season, temperature, tone = tone_key.split('_', 2)
    return season, temperature, tone


def build_tone_name(tone_key):
    season, temperature, tone = split_tone_key(tone_key)
    return f'{SEASON_KO.get(season, season)} {TEMPERATURE_KO.get(temperature, temperature)} {TONE_KO.get(tone, tone)}'


def tone_key_to_personal_color_fields(tone_key):
    season, temperature, tone = split_tone_key(tone_key)
    return {
        'season': 'fall' if season == 'autumn' else season,
        'base_temperature': temperature,
        'tone': tone.upper(),
    }
