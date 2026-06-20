from django.db.models import Avg, Count, Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Review
from .serializers import ProductSerializer, ReviewSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.annotate(
            review_count=Count('reviews', distinct=True),
            average_rating=Avg('reviews__rating'),
        )
        category = self.request.query_params.get('category')
        keyword = self.request.query_params.get('q')

        if category:
            queryset = queryset.filter(category=category)
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) | Q(brand__icontains=keyword)
            )
        return queryset


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
    queryset = Product.objects.annotate(
        review_count=Count('reviews', distinct=True),
        average_rating=Avg('reviews__rating'),
    )

    if not queryset.exists():
        products = [
            {
                "id": 1,
                "brand": "롬앤",
                "name": "쥬시 래스팅 틴트",
                "category": "립틴트",
                "match_score": 92,
                "image": "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0018/A00000018056701ko.jpg"
            },
            {
                "id": 2,
                "brand": "페리페라",
                "name": "잉크 무드 글로이 틴트",
                "category": "립틴트",
                "match_score": 88,
                "image": "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0019/A00000019723101ko.jpg"
            },
        ]
        return Response(products)

    serializer = ProductSerializer(queryset, many=True)
    return Response(serializer.data)
