from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='community-post')
router.register('comments', views.CommentViewSet, basename='community-comment')

urlpatterns = [
    path('', include(router.urls)),
]
