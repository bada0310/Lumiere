from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
# 1. 퍼스널 컬러 기준 정보 (Master Data)
class PersonalColor(models.Model):
    # e.g) 여름 쿨 뮤트 와 같은 타입 풀네임  
    type_name = models.CharField(max_length=50, unique=True) # 예: 여름 쿨 (뮤트)

    # 0 = 완전 웜톤, 100 = 완전 쿨톤 
    tone_key = models.CharField(max_length=80, unique=True, null=True, blank=True, db_index=True)

    class BaseTemperature(models.TextChoices):
        warm = 'warm', '웜(warm)'
        cool = 'cool', '쿨(cool)'
    base_temperature = models.CharField(max_length=5, choices=BaseTemperature.choices)

    # 봄 여름 가을 겨울 
    class SeasonChoice(models.TextChoices):
        spring = 'spring', '봄(spring)'
        summer = 'summer', '여름(summer)'
        fall = 'fall', '가을(fall)'
        winter = 'winter', '겨울(winter)'
    season =  models.CharField(max_length=10, choices=SeasonChoice.choices)

    # 브라이트  뮤트 딥
    class ToneChoices(models.TextChoices):
        BRIGHT = 'BRIGHT', '브라이트(Bright)'
        LIGHT = 'LIGHT', '라이트(Light)'
        MUTE = 'MUTE', '뮤트(Mute)'
        DEEP = 'DEEP', '딥(Deep)'
    tone = models.CharField(max_length=10, choices=ToneChoices.choices)
    
    # 짧은 설명 
    description = models.TextField(help_text="퍼스널컬러에 대한 짧은 설명")
    
    # 2. UI 슬라이더 / 프로그레스 바용 수치 필드
    # ==========================================
    # validators를 사용하여 0~100 사이의 값만 들어가도록 강제 (안정성 확보)
    
    # 0 = 완전 웜톤, 100 = 완전 쿨톤
    temperature_degree = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="온도감 (0:Warm ~ 100:Cool)"
    )
    
    # 0 = 완전 저명도, 100 = 완전 고명도
    brightness_degree = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="명도 (0:Low ~ 100:High)"
    )
    
    # 0 = 완전 저채도, 100 = 완전 고채도
    saturation_degree = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="채도 (0:Low ~ 100:High)"
    )
    # 투명도 0=clear  100=muted
    turbidity_degree = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="쳥량함(0) 탁함(0)"
    )
    # 광택감 0=glossy watery  100 =matt
    glossiness_degree = models.IntegerField(
        validators=[MinValueValidator(0),MaxValueValidator(100)],
    )
    #명도랑 채도만으로 대비감을 표현하다 
    # 대비 
    contrast_degree = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="대비감 (0:Low Contrast ~ 100:High Contrast)"
    )
    #PCCS
    # 베스트 PCCS 톤 (예: ['sf', 'ltg'])
    best_pccs = models.JSONField(default=list, help_text="베스트 PCCS 톤 코드 목록")
    
    # 세컨드/서브 PCCS 톤 (예: ['g', 'd'])
    sub_pccs = models.JSONField(default=list, blank=True, help_text="서브 PCCS 톤 코드 목록")

    def __str__(self):
        return self.type_name

# 진단 결과의 기준 상품&사용자를 있는 매개체 -> 하나의 퍼컬에는 여러개의 상품 option

# makeup 부위에 따라 추천하는 색감
# 립 컬러 /베이스 컬러(블러서 ,셰딩,파운데이션) / 아이 메이크업 컬러(세도우, 아이라이너, 아이브로우,마스카라,)애교살 색상,뒷트임 라이너 )  

