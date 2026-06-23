import json
import logging

from diagnosis.ai_clients.openai_compatible import (
    AIClientConfigurationError,
    AIClientResponseError,
    OpenAICompatibleClient,
)

logger = logging.getLogger(__name__)


EXPLANATION_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'items': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'option_id': {'type': 'string'},
                    'short_reason': {'type': 'string'},
                    'detail_reason': {'type': 'string'},
                    'usage_tip': {'type': 'string'},
                },
                'required': ['option_id', 'short_reason', 'detail_reason', 'usage_tip'],
            },
        },
    },
    'required': ['items'],
}


def attach_ai_explanations(options, *, product, user_tone):
    fallback_map = {str(option['id']): fallback_explanation(option, user_tone) for option in options}
    if not options or not user_tone:
        return _apply_explanations(options, fallback_map), 'skipped'

    try:
        payload = OpenAICompatibleClient().create_chat_json(
            prompt=_build_prompt(options, product, user_tone),
            schema=EXPLANATION_SCHEMA,
            schema_name='product_color_option_explanations',
            temperature=0.25,
            system_prompt=(
                'You explain cosmetic color recommendations in Korean. '
                'Do not change recommendation grades or scores. '
                'Avoid exaggerated certainty and return only valid JSON.'
            ),
        )
        ai_map = {
            str(item.get('option_id')): {
                'short_reason': item.get('short_reason') or '',
                'detail_reason': item.get('detail_reason') or '',
                'usage_tip': item.get('usage_tip') or '',
            }
            for item in payload.get('items', [])
            if item.get('option_id') is not None
        }
        merged = {
            option_id: {
                **fallback,
                **{key: value for key, value in ai_map.get(option_id, {}).items() if value},
            }
            for option_id, fallback in fallback_map.items()
        }
        return _apply_explanations(options, merged), 'ok'
    except (AIClientConfigurationError, AIClientResponseError, TimeoutError, OSError, RuntimeError) as exc:
        logger.warning('Product color explanation generation failed: %s', exc)
        return _apply_explanations(options, fallback_map), 'fallback'


def fallback_explanation(option, user_tone=None):
    grade = option.get('grade') or '분석'
    tone_label = (user_tone or {}).get('tone_label') or (user_tone or {}).get('tone_name') or '현재 톤'
    label = option.get('option_name') or option.get('option_no') or '이 옵션'
    brightness = option.get('brightness')
    saturation = option.get('saturation')
    coolness = option.get('coolness')
    depth_word = '밝은' if _number(brightness) >= 65 else '차분한' if _number(brightness) >= 45 else '딥한'
    chroma_word = '선명한' if _number(saturation) >= 65 else '부드러운' if _number(saturation) <= 40 else '적당한 채도의'
    temp_word = '쿨한' if _number(coolness) >= 60 else '따뜻한' if _number(coolness) <= 40 else '중립적인'

    if grade == 'BEST':
        short = f'{label}은 {depth_word} {temp_word} 색감이라 {tone_label}과 조화로울 가능성이 높습니다.'
        tip = '단독으로 얇게 올리면 데일리 컬러로 쓰기 좋고, 선명도를 더하고 싶을 때 한 번 더 레이어링해보세요.'
    elif grade == 'GOOD':
        short = f'{label}은 {chroma_word} {temp_word} 계열로 부담 없이 시도해볼 수 있는 옵션입니다.'
        tip = '피부톤에 따라 발색이 강하면 양을 줄이거나 비슷한 톤의 베이스와 함께 사용해보세요.'
    elif grade == 'CAUTION':
        short = f'{label}은 일부 축에서 {tone_label} 기준과 차이가 있어 사용 방법을 조절하는 편이 좋습니다.'
        tip = '전체를 진하게 바르기보다 중앙에 소량만 올리거나 더 잘 맞는 베이스 컬러와 섞어 사용해보세요.'
    else:
        short = f'{label}의 색상 특징을 기준으로 참고용 분석을 생성했습니다.'
        tip = '실제 발색은 조명과 피부톤에 따라 달라질 수 있으니 얇게 테스트해보세요.'

    return {
        'short_reason': short,
        'detail_reason': (
            f'이 색상은 명도 {brightness}, 채도 {saturation}, 쿨니스 {coolness} 수준으로 분석되었습니다. '
            f'{depth_word} 인상과 {chroma_word} 발색, {temp_word} 온도감이 함께 나타나므로 추천 등급은 {grade}로 분류했습니다.'
        ),
        'usage_tip': tip,
    }


def _build_prompt(options, product, user_tone):
    compact_options = [
        {
            'option_id': option.get('id'),
            'option_name': option.get('option_name') or option.get('option_no'),
            'hex_code': option.get('hex_code'),
            'brightness': option.get('brightness'),
            'saturation': option.get('saturation'),
            'coolness': option.get('coolness'),
            'depth': option.get('depth'),
            'softness': option.get('softness'),
            'contrast': option.get('contrast'),
            'match_score': option.get('match_score'),
            'grade': option.get('grade'),
            'base_reason': option.get('reason'),
        }
        for option in options
    ]
    return (
        '다음 화장품 옵션 색상 분석 결과를 한국어 추천 설명으로 바꿔주세요.\n'
        'short_reason은 1문장, detail_reason은 2~3문장, usage_tip은 1~2문장으로 작성하세요.\n'
        'CAUTION도 부정적으로만 말하지 말고 활용 팁을 포함하세요.\n'
        f'제품: {json.dumps(product, ensure_ascii=False)}\n'
        f'사용자 퍼스널컬러: {json.dumps(user_tone, ensure_ascii=False)}\n'
        f'옵션 분석값: {json.dumps(compact_options, ensure_ascii=False)}'
    )


def _apply_explanations(options, explanations):
    enriched = []
    for option in options:
        option_id = str(option.get('id'))
        enriched.append({**option, **explanations.get(option_id, fallback_explanation(option))})
    return enriched


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0
