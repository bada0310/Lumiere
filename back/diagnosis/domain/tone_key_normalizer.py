from difflib import get_close_matches

from .tone_keys import SEASON_ALIASES, TONE_ALIASES, TONE_KEY_SET


class ToneKeyError(ValueError):
    pass


def normalize_tone_key(value, *, allow_close_match=False):
    raw = str(value or '').strip().lower()
    if not raw:
        raise ToneKeyError('toneKey is required.')

    parts = raw.replace('-', '_').replace(' ', '_').split('_')
    parts = [part for part in parts if part]

    if len(parts) != 3:
        if allow_close_match:
            close = _closest(raw)
            if close:
                return close
        raise ToneKeyError(f'Invalid toneKey format: {value}')

    season, temperature, tone = parts
    season = SEASON_ALIASES.get(season, season)
    tone = TONE_ALIASES.get(tone, tone)
    candidate = f'{season}_{temperature}_{tone}'

    if candidate in TONE_KEY_SET:
        return candidate

    if allow_close_match:
        close = _closest(candidate)
        if close:
            return close

    raise ToneKeyError(f'Unsupported toneKey: {value}')


def _closest(value):
    normalized = str(value or '').replace('-', '_').replace(' ', '_').lower()
    matches = get_close_matches(normalized, TONE_KEY_SET, n=1, cutoff=0.86)
    return matches[0] if matches else None
