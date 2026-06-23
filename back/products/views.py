import logging

from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from diagnosis.domain.tone_profiles import build_tone_result_payload
from diagnosis.services.primary import get_primary_diagnosis_for_user
from products.models import Product, ProductOffer, ProductOption, ProductOptionToneScore, Review
from products.serializers import (
    ProductColorAnalysisRequestSerializer,
    ProductScrapeRequestSerializer,
    ProductSerializer,
    ReviewSerializer,
)
from products.services.catalog_color_analysis import build_product_color_analysis_payload
from products.services.recommendation import build_user_tone_profile, calculate_option_match
from products.services.url_color_analysis import ProductColorAnalysisError, analyze_product_color_url


logger = logging.getLogger(__name__)
SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE = '상품 정보를 가져올 수 없습니다. URL을 다시 확인해주세요.'
SHORT_URL_RESOLVE_ERROR_MESSAGE = '단축 링크를 분석하지 못했습니다. 올리브영 상품 상세 페이지의 전체 URL을 입력해주세요.'


def safe_product_analysis_error_message(code):
    if code == 'SHORT_URL_RESOLVE_FAILED':
        return SHORT_URL_RESOLVE_ERROR_MESSAGE
    return SAFE_PRODUCT_ANALYSIS_ERROR_MESSAGE


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
        return Response(
            {
                'success': False,
                'message': '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
                'detail': '제품 링크를 확인할 수 없습니다. URL을 다시 확인해주세요.',
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
        return Response(
            {
                'success': False,
                'message': '상품 URL 분석 중 오류가 발생했습니다.',
                'detail': '상품 URL 분석 중 오류가 발생했습니다.',
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
