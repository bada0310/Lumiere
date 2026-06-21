from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from diagnosis.models import (
    DiagnosisColorPalette,
    DiagnosisMakeoverStyle,
    DiagnosisRecommendedLens,
    DiagnosisRecommendedProduct,
    DiagnosisRepresentativeColor,
    DiagnosisResult,
    PersonalColor,
)
from products.models import Product


class Command(BaseCommand):
    help = 'Seed an idempotent demo diagnosis result for frontend development.'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='test@lumiere.dev')
        parser.add_argument('--password', default='test1234!')
        parser.add_argument('--reset', action='store_true')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        reset = options['reset']

        with transaction.atomic():
            user = self.seed_user(email, password)

            if reset:
                deleted, _ = DiagnosisResult.objects.filter(user=user, is_demo=True).delete()
                self.stdout.write(self.style.WARNING(f'Reset demo diagnosis objects: {deleted}'))

            personal_color = self.seed_personal_color()
            diagnosis = self.seed_diagnosis(user, personal_color)

            counts = {
                'representative_colors': self.replace_representative_colors(diagnosis),
                'makeover_styles': self.replace_makeover_styles(diagnosis),
                'color_palettes': self.replace_color_palettes(diagnosis),
                'recommended_products': self.replace_recommended_products(diagnosis),
                'recommended_lenses': self.replace_recommended_lenses(diagnosis),
            }

        self.stdout.write(self.style.SUCCESS(f'Demo user: {user.email} ({user.pk})'))
        self.stdout.write(self.style.SUCCESS(f'Demo diagnosis: {diagnosis.pk}'))
        for key, value in counts.items():
            self.stdout.write(f'{key}: {value}')

    def media_path_or_none(self, relative_path):
        full_path = Path(settings.MEDIA_ROOT) / relative_path
        if full_path.exists():
            return relative_path.replace('\\', '/')
        self.stdout.write(self.style.WARNING(f'Missing media file, stored null: {relative_path}'))
        return None

    def seed_user(self, email, password):
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
            )
        else:
            if user.username != email and not User.objects.exclude(pk=user.pk).filter(username=email).exists():
                user.username = email
            user.set_password(password)

        user.nickname = f"Dev {email.split('@')[0]}"
        profile_image = self.media_path_or_none('demo/profiles/subina-profile.jpg')
        if profile_image:
            user.profile_image = profile_image
        user.save()
        return user

    def seed_personal_color(self):
        personal_color, _ = PersonalColor.objects.update_or_create(
            type_name='여름 쿨 라이트',
            defaults={
                'base_temperature': PersonalColor.BaseTemperature.cool,
                'season': PersonalColor.SeasonChoice.summer,
                'tone': PersonalColor.ToneChoices.LIGHT,
                'description': '맑고 부드러운 쿨톤 컬러가 잘 어울리는 톤입니다.',
                'temperature_degree': 85,
                'brightness_degree': 65,
                'saturation_degree': 30,
                'turbidity_degree': 18,
                'glossiness_degree': 40,
                'contrast_degree': 35,
                'best_pccs': ['lt', 'sf'],
                'sub_pccs': ['p', 'ltg'],
            },
        )
        return personal_color

    def seed_diagnosis(self, user, personal_color):
        payload = {
            'personal_color_code': 'summer-cool-light',
            'korean_name': '여름 쿨 라이트',
            'english_name': 'Summer Cool Light',
            'confidence_score': 93,
            'diagnosed_at': date(2026, 6, 15),
            'summary': '맑고 부드러운 쿨톤 컬러가 당신의 매력을 가장 빛나게 해요.',
            'keywords': ['맑은 톤', '부드러운 대비', '쿨 핑크 베이스', '저채도'],
            'image_features': [
                {'key': 'clear', 'title': '맑음', 'description': '깨끗하고 투명한 인상', 'icon': 'sun'},
                {'key': 'soft', 'title': '부드러움', 'description': '은은하고 부드러운 톤', 'icon': 'cloud'},
                {'key': 'refined', 'title': '세련됨', 'description': '차분하고 도시적인 분위기', 'icon': 'diamond'},
                {'key': 'elegant', 'title': '우아함', 'description': '자연스럽고 우아한 무드', 'icon': 'leaf'},
            ],
            'skin_metrics': {
                'brightness': 65,
                'saturation': 30,
                'clarity': 18,
                'gloss': 40,
                'contrast': 35,
                'cool_warm': 85,
            },
            'radar_chart': {
                'brightness': 65,
                'saturation': 30,
                'clarity': 82,
                'gloss': 40,
                'contrast': 35,
                'coolness': 85,
            },
            'style_guide': {
                'hair_colors': [
                    {
                        'name': '애쉬 브라운',
                        'hex': '#6D554A',
                        'image': self.media_path_or_none('demo/style/hair-ash-brown.png'),
                        'order': 1,
                    },
                    {
                        'name': '다크 쿨 브라운',
                        'hex': '#46372F',
                        'image': self.media_path_or_none('demo/style/hair-dark-cool-brown.png'),
                        'order': 2,
                    },
                ],
                'accessories': [
                    {
                        'name': '실버',
                        'description': '실버, 화이트 골드, 쿨톤 주얼리',
                        'image': self.media_path_or_none('demo/style/silver-accessory.png'),
                        'order': 1,
                    },
                ],
                'recommended_styles': [
                    {'name': '라벤더', 'hex': '#C5B9DF', 'order': 1},
                    {'name': '소프트 블루', 'hex': '#AFC4DB', 'order': 2},
                    {'name': '그레이', 'hex': '#B8BBC2', 'order': 3},
                    {'name': '쿨 핑크', 'hex': '#DDA8BD', 'order': 4},
                ],
            },
            'is_demo': True,
        }

        original_image = self.media_path_or_none('demo/diagnosis/original/summer-cool-light-original.jpg')
        generated_image = self.media_path_or_none('demo/diagnosis/generated/summer-cool-light-natural.jpg')

        diagnosis = DiagnosisResult.objects.filter(user=user, personal_color=personal_color, is_demo=True).first()
        if not diagnosis:
            diagnosis = DiagnosisResult(user=user, personal_color=personal_color, is_demo=True)

        for key, value in payload.items():
            setattr(diagnosis, key, value)
        if original_image:
            diagnosis.uploaded_image = original_image
        if generated_image:
            diagnosis.generated_makeup_image = generated_image
        else:
            diagnosis.generated_makeup_image = None
        diagnosis.full_clean()
        diagnosis.save()
        return diagnosis

    def replace_representative_colors(self, diagnosis):
        items = [
            {'name': '쿨 핑크', 'hex': '#EDA0BA', 'order': 1},
            {'name': '라이트 로즈', 'hex': '#E5B7CD', 'order': 2},
            {'name': '소프트 라일락', 'hex': '#CEABD3', 'order': 3},
            {'name': '라벤더', 'hex': '#B6A2D4', 'order': 4},
            {'name': '페리윙클', 'hex': '#9B96D0', 'order': 5},
            {'name': '소프트 블루그레이', 'hex': '#9FAFC1', 'order': 6},
        ]
        DiagnosisRepresentativeColor.objects.filter(diagnosis=diagnosis).delete()
        DiagnosisRepresentativeColor.objects.bulk_create(
            [DiagnosisRepresentativeColor(diagnosis=diagnosis, **item) for item in items]
        )
        return len(items)

    def replace_makeover_styles(self, diagnosis):
        items = [
            {
                'key': 'natural',
                'name': '내추럴',
                'description': '자연스럽고 깨끗한 데일리 룩',
                'image': self.media_path_or_none('demo/diagnosis/generated/summer-cool-light-natural.jpg'),
                'order': 1,
                'is_default': True,
            },
            {
                'key': 'daily',
                'name': '데일리',
                'description': '생기 있는 데일리 룩',
                'image': self.media_path_or_none('demo/diagnosis/generated/summer-cool-light-daily.jpg'),
                'order': 2,
                'is_default': False,
            },
            {
                'key': 'clear',
                'name': '청순',
                'description': '맑고 청순한 룩',
                'image': self.media_path_or_none('demo/diagnosis/generated/summer-cool-light-clear.jpg'),
                'order': 3,
                'is_default': False,
            },
            {
                'key': 'romantic',
                'name': '로맨틱',
                'description': '사랑스러운 핑크 룩',
                'image': self.media_path_or_none('demo/diagnosis/generated/summer-cool-light-romantic.jpg'),
                'order': 4,
                'is_default': False,
            },
            {
                'key': 'smoky',
                'name': '스모키',
                'description': '우아한 음영 메이크업',
                'image': self.media_path_or_none('demo/diagnosis/generated/summer-cool-light-smoky.jpg'),
                'order': 5,
                'is_default': False,
            },
        ]
        DiagnosisMakeoverStyle.objects.filter(diagnosis=diagnosis).delete()
        DiagnosisMakeoverStyle.objects.bulk_create(
            [DiagnosisMakeoverStyle(diagnosis=diagnosis, **item) for item in items]
        )
        return len(items)

    def replace_color_palettes(self, diagnosis):
        groups = {
            'best': [
                {'name': '쿨 로즈', 'hex': '#EB96B4', 'order': 1},
                {'name': '베이비 핑크', 'hex': '#EDB4C9', 'order': 2},
                {'name': '라일락 핑크', 'hex': '#D9A5CC', 'order': 3},
                {'name': '소프트 라벤더', 'hex': '#B9A6D7', 'order': 4},
                {'name': '페리윙클', 'hex': '#9992CC', 'order': 5},
            ],
            'neutral': [
                {'name': '쿨 베이지', 'hex': '#D8D3D1', 'order': 1},
                {'name': '라이트 그레이', 'hex': '#C6C5C7', 'order': 2},
                {'name': '블루 그레이', 'hex': '#B8BFCA', 'order': 3},
                {'name': '소프트 슬레이트', 'hex': '#9FAEC0', 'order': 4},
            ],
            'accent': [
                {'name': '로즈 핑크', 'hex': '#C66783', 'order': 1},
                {'name': '모브', 'hex': '#B66A8B', 'order': 2},
                {'name': '소프트 퍼플', 'hex': '#866EAA', 'order': 3},
                {'name': '딥 페리윙클', 'hex': '#626D9C', 'order': 4},
            ],
            'worst': [
                {'name': '웜 오렌지', 'hex': '#F1B054', 'order': 1},
                {'name': '테라코타', 'hex': '#DE9061', 'order': 2},
                {'name': '머스터드', 'hex': '#DFC35B', 'order': 3},
                {'name': '올리브', 'hex': '#99975B', 'order': 4},
            ],
        }
        DiagnosisColorPalette.objects.filter(diagnosis=diagnosis).delete()
        objects = []
        for group, items in groups.items():
            objects.extend(DiagnosisColorPalette(diagnosis=diagnosis, group=group, **item) for item in items)
        DiagnosisColorPalette.objects.bulk_create(objects)
        return len(objects)

    def replace_recommended_products(self, diagnosis):
        items = [
            {
                'category': 'base',
                'category_name': '베이스',
                'tone_label': '라이트 베이지 계열',
                'brand': '에스쁘아',
                'product_name': '프로 테일러 비 글로우 쿠션',
                'shade': '아이보리',
                'description': '맑고 자연스럽게 피부톤을 밝혀주는 베이스',
                'image': self.media_path_or_none('demo/products/base-cushion.png'),
                'product_url': None,
                'order': 1,
            },
            {
                'category': 'lip',
                'category_name': '립',
                'tone_label': '쿨 핑크 MLBB',
                'brand': '롬앤',
                'product_name': '쥬시 래스팅 틴트',
                'shade': '베어 그레이프',
                'description': '맑고 부드러운 입술 톤 연출',
                'image': self.media_path_or_none('demo/products/lip-tint.png'),
                'product_url': None,
                'order': 2,
            },
            {
                'category': 'cheek',
                'category_name': '치크',
                'tone_label': '라벤더 핑크',
                'brand': '클리오',
                'product_name': '에센셜 립치크 탭',
                'shade': '라벤더 핑크',
                'description': '은은하고 맑은 생기 표현',
                'image': self.media_path_or_none('demo/products/cheek.png'),
                'product_url': None,
                'order': 3,
            },
            {
                'category': 'eye',
                'category_name': '아이',
                'tone_label': '쿨 라벤더 팔레트',
                'brand': '클리오',
                'product_name': '프로 아이 팔레트',
                'shade': '라벤더 스쿱',
                'description': '차분하고 세련된 쿨톤 아이 연출',
                'image': self.media_path_or_none('demo/products/eye-palette.png'),
                'product_url': None,
                'order': 4,
            },
        ]
        DiagnosisRecommendedProduct.objects.filter(diagnosis=diagnosis).delete()
        objects = []
        for item in items:
            product, _ = Product.objects.update_or_create(
                brand=item['brand'],
                name=item['product_name'],
                defaults={
                    'category': self.product_category(item['category']),
                    'description': item['description'],
                    'product_url': item['product_url'] or '',
                    'match_score': 93,
                },
            )
            objects.append(DiagnosisRecommendedProduct(diagnosis=diagnosis, product=product, **item))
        DiagnosisRecommendedProduct.objects.bulk_create(objects)
        return len(objects)

    def product_category(self, category):
        return {
            'base': Product.Category.BASE,
            'lip': Product.Category.LIP,
            'cheek': Product.Category.CHEEK,
            'eye': Product.Category.EYE,
        }.get(category, Product.Category.ETC)

    def replace_recommended_lenses(self, diagnosis):
        items = [
            {
                'rank': 'BEST',
                'brand': '오렌즈',
                'product_name': '스칸디 라이트 그레이',
                'color': '라이트 그레이',
                'description': '맑은 눈매를 연출하는 자연스러운 그레이',
                'image': self.media_path_or_none('demo/lenses/light-gray.png'),
                'order': 1,
            },
            {
                'rank': 'BEST',
                'brand': '렌즈미',
                'product_name': '키치링크 그레이',
                'color': '쿨 그레이',
                'description': '차분하고 세련된 쿨 그레이',
                'image': self.media_path_or_none('demo/lenses/cool-gray.png'),
                'order': 2,
            },
            {
                'rank': 'GOOD',
                'brand': '아이돌렌즈',
                'product_name': '루나 그레이',
                'color': '소프트 그레이',
                'description': '부드럽고 자연스러운 데일리 렌즈',
                'image': self.media_path_or_none('demo/lenses/soft-gray.png'),
                'order': 3,
            },
        ]
        DiagnosisRecommendedLens.objects.filter(diagnosis=diagnosis).delete()
        DiagnosisRecommendedLens.objects.bulk_create(
            [DiagnosisRecommendedLens(diagnosis=diagnosis, **item) for item in items]
        )
        return len(items)
