import logging

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from diagnosis.ai_clients.openai_compatible import (
    AIClientConfigurationError,
)
from diagnosis.domain.tone_profiles import build_tone_result_payload
from diagnosis.services.primary import get_primary_diagnosis_for_user
from Lumiere.api_pagination import list_response
from products.models import (
    Product,
    ProductImageAnalysis,
    ProductOffer,
    ProductOption,
    ProductOptionToneScore,
    Review,
)
from products.serializers import (
    ProductImageAnalysisRequestSerializer,
    ProductImageAnalysisSummarySerializer,
    ProductImageAnalysisUpdateSerializer,
    ProductSerializer,
    ReviewSerializer,
)
from products.services.catalog_color_analysis import build_product_color_analysis_payload
from products.services.image_color_analysis import (
    NoColorCandidatesFoundError,
    ProductImageAnalysisPipeline,
    build_product_image_analysis_payload,
    confirm_analysis,
    update_analysis_from_review,
)
from products.services.recommendation import build_user_tone_profile, calculate_option_match


logger = logging.getLogger(__name__)
IMAGE_ANALYSIS_SAVE_FAILED_MESSAGE = 'The uploaded image could not be saved for analysis.'
IMAGE_ANALYSIS_FAILED_MESSAGE = 'Product image analysis failed unexpectedly.'


def validation_error_message(exc):
    if hasattr(exc, 'message'):
        return exc.message
    if hasattr(exc, 'messages') and exc.messages:
        return exc.messages[0]
    return str(exc)


def mark_product_image_analysis_failed(analysis, *, code, message, exc=None):
    """Persist analysis failure metadata without deleting the uploaded analysis row."""
    if not analysis or not analysis.pk:
        return None

    raw_payload = analysis.raw_ai_response if isinstance(analysis.raw_ai_response, dict) else {}
    raw_meta = raw_payload.get('analysis_meta') if isinstance(raw_payload.get('analysis_meta'), dict) else {}

    error_message = message or (str(exc) if exc else '')

    raw_payload['analysis_meta'] = {
        **raw_meta,
        'success': False,
        'code': code,
        'error_type': exc.__class__.__name__ if exc else '',
        'error_message': str(exc) if exc else error_message,
        'message': error_message,
    }

    analysis.raw_ai_response = raw_payload
    try:
        analysis.save(update_fields=['raw_ai_response', 'updated_at'])
    except Exception:
        logger.exception(
            'Failed to persist product image analysis failure metadata. analysis_id=%s code=%s',
            analysis.pk,
            code,
        )
    return analysis.pk


def product_image_analysis_error_response(analysis, *, code, message, http_status, exc=None, detail=None):
    analysis_id = mark_product_image_analysis_failed(
        analysis,
        code=code,
        message=message,
        exc=exc,
    )
    body = {
        'success': False,
        'analysis_id': analysis_id,
        'code': code,
        'message': message,
    }
    if detail is not None:
        body['detail'] = detail
    elif exc is not None:
        body['detail'] = str(exc)
    return Response(body, status=http_status)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


def product_queryset(request, apply_filters=True):
    offer_queryset = ProductOffer.objects.order_by('price', 'id')
    tone_score_queryset = ProductOptionToneScore.objects.order_by('-match_score', 'target_tone', 'id')
    option_queryset = (
        ProductOption.objects.select_related('product')
        .prefetch_related(
            Prefetch('offers', queryset=offer_queryset),
            Prefetch('tone_scores', queryset=tone_score_queryset),
        )
        .order_by('option_no', 'option_name', 'id')
    )
    queryset = (
        Product.objects.all()
        .annotate(
            review_count=Count('reviews', distinct=True),
            average_rating=Avg('reviews__rating'),
        )
        .prefetch_related(Prefetch('options', queryset=option_queryset))
    )
    if not apply_filters:
        return queryset

    category = request.query_params.get('category')
    keyword = request.query_params.get('q')

    if category:
        queryset = queryset.filter(category=category)
    if keyword:
        queryset = queryset.filter(Q(name__icontains=keyword) | Q(brand__icontains=keyword))
    return queryset


def user_tone_profile_from_request(request):
    tone_key = request.query_params.get('tone_key')
    second_tone_key = request.query_params.get('second_tone_key')
    axis_profile = None
    range_profile = None

    if not tone_key and request.user.is_authenticated:
        try:
            diagnosis = get_primary_diagnosis_for_user(request.user)
        except Exception:
            diagnosis = None
        if diagnosis:
            profile_payload = build_tone_result_payload(
                diagnosis.tone_key or diagnosis.personal_color_code,
                (diagnosis.diagnosis_json or {}).get('second_tone_key'),
            )
            tone_key = profile_payload['tone_key']
            second_tone_key = profile_payload['second_tone_key']
            axis_profile = profile_payload['axis_profile']
            range_profile = profile_payload['range_profile']

    return build_user_tone_profile(
        tone_key=tone_key,
        second_tone_key=second_tone_key,
        axis_profile=axis_profile,
        range_profile=range_profile,
    )


