from diagnosis.domain.tone_key_normalizer import ToneKeyError, normalize_tone_key
from diagnosis.domain.tone_keys import build_tone_name


class ToneCandidateValidationError(ValueError):
    pass


def english_name(tone_key):
    return ' '.join(part.title() for part in str(tone_key or '').split('_'))


def normalize_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise ToneCandidateValidationError('Tone candidate confidence must be a number.') from exc

    if 0 <= confidence <= 1:
        confidence *= 100

    if confidence < 0 or confidence > 100:
        raise ToneCandidateValidationError('Tone candidate confidence must be between 0 and 100.')

    return round(confidence)


def normalize_candidate(candidate, index=0):
    if not isinstance(candidate, dict):
        raise ToneCandidateValidationError('Tone candidate must be an object.')

    raw_tone_key = (
        candidate.get('tone_key')
        or candidate.get('toneKey')
        or candidate.get('code')
        or candidate.get('type')
        or candidate.get('personal_color_code')
    )

    try:
        tone_key = normalize_tone_key(raw_tone_key, allow_close_match=False)
    except ToneKeyError as exc:
        raise ToneCandidateValidationError(str(exc)) from exc

    confidence = normalize_confidence(
        candidate.get('confidence')
        if candidate.get('confidence') is not None
        else candidate.get('confidence_score', candidate.get('score'))
    )

    return {
        'rank': int(candidate.get('rank') or index + 1),
        'tone_key': tone_key,
        'toneNameKo': candidate.get('toneNameKo')
        or candidate.get('tone_name_ko')
        or candidate.get('toneName')
        or candidate.get('tone_name')
        or candidate.get('korean_name')
        or build_tone_name(tone_key),
        'toneNameEn': candidate.get('toneNameEn') or candidate.get('tone_name_en') or candidate.get('english_name') or english_name(tone_key),
        'confidence': confidence,
        'reason': str(candidate.get('reason') or candidate.get('description') or candidate.get('summary') or '').strip(),
    }


def normalize_candidate_list(candidates):
    if not candidates:
        return []
    if not isinstance(candidates, list):
        raise ToneCandidateValidationError('tone_candidates must be a list.')

    normalized = []
    seen = set()
    for index, candidate in enumerate(candidates):
        item = normalize_candidate(candidate, index)
        if item['tone_key'] in seen:
            continue
        seen.add(item['tone_key'])
        normalized.append(item)

    return sorted(normalized, key=lambda item: item['rank'])


def normalize_tone_candidates_for_ai(candidates, *, primary_tone_key, primary_confidence):
    normalized = normalize_candidate_list(candidates)
    if len(normalized) < 2:
        raise ToneCandidateValidationError('tone_candidates must include primary and secondary candidates.')

    try:
        primary = normalize_tone_key(primary_tone_key, allow_close_match=False)
    except ToneKeyError as exc:
        raise ToneCandidateValidationError(str(exc)) from exc

    first = normalized[0]
    if first['tone_key'] != primary:
        raise ToneCandidateValidationError('The first tone candidate must match the primary tone_key.')

    primary_score = normalize_confidence(primary_confidence)
    if first['confidence'] != primary_score:
        first['confidence'] = primary_score

    secondary = next((candidate for candidate in normalized[1:] if candidate['tone_key'] != primary), None)
    if not secondary:
        raise ToneCandidateValidationError('Secondary tone candidate must be different from primary tone_key.')

    if secondary['confidence'] > primary_score:
        raise ToneCandidateValidationError('Secondary tone candidate confidence must not exceed primary confidence.')

    return normalized


def get_secondary_tone(candidates, primary_tone_key):
    try:
        primary = normalize_tone_key(primary_tone_key, allow_close_match=False)
    except ToneKeyError:
        primary = str(primary_tone_key or '')

    return next((candidate for candidate in candidates if candidate.get('tone_key') != primary and candidate.get('rank') != 1), None)
