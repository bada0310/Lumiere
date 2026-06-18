from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list),
]

# /products 앱으로 요청이 들어오면, views.py의 product_list 함수를 실행해라 