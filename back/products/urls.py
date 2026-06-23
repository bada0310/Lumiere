from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('items', views.ProductViewSet, basename='product')
router.register('reviews', views.ReviewViewSet, basename='review')

urlpatterns = [
    path('', views.product_list),
    path('scrape/', views.product_scrape, name='product-scrape'),
    path('color-analysis/', views.product_color_analysis, name='product-color-analysis'),
    path('<int:product_id>/color-analysis/', views.product_catalog_color_analysis, name='product-catalog-color-analysis'),
    path('<int:product_id>/', views.product_detail, name='product-detail'),
    path('', include(router.urls)),
]

# /products 앱으로 요청이 들어오면, views.py의 product_list 함수를 실행해라 
