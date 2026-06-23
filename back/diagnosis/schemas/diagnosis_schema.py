from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS

DIAGNOSIS_JSON_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['toneKey', 'toneName', 'confidence', 'summary', 'analysis', 'evidence', 'cautions'],
    'properties': {
        'toneKey': {'type': 'string', 'enum': CANONICAL_TONE_KEYS},
        'tone_key': {'type': 'string', 'enum': CANONICAL_TONE_KEYS},
        'toneName': {'type': 'string', 'minLength': 1},
        'tone_label': {'type': 'string', 'minLength': 1},
        'second_tone_key': {'type': 'string', 'enum': CANONICAL_TONE_KEYS},
        'second_tone_label': {'type': 'string', 'minLength': 1},
        'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
        'summary': {'type': 'string', 'minLength': 1},
        'axis_profile': {
            'type': 'object',
            'additionalProperties': {'type': 'number', 'minimum': 0, 'maximum': 100},
        },
        'range_profile': {
            'type': 'object',
            'properties': {
                'best': {'$ref': '#/$defs/metricRangeProfile'},
                'good': {'$ref': '#/$defs/metricRangeProfile'},
            },
            'additionalProperties': False,
        },
        'recommended_color_families': {'type': 'array', 'items': {'type': 'string'}},
        'caution_color_families': {'type': 'array', 'items': {'type': 'string'}},
        'analysis': {
            'type': 'object',
            'additionalProperties': False,
            'required': [
                'temperature',
                'brightness',
                'chroma',
                'contrast',
                'skinUndertone',
                'recommendedIntensity',
            ],
            'properties': {
                'temperature': {'type': 'string', 'enum': ['warm', 'cool', 'neutral']},
                'brightness': {
                    'type': 'string',
                    'enum': ['low', 'medium_low', 'medium', 'medium_high', 'high'],
                },
                'chroma': {
                    'type': 'string',
                    'enum': ['low', 'low_to_medium', 'medium_low', 'medium', 'medium_high', 'high'],
                },
                'contrast': {'type': 'string', 'enum': ['low', 'medium_low', 'medium', 'medium_high', 'high']},
                'skinUndertone': {'type': 'string', 'minLength': 1},
                'recommendedIntensity': {'type': 'string', 'minLength': 1},
            },
        },
        'evidence': {
            'type': 'object',
            'additionalProperties': False,
            'required': ['skinToneReason', 'contrastReason', 'chromaReason'],
            'properties': {
                'skinToneReason': {'type': 'string', 'minLength': 1},
                'contrastReason': {'type': 'string', 'minLength': 1},
                'chromaReason': {'type': 'string', 'minLength': 1},
            },
        },
        'cautions': {
            'type': 'array',
            'minItems': 1,
            'items': {'type': 'string', 'minLength': 1},
        },
    },
    '$defs': {
        'metricRangeProfile': {
            'type': 'object',
            'additionalProperties': {
                'type': 'array',
                'minItems': 2,
                'maxItems': 2,
                'items': {'type': 'number', 'minimum': 0, 'maximum': 100},
            },
        },
    },
}

LOW_CONFIDENCE_THRESHOLD = 0.65
