from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Product(models.Model):
    class Category(models.TextChoices):
        LIP = 'LIP', '립'
        EYE = 'EYE', '아이'
        CHEEK = 'CHEEK', '치크'
        BASE = 'BASE', '베이스'
        LENS = 'LENS', '렌즈'
        ETC = 'ETC', '기타'

    class ToneTag(models.TextChoices):
        SPRING_LIGHT = 'SPRING_LIGHT', '봄 웜 라이트'
        SPRING_BRIGHT = 'SPRING_BRIGHT', '봄 웜 브라이트'
        SUMMER_LIGHT = 'SUMMER_LIGHT', '여름 쿨 라이트'
        SUMMER_MUTE = 'SUMMER_MUTE', '여름 쿨 뮤트'
        AUTUMN_MUTE = 'AUTUMN_MUTE', '가을 웜 뮤트'
        AUTUMN_DEEP = 'AUTUMN_DEEP', '가을 웜 딥'
        WINTER_BRIGHT = 'WINTER_BRIGHT', '겨울 쿨 브라이트'
        WINTER_DEEP = 'WINTER_DEEP', '겨울 쿨 딥'
        UNKNOWN = 'UNKNOWN', '미분류'

    class Finish(models.TextChoices):
        MATTE = 'MATTE', '매트'
        GLOSSY = 'GLOSSY', '글로시'
        VELVET = 'VELVET', '벨벳'
        SHIMMER = 'SHIMMER', '쉬머'
        NATURAL = 'NATURAL', '내추럴'
        UNKNOWN = 'UNKNOWN', '미분류'

    class ColorFamily(models.TextChoices):
        PINK = 'PINK', '핑크'
        ROSE = 'ROSE', '로즈'
        CORAL = 'CORAL', '코랄'
        RED = 'RED', '레드'
        BERRY = 'BERRY', '베리'
        LAVENDER = 'LAVENDER', '라벤더'
        BEIGE = 'BEIGE', '베이지'
        BROWN = 'BROWN', '브라운'
        GRAY = 'GRAY', '그레이'
        IVORY = 'IVORY', '아이보리'
        ETC = 'ETC', '기타'

    # 기본 상품 정보
    brand = models.CharField(max_length=80)
    name = models.CharField(max_length=300)
    canonical_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ETC,
    )

    image_url = models.URLField(max_length=1000, blank=True)
    representative_image_url = models.URLField(max_length=1000, blank=True)
    product_url = models.URLField(max_length=1000, blank=True)
    description = models.TextField(blank=True)

    # 네이버 쇼핑 API 원본 정보
    price = models.PositiveIntegerField(default=0)
    mall_name = models.CharField(max_length=100, blank=True)
    naver_product_id = models.CharField(max_length=100, blank=True)
    source_query = models.CharField(max_length=200, blank=True)

    naver_category1 = models.CharField(max_length=100, blank=True)
    naver_category2 = models.CharField(max_length=100, blank=True)
    naver_category3 = models.CharField(max_length=100, blank=True)
    naver_category4 = models.CharField(max_length=100, blank=True)

    # 추천/필터용 태그 정보
    texture = models.CharField(
        max_length=100,
        blank=True,
        help_text='예: 립틴트, 립글로스, 아이팔레트, 쿠션, 블러셔, 컬러렌즈',
    )

    finish = models.CharField(
        max_length=20,
        choices=Finish.choices,
        default=Finish.UNKNOWN,
    )

    tone_tag = models.CharField(
        max_length=30,
        choices=ToneTag.choices,
        default=ToneTag.UNKNOWN,
    )

    color_family = models.CharField(
        max_length=20,
        choices=ColorFamily.choices,
        default=ColorFamily.ETC,
    )

    # 상품 이미지/색상 분석 결과
    hex_code = models.CharField(max_length=20, blank=True)

    rgb_r = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )
    rgb_g = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )
    rgb_b = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )

    brightness = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='명도: 밝을수록 높음',
    )
    saturation = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='채도: 선명할수록 높음',
    )
    coolness = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='쿨톤 점수',
    )
    warmth = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='웜톤 점수',
    )
    depth = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='딥한 정도: 어두울수록 높음',
    )
    softness = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='탁도/부드러움: 회색기나 부드러움이 클수록 높음',
    )
    contrast = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='대비감',
    )

    # 추천 결과
    match_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['canonical_key'],
                condition=Q(canonical_key__isnull=False),
                name='unique_product_canonical_key',
            )
        ]

    def __str__(self):
        return f'{self.brand} {self.name}'

    @property
    def display_image_url(self):
        return self.representative_image_url or self.image_url


