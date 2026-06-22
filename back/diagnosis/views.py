from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, parsers, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from diagnosis.ai_clients.openai_compatible import AIClientConfigurationError, AIClientResponseError
from diagnosis.domain.tone_keys import build_tone_name
from diagnosis.services.ai_diagnosis import diagnose_personal_color
from diagnosis.services.makeup_generation import (
    enqueue_makeover_generation,
    get_makeover_payload,
    retry_makeover_style_generation,
)
from diagnosis.services.palettes import apply_palette_snapshot_to_diagnosis, serialize_palette
from diagnosis.services.workflow import get_or_create_personal_color

from .models import DiagnosisResult, PersonalColorPalette
from .serializers import DiagnosisResultSerializer


DIAGNOSIS_PREFETCH = (
    'representative_colors',
    'makeover_styles',
    'color_palettes',
    'recommended_products',
    'recommended_lenses',
)


class DiagnosisAnalyzeView(APIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        uploaded_image = request.FILES.get('image')
        if not uploaded_image:
            return Response(
                {'code': 'image_required', 'detail': 'image 파일을 업로드해 주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = create_ai_diagnosis_result(request.user, uploaded_image)
        except AIClientConfigurationError as exc:
            return Response(
                {'code': 'ai_not_configured', 'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except AIClientResponseError as exc:
            return Response(
                {'code': 'invalid_ai_response', 'detail': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValidationError as exc:
            return Response(
                {'code': 'invalid_diagnosis', 'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PaletteMissingError as exc:
            return Response(
                {'code': 'palette_missing', 'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = self._with_related(result.pk)
        return Response(DiagnosisResultSerializer(result, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def _with_related(self, pk):
        return (
            DiagnosisResult.objects.select_related('user', 'personal_color')
            .prefetch_related(*DIAGNOSIS_PREFETCH)
            .get(pk=pk)
        )


class PaletteMissingError(ValueError):
    pass


def create_ai_diagnosis_result(user, uploaded_image):
    diagnosis_json = diagnose_personal_color(uploaded_image)
    tone_key = diagnosis_json['tone_key']
    palette = (
        PersonalColorPalette.objects.select_related('personal_color')
        .filter(tone_key=tone_key, is_placeholder=False)
        .first()
    )
    if not palette:
        raise PaletteMissingError('해당 tone_key에 대한 팔레트가 없습니다.')

    palette_data = deepcopy(palette.data) if palette.data else serialize_palette(palette)
    personal_color = palette.personal_color or get_or_create_personal_color(tone_key, _workflow_payload(diagnosis_json), palette_data)

    with transaction.atomic():
        diagnosis = DiagnosisResult(
            user=user,
            personal_color=personal_color,
            status=DiagnosisResult.Status.COMPLETED,
            tone_key=tone_key,
            personal_color_code=tone_key,
            korean_name=palette_data.get('toneName') or palette.tone_name or build_tone_name(tone_key),
            english_name=_english_name(tone_key),
            confidence_score=diagnosis_json['confidence'],
            diagnosed_at=timezone.localdate(),
            summary=diagnosis_json.get('summary', ''),
            diagnosis_json=diagnosis_json,
            palette_snapshot=palette_data,
            palette_status=DiagnosisResult.PaletteStatus.READY,
            keywords=palette_data.get('keywords') or [],
            image_features=_image_features(diagnosis_json.get('features') or {}),
            skin_metrics=_skin_metrics(diagnosis_json.get('features') or {}),
            radar_chart=_radar_chart(diagnosis_json.get('features') or {}),
            style_guide=_style_guide(palette_data),
            makeup_generation_status=DiagnosisResult.MakeupGenerationStatus.NONE,
        )
        if hasattr(uploaded_image, 'seek'):
            uploaded_image.seek(0)
        diagnosis.uploaded_image = uploaded_image
        diagnosis.full_clean()
        diagnosis.save()
        apply_palette_snapshot_to_diagnosis(diagnosis, palette_data)

    return diagnosis


def _workflow_payload(diagnosis_json):
    features = diagnosis_json.get('features') or {}
    return {
        'toneKey': diagnosis_json['tone_key'],
        'confidence': diagnosis_json['confidence'] / 100,
        'summary': diagnosis_json.get('summary', ''),
        'analysis': features,
    }


def _image_features(features):
    return [
        {
            'key': key,
            'title': title,
            'description': str(features.get(key, '')),
            'icon': icon,
        }
        for key, title, icon in [
            ('temperature', '온도감', 'sparkle'),
            ('brightness', '명도', 'cloud'),
            ('chroma', '채도', 'diamond'),
            ('contrast', '대비감', 'circle'),
        ]
    ]


def _skin_metrics(features):
    brightness = _degree(features.get('brightness'))
    chroma = _degree(features.get('chroma'))
    contrast = _degree(features.get('contrast'))
    temperature = _temperature_degree(features.get('temperature'))
    return {
        'brightness': brightness,
        'saturation': chroma,
        'clarity': max(0, min(100, 100 - chroma + 20)),
        'contrast': contrast,
        'cool_warm': temperature,
        'softness': max(0, min(100, 100 - contrast + 10)),
        'gloss': 50,
    }


def _radar_chart(features):
    metrics = _skin_metrics(features)
    return {
        'brightness': metrics['brightness'],
        'saturation': metrics['saturation'],
        'clarity': metrics['clarity'],
        'contrast': metrics['contrast'],
        'softness': metrics['softness'],
        'coolness': metrics['cool_warm'],
    }


def _style_guide(palette_data):
    if palette_data.get('styleGuide'):
        return {
            **palette_data['styleGuide'],
            'styling_keywords': palette_data.get('stylingKeywords') or palette_data.get('keywords') or [],
            'recommended_product_tone_range': palette_data.get('recommendedProductToneRange') or {},
        }

    return {
        'styling_keywords': palette_data.get('stylingKeywords') or palette_data.get('keywords') or [],
        'recommended_product_tone_range': palette_data.get('recommendedProductToneRange') or {},
        'fashion': [
            {
                'name': item.get('nameKo') or item.get('name'),
                'hex': item.get('hex'),
                'description': item.get('description') or item.get('reason') or '',
            }
            for item in palette_data.get('bestColors') or palette_data.get('palettes', {}).get('best', [])
        ],
    }


def _degree(value):
    return {
        'low': 25,
        'low_to_medium': 38,
        'medium_low': 40,
        'medium': 55,
        'medium_high': 70,
        'high': 85,
    }.get(value, 50)


def _temperature_degree(value):
    return {
        'warm': 20,
        'neutral': 50,
        'cool': 82,
    }.get(value, 50)


def _english_name(tone_key):
    return ' '.join(part.title() for part in tone_key.split('_'))


class DiagnosisResultListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            DiagnosisResult.objects.filter(user=self.request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(*DIAGNOSIS_PREFETCH)
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
            .prefetch_related(*DIAGNOSIS_PREFETCH)
        )


class DiagnosisMakeoverView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        diagnosis = self._get_diagnosis(request, pk)
        return Response(get_makeover_payload(diagnosis, request=request))

    def post(self, request, pk):
        diagnosis = self._get_diagnosis(request, pk)
        if diagnosis.status != DiagnosisResult.Status.COMPLETED:
            return Response(
                {'detail': '완료된 진단 결과에서만 AI 메이크오버를 생성할 수 있어요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if diagnosis.palette_status != DiagnosisResult.PaletteStatus.READY:
            return Response(
                {'detail': '고정 팔레트가 준비된 진단 결과에서만 AI 메이크오버를 생성할 수 있어요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not (diagnosis.processed_image or diagnosis.uploaded_image):
            return Response(
                {'detail': 'AI 메이크오버에 사용할 원본 이미지가 없어요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enqueue_makeover_generation(diagnosis)
        diagnosis = self._get_diagnosis(request, pk)
        return Response(get_makeover_payload(diagnosis, request=request), status=status.HTTP_202_ACCEPTED)

    def _get_diagnosis(self, request, pk):
        return get_object_or_404(
            DiagnosisResult.objects.filter(user=request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(*DIAGNOSIS_PREFETCH),
            pk=pk,
        )


class DiagnosisMakeoverRetryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, style_key):
        diagnosis = get_object_or_404(
            DiagnosisResult.objects.filter(user=request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(*DIAGNOSIS_PREFETCH),
            pk=pk,
        )
        try:
            retry_makeover_style_generation(diagnosis, style_key)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        diagnosis = get_object_or_404(
            DiagnosisResult.objects.filter(user=request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(*DIAGNOSIS_PREFETCH),
            pk=pk,
        )
        return Response(get_makeover_payload(diagnosis, request=request), status=status.HTTP_202_ACCEPTED)


class LatestDiagnosisResultView(generics.GenericAPIView):
    serializer_class = DiagnosisResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        result = (
            DiagnosisResult.objects.filter(user=request.user)
            .select_related('user', 'personal_color')
            .prefetch_related(*DIAGNOSIS_PREFETCH)
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
            .prefetch_related(*DIAGNOSIS_PREFETCH)
            .first()
        )
        if not result:
            return Response(
                {'detail': 'Demo diagnosis result does not exist. Run python manage.py seed_demo_diagnosis.'},
                status=404,
            )
        return Response(self.get_serializer(result).data)
