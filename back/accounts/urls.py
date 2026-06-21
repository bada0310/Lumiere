from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views


urlpatterns = [
    path('session-login/', views.SessionLoginView.as_view(), name='session_login'),
    path('session-logout/', views.SessionLogoutView.as_view(), name='session_logout'),
    path('jwt-login/', TokenObtainPairView.as_view(), name='jwt_login'),
    path('jwt-refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('user/', views.CurrentUserView.as_view(), name='user_info'),
    path('user/update/', views.CurrentUserUpdateView.as_view(), name='user_update'),
    path('check-username/', views.CheckUsernameView.as_view(), name='check_username'),
    path('check-nickname/', views.CheckNicknameView.as_view(), name='check_nickname'),
    path('find-password/', views.FindPasswordView.as_view(), name='find_password'),
]
