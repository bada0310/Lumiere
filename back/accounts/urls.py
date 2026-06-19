from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # --- Session 기반 엔드포인트 ---
    path('session-login/', views.session_login_view, name='session_login'),
    path('session-logout/', views.session_logout_view, name='session_logout'),

    # --- JWT 기반 엔드포인트 ---
    path('jwt-login/', TokenObtainPairView.as_view(), name='jwt_login'),
    path('jwt-refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    
    # --- 회원가입 ---
    path('signup/', views.signup_view, name='signup'), # 회원가입 
    path('user/', views.user_info_view, name='user_info'), # 내 정보 가져오기
    path('check-username/', views.check_username_view, name='check_username'), # 중복 확인 전용 주소 추가
]