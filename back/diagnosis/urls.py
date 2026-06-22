from django.urls import path

from . import views

urlpatterns = [
    path('analyze/', views.DiagnosisAnalyzeView.as_view(), name='diagnosis-analyze'),
    path('demo/', views.DemoDiagnosisResultView.as_view(), name='diagnosis-demo'),
    path('latest/', views.LatestDiagnosisResultView.as_view(), name='diagnosis-latest'),
    path('results/', views.DiagnosisResultListCreateView.as_view(), name='diagnosis-results'),
    path('results/<int:pk>/', views.DiagnosisResultDetailView.as_view(), name='diagnosis-result-detail'),
]
