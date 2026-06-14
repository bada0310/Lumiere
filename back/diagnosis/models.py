from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
# 1. 퍼스널 컬러 기준 정보 (Master Data)
class PersonalColor(models.Model):
    # e.g) 여름 쿨 뮤트 와 같은 타입 풀네임  
    type_name = models.CharField(max_length=50, unique=True) # 예: 여름 쿨 (뮤트)

    # 0 = 완전 웜톤, 100 = 완전 쿨톤 
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
