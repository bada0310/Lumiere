from django.db import models
from django_conf import settings

# Create your models here.
# 진단 결과의 기준 상품&사용자를 있는 매개체 -> 하나의 퍼컬에는 여러개의 상품 option
class PerSonalColorAnalysis(models.Model):
    # e.g) 여름 쿨 뮤트 와 같은 타입 풀네임 
    type_name  = models.CharField(max_length=50 unique=True)

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
    description = models.TextField() 
   