from diagnosis.domain.tone_profiles import build_tone_result_payload
from diagnosis.services.primary import get_primary_diagnosis_for_user
from products.models import ProductOptionToneScore
from products.serializers import ProductOfferSerializer
from products.services.ai_color_explanations import fallback_explanation
from products.services.color_metrics import public_grade_from_score
from products.services.recommendation import build_user_tone_profile, calculate_option_match


def build_product_color_analysis_payload(product, *, request):
    tone_payload = _tone_payload_from_request(request)
    user_profile = _user_profile_from_payload(tone_payload)
    options = [_option_payload(option, user_profile) for option in _product_options(product)]
    best_option = _best_option(options)

    return {
        'product': {
            'id': product.id,
            'url': product.product_url,
            'brand_name': product.brand,
            'product_name': product.name,
            'category': product.category,
            'description': product.description,
            'thumbnail_url': product.display_image_url,
        },
        'user_tone': _public_tone_payload(tone_payload),
        'personalized': bool(user_profile),
        'chart': {
            'axis': {'x': 'warmCool', 'y': 'lightDeep'},
            'zones': _chart_zones(tone_payload),
        },
        'options': options,
        'best_option': best_option,
        'recommendation_groups': _recommendation_groups(options),
        'ai_explanation_status': 'fallback',
        'disclaimer': (
            '화면의 색상은 실제와 다를 수 있으며, 개인차가 있을 수 있습니다. '
            'AI 분석 결과는 참고용이며 실제 발색은 피부톤, 조명, 모니터 환경에 따라 달라질 수 있습니다.'
        ),
    }


def _tone_payload_from_request(request):
    tone_key = request.query_params.get('tone_key')
    second_tone_key = request.query_params.get('second_tone_key')
    if tone_key:
        return build_tone_result_payload(tone_key, second_tone_key)

    if not request.user.is_authenticated:
        return None

    diagnosis = get_primary_diagnosis_for_user(request.user)
    if not diagnosis:
        return None

    payload = build_tone_result_payload(
        diagnosis.tone_key or diagnosis.personal_color_code,
        (diagnosis.diagnosis_json or {}).get('second_tone_key'),
    )
    payload['diagnosis_id'] = diagnosis.id
    return payload


def _user_profile_from_payload(tone_payload):
    if not tone_payload:
        return None
    return build_user_tone_profile(
        tone_key=tone_payload.get('tone_key'),
        second_tone_key=tone_payload.get('second_tone_key'),
        axis_profile=tone_payload.get('axis_profile'),
        range_profile=tone_payload.get('range_profile'),
    )


def _option_payload(option, user_profile):
    if user_profile:
        match = calculate_option_match(option, user_profile, option.product.category)
        match_score = match['match_score']
        grade = public_grade_from_score(match_score)
        reason = match['reason']
    else:
        match_score = None
        grade = ''
        reason = '메인 퍼스널컬러가 설정되면 개인화 추천 이유를 확인할 수 있습니다.'

    payload = {
        'id': option.id,
        'option_no': option.option_no,
        'option_name': option.option_name,
        'option_key': option.option_key,
        'image_url': option.image_url,
        'color_family': option.color_family,
        'analyzed_tone_tag': option.analyzed_tone_tag,
        'hex_code': option.hex_code,
        'rgb': [option.rgb_r, option.rgb_g, option.rgb_b],
        'rgb_r': option.rgb_r,
        'rgb_g': option.rgb_g,
        'rgb_b': option.rgb_b,
        'brightness': option.brightness,
        'saturation': option.saturation,
        'coolness': option.coolness,
        'warmth': option.warmth,
        'depth': option.depth,
        'softness': option.softness,
        'contrast': option.contrast,
        'chart_x': option.coolness,
        'chart_y': max(0, min(100, 100 - option.brightness)),
        'match_score': match_score,
        'grade': grade,
        'reason': reason,
        'representative_offer': _representative_offer(option),
        'offers': ProductOfferSerializer(_option_offers(option), many=True).data,
        'tone_scores': _tone_scores(option),
    }
    payload.update(fallback_explanation(payload))
    return payload


def _product_options(product):
    return list(getattr(product, '_prefetched_objects_cache', {}).get('options', []) or product.options.all())


def _option_offers(option):
    return list(getattr(option, '_prefetched_objects_cache', {}).get('offers', []) or option.offers.all())


def _representative_offer(option):
    offers = _option_offers(option)
    representative = next((offer for offer in offers if offer.is_representative), None)
    if representative is None and offers:
        representative = sorted(offers, key=lambda offer: (offer.price or 10**12, offer.id))[0]
    return ProductOfferSerializer(representative).data if representative else None


def _tone_scores(option):
    scores = list(getattr(option, '_prefetched_objects_cache', {}).get('tone_scores', []) or option.tone_scores.all())
    return [
        {
            'id': score.id,
            'target_tone': score.target_tone,
            'match_score': score.match_score,
            'grade': score.grade,
            'reason': score.reason,
        }
        for score in scores
    ]


def _best_option(options):
    scored = [option for option in options if option.get('match_score') is not None]
    if not scored:
        return options[0] if options else None
    return max(scored, key=lambda option: option.get('match_score') or 0)


def _recommendation_groups(options):
    groups = {'BEST': [], 'GOOD': [], 'CAUTION': []}
    for option in options:
        grade = option.get('grade')
        if grade in groups:
            groups[grade].append(option.get('id'))
    return groups


def _chart_zones(tone_payload):
    if not tone_payload:
        return []
    range_profile = tone_payload.get('range_profile') or {}
    return [
        {'type': 'GOOD', 'range': range_profile.get('good')},
        {'type': 'BEST', 'range': range_profile.get('best')},
    ]


def _public_tone_payload(tone_payload):
    if not tone_payload:
        return None
    return {
        'diagnosis_id': tone_payload.get('diagnosis_id'),
        'tone_key': tone_payload.get('tone_key'),
        'tone_label': tone_payload.get('tone_label'),
        'tone_name': tone_payload.get('tone_label'),
        'second_tone_key': tone_payload.get('second_tone_key'),
        'second_tone_label': tone_payload.get('second_tone_label'),
        'axis_profile': tone_payload.get('axis_profile'),
        'range_profile': tone_payload.get('range_profile'),
        'recommended_color_families': tone_payload.get('recommended_color_families', []),
        'caution_color_families': tone_payload.get('caution_color_families', []),
    }
