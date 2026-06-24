from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('items', views.ProductViewSet, basename='product')
router.register('reviews', views.ReviewViewSet, basename='review')

urlpatterns = [
    path('', views.product_list),
    path('scrape/', views.product_scrape, name='product-scrape'),
    path('analyze-image/', views.product_image_analysis, name='product-image-analysis'),
    path('image-analyses/', views.product_image_analysis_list, name='product-image-analysis-list'),
    path('image-analyses/<int:analysis_id>/', views.product_image_analysis_detail, name='product-image-analysis-detail'),
    path('image-analyses/<int:analysis_id>/confirm/', views.product_image_analysis_confirm, name='product-image-analysis-confirm'),
    path('color-analysis/', views.product_color_analysis, name='product-color-analysis'),
    path('<int:product_id>/color-analysis/', views.product_catalog_color_analysis, name='product-catalog-color-analysis'),
    path('<int:product_id>/', views.product_detail, name='product-detail'),
    path('', include(router.urls)),
]

# /products 앱으로 요청이 들어오면, views.py의 product_list 함수를 실행해라 