def sort_products_by_best_option(products, user_profile):
    def best_score(product):
        options = list(getattr(product, '_prefetched_objects_cache', {}).get('options', []) or [])
        if not options:
            return getattr(product, 'match_score', 0) or 0
        return max(
            calculate_option_match(option, user_profile, product.category)['match_score']
            for option in options
        )

    return sorted(products, key=best_score, reverse=True)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return product_queryset(self.request)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_tone_profile'] = user_tone_profile_from_request(self.request)
        context['option_match_cache'] = {}
        return context

    def list(self, request, *args, **kwargs):
        user_profile = user_tone_profile_from_request(request)
        products = sort_products_by_best_option(list(self.get_queryset()), user_profile)
        serializer = self.get_serializer(
            products,
            many=True,
            context={**self.get_serializer_context(), 'user_tone_profile': user_profile},
        )
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.select_related('product', 'author')
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset


@api_view(['GET'])
def product_list(request):
    user_profile = user_tone_profile_from_request(request)
    products = sort_products_by_best_option(list(product_queryset(request)), user_profile)
    serializer = ProductSerializer(
        products,
        many=True,
        context={'request': request, 'user_tone_profile': user_profile, 'option_match_cache': {}},
    )
    return Response(serializer.data)


@api_view(['GET'])
def product_detail(request, product_id):
    user_profile = user_tone_profile_from_request(request)
    product = get_object_or_404(product_queryset(request, apply_filters=False), pk=product_id)
    serializer = ProductSerializer(
        product,
        context={'request': request, 'user_tone_profile': user_profile, 'option_match_cache': {}},
    )
    return Response(serializer.data)


@api_view(['GET'])
def product_catalog_color_analysis(request, product_id):
    product = get_object_or_404(product_queryset(request, apply_filters=False), pk=product_id)
    return Response(build_product_color_analysis_payload(product, request=request))


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def personalized_recommendation_products(request):
    limit = _positive_int(request.query_params.get('limit'), 12)
    per_category = _positive_int(request.query_params.get('per_category'), 2)
    user_profile = user_tone_profile_from_request(request)
    queryset = product_queryset(request, apply_filters=False).filter(options__isnull=False).distinct()
    sorted_products = sort_products_by_best_option(list(queryset), user_profile)
    sorted_products = [
        product
        for product in sorted_products
        if _product_recommendation_status(product, user_profile) != 'AVOID'
    ]
    selected_products, balance = _balanced_recommendation_products(
        sorted_products,
        limit=limit,
        per_category=per_category,
    )
    results = [_recommendation_summary(product, request) for product in selected_products]
    return Response(
        {
            'count': len(results),
            'results': results,
            'category_balance': balance,
        },
        status=status.HTTP_200_OK,
    )


def _product_recommendation_status(product, user_profile):
    options = list(getattr(product, '_prefetched_objects_cache', {}).get('options', []) or product.options.all())
    if not options:
        return _recommendation_status(getattr(product, 'match_score', None))
    best_score = max(
        calculate_option_match(option, user_profile, product.category)['match_score']
        for option in options
    )
    return _recommendation_status(best_score)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def recommendation_color_matching(request, product_id):
    product = get_object_or_404(
        product_queryset(request, apply_filters=False).filter(options__isnull=False).distinct(),
        pk=product_id,
    )
    payload = build_product_color_analysis_payload(product, request=request)
    best_option = _enrich_recommendation_option(payload.get('best_option'))
    options = [_enrich_recommendation_option(option) for option in payload.get('options', [])]
    payload['product'] = {
        **payload.get('product', {}),
        'brand': product.brand,
        'name': product.name,
        'image_url': product.display_image_url,
        'product_url': product.product_url,
    }
    payload['options'] = options
    payload['best_option'] = best_option
    payload['match_status'] = best_option.get('match_status') if best_option else ''
    payload['summary_reason'] = _friendly_recommendation_reason(best_option)
    payload['comparison_metrics'] = _comparison_metrics(payload.get('user_tone'), best_option)
    return Response(payload, status=status.HTTP_200_OK)


