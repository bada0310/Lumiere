from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('liked-options', views.LikedProductOptionViewSet, basename='liked-option')
router.register('url-analyses', views.UrlAnalysisRecordViewSet, basename='url-analysis')

urlpatterns = [
    path('', include(router.urls)),
]