# 퍼스널 컬러별 메이크업 부위 색상 추천을 담당하는 모델
class ColorRecommendation(models.Model):
    
    personal_color = models.ForeignKey(
        PersonalColor,
        on_delete=models.CASCADE,
        related_name='color_recommendation'
    )
    
    # 추천 타입(best,worst, Representative)
    class RecoType(models.TextChoices):
        REP = 'REP', '대표 컬러(Representative)'
        BEST = 'BEST', '베스트 컬러(best)'
        WORST = 'WORST', '워스트 컬러(Worst)'
    
    # 실제 데이터를 담는 '주문서' (DB 컬럼)
    recommendation_type = models.CharField(max_length=10, choices=RecoType.choices)

    class MakeupPart(models.TextChoices):
        LIP = 'LIP', '립(Lip)'
        BASE = 'BASE', '베이스(파운데이션, 블러셔, 쉐딩)'
        EYE = 'EYE', '아이(섀도우, 라이너, 마스카라 등)'
    
    makeup_part = models.CharField(max_length=10, choices=MakeupPart.choices)
    
    # 실제 색상 데이터 (AI 이미지 추출 결과와 매핑하기 좋도록 Hex 코드 포함)
    color_name = models.CharField(max_length=50, help_text="색상명 (예: 페일 핑크, 체리 레드)")
    color_hex = models.CharField(max_length=7, help_text="색상 Hex Code (예: #FFC0CB)")
    
    # 추가 설명 (선택 사항)
    description = models.CharField(max_length=200, blank=True, help_text="예: 애교살 포인트용으로 추천")
    
    def __str__(self):
        return f'[{self.personal_color.type_name}]{self.get_makeup_part_display()}-{self.color_name}({self.recommendation_type}) '


class DiagnosisResult(models.Model):
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        LOW_CONFIDENCE = 'low_confidence', 'Low confidence'
        FAILED = 'failed', 'Failed'

    class PaletteStatus(models.TextChoices):
        READY = 'ready', 'Ready'
        PREPARING = 'preparing', 'Preparing'
        MISSING = 'missing', 'Missing'

    class MakeupGenerationStatus(models.TextChoices):
        NONE = 'none', 'None'
        QUEUED = 'queued', 'Queued'
        RUNNING = 'running', 'Running'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Skipped'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diagnosis_results',
    )
    personal_color = models.ForeignKey(
        PersonalColor,
        on_delete=models.PROTECT,
        related_name='diagnosis_results',
    )
    confidence_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.COMPLETED)
    tone_key = models.CharField(max_length=80, blank=True, db_index=True)
    personal_color_code = models.CharField(max_length=80, blank=True)
    korean_name = models.CharField(max_length=80, blank=True)
    english_name = models.CharField(max_length=80, blank=True)
    summary = models.TextField(blank=True)
    diagnosis_json = models.JSONField(default=dict, blank=True)
    palette_snapshot = models.JSONField(default=dict, blank=True)
    palette_status = models.CharField(max_length=30, choices=PaletteStatus.choices, default=PaletteStatus.READY)
    keywords = models.JSONField(default=list, blank=True)
    image_features = models.JSONField(default=list, blank=True)
    skin_metrics = models.JSONField(default=dict, blank=True)
    radar_chart = models.JSONField(default=dict, blank=True)
    style_guide = models.JSONField(default=dict, blank=True)
    is_demo = models.BooleanField(default=False)
    diagnosed_at = models.DateField(null=True, blank=True)
    uploaded_image = models.ImageField(
        upload_to='diagnosis/originals/',
        null=True,
        blank=True,
    )
    processed_image = models.ImageField(
        upload_to='diagnosis/processed/',
        null=True,
        blank=True,
    )
    generated_makeup_image = models.ImageField(
        upload_to='diagnosis/generated/',
        null=True,
        blank=True,
    )
    makeup_generation_status = models.CharField(
        max_length=30,
        choices=MakeupGenerationStatus.choices,
        default=MakeupGenerationStatus.NONE,
    )
    makeup_generation_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        for field_name in ['skin_metrics', 'radar_chart']:
            values = getattr(self, field_name) or {}
            for key, value in values.items():
                if not isinstance(value, int) or value < 0 or value > 100:
                    raise ValidationError({field_name: f'{key} must be an integer between 0 and 100.'})

    def __str__(self):
        return f'{self.user} - {self.personal_color} ({self.confidence_score}%)'


class DiagnosisRepresentativeColor(models.Model):
    diagnosis = models.ForeignKey(
        DiagnosisResult,
        on_delete=models.CASCADE,
        related_name='representative_colors',
    )
    name = models.CharField(max_length=80)
    hex = models.CharField(max_length=7)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['diagnosis', 'order'], name='unique_representative_color_order'),
        ]

    def __str__(self):
        return f'{self.diagnosis_id} {self.name}'


