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
    ProductColorAnalysisRequestSerializer,
    ProductImageAnalysisRequestSerializer,
    ProductImageAnalysisSummarySerializer,
    ProductImageAnalysisUpdateSerializer,
    ProductScrapeRequestSerializer,
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
from products.services.url_color_analysis import ProductColorAnalysisError, analyze_product_color_url


logger = logging.getLogger(__name__)
IMAGE_ANALYSIS_SAVE_FAILED_MESSAGE = 'The uploaded image could not be saved for analysis.'
IMAGE_ANALYSIS_FAILED_MESSAGE = 'Product image analysis failed unexpectedly.'
SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE = '상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.'
SHORT_URL_RESOLVE_ERROR_MESSAGE = '단축 링크를 분석하지 못했습니다. 올리브영 상품 상세 페이지의 전체 URL을 입력해주세요.'


def safe_product_analysis_error_message(code):
    if code == 'SHORT_URL_RESOLVE_FAILED':
        return SHORT_URL_RESOLVE_ERROR_MESSAGE
    return SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE


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
        Product.objects.filter(canonical_key__isnull=False)
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
            return 0
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


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def product_color_analysis(request):
    serializer = ProductColorAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'success': False,
                'message': SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
                'detail': SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
                'code': 'invalid_url',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = analyze_product_color_url(
            serializer.validated_data['product_url'],
            user=request.user,
        )
    except ProductColorAnalysisError as exc:
        logger.exception('Product color analysis failed with handled error code=%s', exc.code)
        message = safe_product_analysis_error_message(exc.code)
        return Response(
            {
                'success': False,
                'message': message,
                'detail': message,
                'code': exc.code,
            },
            status=exc.status_code,
        )
    except Exception as exc:
        logger.exception('Unexpected product color analysis failure: %s', exc)
        return Response(
            {
                'success': False,
                'message': SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
                'detail': SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE,
                'code': 'PRODUCT_URL_ANALYSIS_FAILED',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def product_scrape(request):
    serializer = ProductScrapeRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'status': 'fail',
                'message': 'The URL is unsupported or temporarily inaccessible.',
                'code': 'INVALID_URL',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from products.services.scraping import ScrapingError, scrape_product_url

        scraped = scrape_product_url(serializer.validated_data['product_url'])
    except ScrapingError as exc:
        logger.exception('Product scrape failed with handled error code=%s', exc.code)
        return Response(
            {
                'status': 'fail',
                'message': 'The URL is unsupported or temporarily inaccessible.',
                'code': exc.code,
            },
            status=exc.status_code,
        )
    except Exception as exc:
        logger.exception('Unexpected product scrape failure: %s', exc)
        return Response(
            {
                'status': 'fail',
                'message': 'The URL is unsupported or temporarily inaccessible.',
                'code': 'SCRAPE_FAILED',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(scraped.public_payload(), status=status.HTTP_200_OK)

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