class ProductOption(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='options',
    )
    option_no = models.CharField(max_length=40, blank=True)
    option_name = models.CharField(max_length=200, blank=True)
    option_key = models.CharField(max_length=220)
    image_url = models.URLField(max_length=1000, blank=True)
    color_family = models.CharField(
        max_length=20,
        choices=Product.ColorFamily.choices,
        default=Product.ColorFamily.ETC,
    )
    analyzed_tone_tag = models.CharField(max_length=80, blank=True, db_index=True)
    hex_code = models.CharField(max_length=20, blank=True)
    rgb_r = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )
    rgb_g = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )
    rgb_b = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(255)],
    )
    brightness = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    saturation = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    coolness = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    warmth = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    depth = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    softness = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    contrast = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product', 'option_no', 'option_name']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'option_key'],
                name='unique_product_option_key',
            )
        ]

    def __str__(self):
        label = ' '.join(part for part in [self.option_no, self.option_name] if part)
        return f'{self.product} {label or self.option_key}'


class ProductOffer(models.Model):
    option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='offers',
    )
    mall_name = models.CharField(max_length=100, blank=True)
    price = models.PositiveIntegerField(default=0)
    product_url = models.URLField(max_length=1000, blank=True)
    naver_product_id = models.CharField(max_length=100, blank=True)
    is_representative = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price', 'id']

    def __str__(self):
        return f'{self.option} {self.mall_name} {self.price}'


class ProductOptionToneScore(models.Model):
    class Grade(models.TextChoices):
        BEST = 'BEST', 'BEST'
        GOOD = 'GOOD', 'GOOD'
        OK = 'OK', 'OK'
        CAUTION = 'CAUTION', 'CAUTION'

    option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='tone_scores',
    )
    target_tone = models.CharField(max_length=80, db_index=True)
    match_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    grade = models.CharField(max_length=20, choices=Grade.choices, default=Grade.CAUTION)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-match_score', 'option_id']
        constraints = [
            models.UniqueConstraint(
                fields=['option', 'target_tone'],
                name='unique_option_target_tone_score',
            )
        ]

    def __str__(self):
        return f'{self.option_id} {self.target_tone} {self.match_score}'


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    content = models.TextField()
    image_url = models.URLField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'author'],
                name='unique_review_per_product_author',
            )
        ]

    def __str__(self):
        return f'{self.product} - {self.rating}'


class ProductImageAnalysis(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_image_analyses',
    )
    product_name = models.CharField(max_length=300, blank=True)
    brand_name = models.CharField(max_length=120, blank=True)
    category = models.CharField(
        max_length=20,
        choices=Product.Category.choices,
        default=Product.Category.ETC,
    )
    uploaded_image = models.ImageField(upload_to='products/color-analysis/')
    raw_ai_response = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.product_name or self.brand_name or f'Image analysis {self.id}'


class ProductImageAnalysisOption(models.Model):
    class ColorSource(models.TextChoices):
        IMAGE_EXTRACTED = 'IMAGE_EXTRACTED', 'Image extracted'
        AI_ESTIMATED = 'AI_ESTIMATED', 'AI estimated'
        USER_EDITED = 'USER_EDITED', 'User edited'
        PENDING = 'PENDING', 'Pending'

    class Grade(models.TextChoices):
        BEST = 'BEST', 'BEST'
        GOOD = 'GOOD', 'GOOD'
        CAUTION = 'CAUTION', 'CAUTION'
        PENDING = 'PENDING', 'PENDING'

    analysis = models.ForeignKey(
        ProductImageAnalysis,
        on_delete=models.CASCADE,
        related_name='options',
    )
    option_name = models.CharField(max_length=200, blank=True)
    display_name = models.CharField(max_length=200, blank=True)
    hex_code = models.CharField(max_length=20, blank=True)
    color_source = models.CharField(
        max_length=20,
        choices=ColorSource.choices,
        default=ColorSource.PENDING,
    )
    confidence = models.FloatField(null=True, blank=True)
    chart_x = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    chart_y = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    brightness = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    saturation = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    warmth = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    coolness = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    depth = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    softness = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    contrast = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    match_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    grade = models.CharField(max_length=20, choices=Grade.choices, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.display_name or self.option_name or f'Analysis option {self.id}'