def _balanced_recommendation_products(products, *, limit, per_category):
    target_categories = [Product.Category.LIP, Product.Category.EYE, Product.Category.BASE, Product.Category.CHEEK]
    selected = []
    selected_ids = set()
    actual = {category: 0 for category in target_categories}

    for category in target_categories:
        category_products = [product for product in products if product.category == category]
        for product in category_products[:per_category]:
            selected.append(product)
            selected_ids.add(product.id)
            actual[category] += 1

    for product in products:
        if len(selected) >= limit:
            break
        if product.id in selected_ids:
            continue
        selected.append(product)
        selected_ids.add(product.id)
        if product.category in actual:
            actual[product.category] += 1

    return selected[:limit], {
        'requested_total': limit,
        'requested_per_category': per_category,
        'actual': actual,
        'filled_with_alternatives': max(0, len(selected[:limit]) - sum(min(per_category, actual[category]) for category in target_categories)),
    }


def _recommendation_summary(product, request):
    payload = build_product_color_analysis_payload(product, request=request)
    best_option = _enrich_recommendation_option(payload.get('best_option'))
    options = [_enrich_recommendation_option(option) for option in payload.get('options', [])]
    representative_offer = best_option.get('representative_offer') if best_option else None
    return {
        'id': product.id,
        'brand': product.brand,
        'name': product.name,
        'category': product.category,
        'image_url': best_option.get('image_url') if best_option else product.display_image_url,
        'product_url': (representative_offer or {}).get('product_url') or product.product_url,
        'best_option': best_option,
        'options': options,
        'match_status': best_option.get('match_status') if best_option else '',
        'match_score': best_option.get('match_score') if best_option else None,
        'short_reason': _friendly_recommendation_reason(best_option),
        'detail_reason': best_option.get('detail_reason') if best_option else '',
        'usage_tip': best_option.get('usage_tip') if best_option else '',
        'personalized': payload.get('personalized', False),
    }


def _enrich_recommendation_option(option):
    if not option:
        return {}
    status_label = _recommendation_status(option.get('match_score'))
    return {
        **option,
        'match_status': status_label,
        'is_precise_color': _has_complete_color_metrics(option),
    }


def _recommendation_status(score):
    try:
        number = float(score)
    except (TypeError, ValueError):
        return ''
    if number >= 85:
        return 'BEST'
    if number >= 70:
        return 'GOOD'
    if number >= 40:
        return 'CAUTION'
    return 'AVOID'


def _friendly_recommendation_reason(option):
    if not option:
        return '아직 추천할 수 있는 색상 옵션 정보가 충분하지 않아요.'
    status_label = option.get('match_status') or _recommendation_status(option.get('match_score'))
    brightness = _metric_value(option, 'brightness')
    saturation = _metric_value(option, 'saturation')
    coolness = _metric_value(option, 'coolness')
    option_name = ' '.join(part for part in [option.get('option_no'), option.get('option_name')] if part) or '이 옵션'
    light_word = '밝고 맑은' if brightness >= 65 else '차분한' if brightness >= 45 else '깊이 있는'
    chroma_word = '생기 있는' if saturation >= 55 else '부드러운'
    temp_word = '쿨한' if coolness >= 60 else '따뜻한' if coolness <= 40 else '중립적인'

    if status_label == 'BEST':
        return f'{option_name}은 {light_word} {temp_word} 톤이라 피부가 맑아 보이기 쉬운 추천 옵션이에요.'
    if status_label == 'GOOD':
        return f'{option_name}은 {chroma_word} 색감이 부담 없이 어울려 데일리로 쓰기 좋은 편이에요.'
    if status_label == 'MIX':
        return f'{option_name}은 단독보다 비슷한 계열의 밝은 색과 섞으면 더 자연스럽게 어울려요.'
    if status_label == 'CAUTION':
        return f'{option_name}은 살짝 튀어 보일 수 있어 양을 줄이거나 포인트로 쓰는 편이 좋아요.'
    if status_label == 'AVOID':
        return f'{option_name}은 현재 퍼스널 컬러 기준과 차이가 커서 신중하게 테스트해보는 편이 좋아요.'
    return '퍼스널 컬러 진단을 설정하면 더 정확한 추천 이유를 볼 수 있어요.'


def _comparison_metrics(user_tone, option):
    if not option:
        return []
    axis = (user_tone or {}).get('axis_profile') or {}
    metric_specs = [
        ('brightness', '명도'),
        ('saturation', '채도'),
        ('coolness', '쿨 경향'),
        ('warmth', '웜 경향'),
        ('softness', '부드러움'),
        ('contrast', '대비'),
    ]
    rows = []
    for key, label in metric_specs:
        user_value = _metric_value(axis, key)
        product_value = _metric_value(option, key)
        diff = abs(user_value - product_value)
        rows.append(
            {
                'key': key,
                'label': label,
                'user_value': user_value,
                'product_value': product_value,
                'diff': diff,
                'explanation': _metric_explanation(label, diff),
            }
        )
    return rows