class DiagnosisColorPalette(models.Model):
    class Group(models.TextChoices):
        BEST = 'best', 'Best'
        NEUTRAL = 'neutral', 'Neutral'
        ACCENT = 'accent', 'Accent'
        TRY = 'try', 'Try'
        WORST = 'worst', 'Worst'

    diagnosis = models.ForeignKey(
        DiagnosisResult,
        on_delete=models.CASCADE,
        related_name='color_palettes',
    )
    group = models.CharField(max_length=20, choices=Group.choices)
    name = models.CharField(max_length=80)
    hex = models.CharField(max_length=7)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['group', 'order']
        constraints = [
            models.UniqueConstraint(fields=['diagnosis', 'group', 'order'], name='unique_palette_group_order'),
        ]

    def __str__(self):
        return f'{self.diagnosis_id} {self.group} {self.name}'


class DiagnosisMakeoverStyle(models.Model):
    class Status(models.TextChoices):
        NONE = 'none', 'None'
        QUEUED = 'queued', 'Queued'
        RUNNING = 'running', 'Running'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Skipped'

    diagnosis = models.ForeignKey(
        DiagnosisResult,
        on_delete=models.CASCADE,
        related_name='makeover_styles',
    )
    key = models.CharField(max_length=40)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NONE, db_index=True)
    error_message = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['diagnosis', 'key'], name='unique_makeover_style_key'),
        ]

    def __str__(self):
        return f'{self.diagnosis_id} {self.name}'


class DiagnosisRecommendedProduct(models.Model):
    diagnosis = models.ForeignKey(
        DiagnosisResult,
        on_delete=models.CASCADE,
        related_name='recommended_products',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diagnosis_recommendations',
    )
    category = models.CharField(max_length=40)
    category_name = models.CharField(max_length=80)
    tone_label = models.CharField(max_length=120)
    brand = models.CharField(max_length=80)
    product_name = models.CharField(max_length=120)
    shade = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=240, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    product_url = models.URLField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['diagnosis', 'category'], name='unique_recommended_product_category'),
        ]

    def __str__(self):
        return f'{self.category_name} {self.brand} {self.product_name}'


class DiagnosisRecommendedLens(models.Model):
    diagnosis = models.ForeignKey(
        DiagnosisResult,
        on_delete=models.CASCADE,
        related_name='recommended_lenses',
    )
    rank = models.CharField(max_length=20)
    brand = models.CharField(max_length=80)
    product_name = models.CharField(max_length=120)
    color = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['diagnosis', 'order'], name='unique_recommended_lens_order'),
        ]

    def __str__(self):
        return f'{self.rank} {self.brand} {self.product_name}'


class PersonalColorPalette(models.Model):
    tone_key = models.CharField(max_length=80, unique=True, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    tone_name = models.CharField(max_length=80)
    season = models.CharField(max_length=20)
    temperature = models.CharField(max_length=20)
    brightness = models.CharField(max_length=40)
    chroma = models.CharField(max_length=40)
    contrast = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    best_colors = models.JSONField(default=list, blank=True)
    worst_colors = models.JSONField(default=list, blank=True)
    makeup_palette = models.JSONField(default=dict, blank=True)
    base_makeup_guide = models.TextField(blank=True)
    lip_guide = models.TextField(blank=True)
    cheek_guide = models.TextField(blank=True)
    eye_guide = models.TextField(blank=True)
    styling_keywords = models.JSONField(default=list, blank=True)
    recommended_product_tone_range = models.JSONField(default=dict, blank=True)
    is_placeholder = models.BooleanField(default=False)
    personal_color = models.OneToOneField(
        PersonalColor,
        on_delete=models.SET_NULL,
        related_name='fixed_palette',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tone_key']

    def __str__(self):
        return f'{self.tone_key} palette'


class MakeupGenerationJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        RUNNING = 'running', 'Running'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'

    diagnosis = models.ForeignKey(
        DiagnosisResult,
        on_delete=models.CASCADE,
        related_name='makeup_generation_jobs',
    )
    style_key = models.CharField(max_length=40, blank=True, db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.QUEUED, db_index=True)
    prompt = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'makeup job {self.pk} for diagnosis {self.diagnosis_id}'
