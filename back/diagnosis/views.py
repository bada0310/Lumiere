from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import DiagnosisResult
from .serializers import DiagnosisResultSerializer


class DiagnosisResultListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            DiagnosisResult.objects.filter(user=self.request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(
                'representative_colors',
                'makeover_styles',
                'color_palettes',
                'recommended_products',
                'recommended_lenses',
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DiagnosisResultDetailView(generics.RetrieveAPIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            DiagnosisResult.objects.filter(user=self.request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(
                'representative_colors',
                'makeover_styles',
                'color_palettes',
                'recommended_products',
                'recommended_lenses',
            )
        )


class LatestDiagnosisResultView(generics.GenericAPIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        result = (
            DiagnosisResult.objects.filter(user=request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(
                'representative_colors',
                'makeover_styles',
                'color_palettes',
                'recommended_products',
                'recommended_lenses',
            )
            .first()
        )
        if not result:
            return Response(None)
        return Response(self.get_serializer(result).data)


class DemoDiagnosisResultView(generics.GenericAPIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        result = (
            DiagnosisResult.objects.filter(is_demo=True)
            .select_related('user', 'personal_color')
            .prefetch_related(
                'representative_colors',
                'makeover_styles',
                'color_palettes',
                'recommended_products',
                'recommended_lenses',
            )
            .first()
        )
        if not result:
            return Response(
                {'detail': 'Demo diagnosis result does not exist. Run python manage.py seed_demo_diagnosis.'},
                status=404,
            )
        return Response(self.get_serializer(result).data)
