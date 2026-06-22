from .tone_keys import CANONICAL_TONE_KEYS, build_tone_name

PERSONAL_COLOR_CRITERIA = [
    {
        'toneKey': tone_key,
        'toneName': build_tone_name(tone_key),
        'rule': 'Choose this key only when season, temperature, brightness, chroma, and contrast best match the face image.',
    }
    for tone_key in CANONICAL_TONE_KEYS
]

PERSONAL_COLOR_CRITERIA_TEXT = '\n'.join(
    f"- {item['toneKey']}: {item['toneName']} - {item['rule']}" for item in PERSONAL_COLOR_CRITERIA
)