def _metric_explanation(label, diff):
    if diff <= 8:
        return f'{label} 차이가 작아 자연스럽게 이어지는 편이에요.'
    if diff <= 20:
        return f'{label} 차이가 있어 발색 강도를 조절하면 좋아요.'
    return f'{label} 차이가 커서 포인트 사용을 권장해요.'


def _has_complete_color_metrics(option):
    required = ['hex_code', 'brightness', 'saturation', 'coolness', 'warmth']
    return all(option.get(key) not in [None, ''] for key in required)


def _metric_value(source, key):
    try:
        return round(float(source.get(key, 0)))
    except (AttributeError, TypeError, ValueError):
        return 0


def _positive_int(value, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, number)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def product_image_analysis(request):
    if not request.FILES.get('image'):
        return Response(
            {
                'success': False,
                'analysis_id': None,
                'code': 'IMAGE_REQUIRED',
                'message': 'An image file is required for product image analysis.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ProductImageAnalysisRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    analysis = None
    try:
        analysis = ProductImageAnalysis.objects.create(
            user=request.user,
            product_name=validated.get('product_name', ''),
            brand_name=validated.get('brand_name', ''),
            category=validated.get('category') or Product.Category.ETC,
            uploaded_image=validated['image'],
        )
        logger.info(
            'Product image analysis request saved. analysis_id=%s user_id=%s category=%s image_name=%s image_path=%s',
            analysis.id,
            request.user.id,
            analysis.category,
            analysis.uploaded_image.name,
            getattr(analysis.uploaded_image, 'path', ''),
        )

        pipeline = ProductImageAnalysisPipeline(analysis)
        payload = pipeline.run()

    except NoColorCandidatesFoundError as exc:
        logger.warning(
            'Product image analysis found no color candidates. analysis_id=%s error=%s',
            analysis.id if analysis else None,
            exc,
        )
        return product_image_analysis_error_response(
            analysis,
            code='NO_COLOR_CANDIDATES_FOUND',
            message=str(exc),
            detail=str(exc),
            exc=exc,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    except AIClientConfigurationError as exc:
        logger.exception(
            'Product image analysis AI configuration failed. analysis_id=%s error=%s',
            analysis.id if analysis else None,
            exc,
        )
        return product_image_analysis_error_response(
            analysis,
            code='IMAGE_ANALYSIS_UNAVAILABLE',
            message=str(exc),
            detail=str(exc),
            exc=exc,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except ValidationError as exc:
        message = validation_error_message(exc)
        logger.exception(
            'Product image analysis validation failed. analysis_id=%s error=%s',
            analysis.id if analysis else None,
            message,
        )
        return product_image_analysis_error_response(
            analysis,
            code='INVALID_IMAGE',
            message=message,
            detail=message,
            exc=exc,
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    except (DatabaseError, OSError, ValueError) as exc:
        logger.exception(
            'Product image analysis persistence or processing failed. analysis_id=%s error=%s',
            analysis.id if analysis else None,
            exc,
        )
        return product_image_analysis_error_response(
            analysis,
            code='IMAGE_ANALYSIS_SAVE_FAILED',
            message=IMAGE_ANALYSIS_SAVE_FAILED_MESSAGE,
            detail=str(exc),
            exc=exc,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as exc:
        logger.exception(
            'Unexpected product image analysis failure. analysis_id=%s error=%s',
            analysis.id if analysis else None,
            exc,
        )
        return product_image_analysis_error_response(
            analysis,
            code='IMAGE_ANALYSIS_FAILED',
            message=IMAGE_ANALYSIS_FAILED_MESSAGE,
            detail=str(exc),
            exc=exc,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def product_image_analysis_list(request):
    queryset = ProductImageAnalysis.objects.filter(user=request.user).prefetch_related('options')
    return list_response(request, queryset, ProductImageAnalysisSummarySerializer, context={'request': request})


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def product_image_analysis_detail(request, analysis_id):
    analysis = get_object_or_404(
        ProductImageAnalysis.objects.filter(user=request.user).prefetch_related('options'),
        pk=analysis_id,
    )
    if request.method == 'GET':
        return Response(build_product_image_analysis_payload(analysis), status=status.HTTP_200_OK)
    if request.method == 'DELETE':
        analysis.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProductImageAnalysisUpdateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    try:
        payload = update_analysis_from_review(analysis, serializer.validated_data)
    except ValidationError as exc:
        return Response(
            {
                'success': False,
                'code': 'INVALID_REVIEW_UPDATE',
                'detail': exc.message if hasattr(exc, 'message') else exc.messages[0],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def product_image_analysis_confirm(request, analysis_id):
    analysis = get_object_or_404(
        ProductImageAnalysis.objects.filter(user=request.user).prefetch_related('options'),
        pk=analysis_id,
    )
    payload = confirm_analysis(analysis)
    return Response(payload, status=status.HTTP_200_OK)
