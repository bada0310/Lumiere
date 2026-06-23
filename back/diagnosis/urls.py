from django.urls import path

from . import views

urlpatterns = [
    path('analyze/', views.DiagnosisAnalyzeView.as_view(), name='diagnosis-analyze'),
    path('demo/', views.DemoDiagnosisResultView.as_view(), name='diagnosis-demo'),
    path('latest/', views.LatestDiagnosisResultView.as_view(), name='diagnosis-latest'),
    path('results/', views.DiagnosisResultListCreateView.as_view(), name='diagnosis-results'),
    path('results/<int:pk>/makeovers/', views.DiagnosisMakeoverView.as_view(), name='diagnosis-makeovers'),
    path(
        'results/<int:pk>/makeovers/<str:style_key>/retry/',
        views.DiagnosisMakeoverRetryView.as_view(),
        name='diagnosis-makeover-retry',
    ),
    path('results/<int:result_id>/set-primary/', views.DiagnosisResultSetPrimaryView.as_view(), name='diagnosis-result-set-primary'),
    path('results/<int:result_id>/unset-primary/', views.DiagnosisResultUnsetPrimaryView.as_view(), name='diagnosis-result-unset-primary'),
    path('results/<int:result_id>/', views.DiagnosisResultDetailView.as_view(), name='diagnosis-result-detail'),
]
