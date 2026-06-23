import hashlib
import re
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from diagnosis.domain.tone_profiles import normalize_profile_tone_key
from products.models import Product, ProductOffer, ProductOption, ProductOptionToneScore
from products.services.recommendation import build_user_tone_profile, calculate_option_match, grade_from_score


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = 'Migrate legacy flat Product rows into Product, ProductOption, ProductOffer, and ProductOptionToneScore.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes and roll them back.')
        parser.add_argument('--commit', action='store_true', help='Persist migrated data.')
        parser.add_argument('--limit', type=int, default=None, help='Limit source legacy Product rows.')
        parser.add_argument('--reset-new-products', action='store_true', help='Delete normalized Product rows before running.')

    def handle(self, *args, **options):
        if options['dry_run'] == options['commit']:
            raise CommandError('Use exactly one of --dry-run or --commit.')

        stats = {
            'source_rows': 0,
            'products_created': 0,
            'products_updated': 0,
            'options_created': 0,
            'options_updated': 0,
            'offers_created': 0,
            'scores_upserted': 0,
            'needs_review': 0,
        }

        try:
            with transaction.atomic():
                if options['reset_new_products']:
                    deleted, _ = Product.objects.filter(canonical_key__isnull=False).delete()
                    self.stdout.write(f'reset_new_products deleted={deleted}')

                queryset = Product.objects.filter(canonical_key__isnull=True).order_by('id')
                if options['limit']:
                    queryset = queryset[: options['limit']]

                for source in queryset:
                    stats['source_rows'] += 1
                    self.migrate_source_product(source, stats)

                if options['dry_run']:
                    raise DryRunRollback()
        except DryRunRollback:
            self.stdout.write(self.style.WARNING('dry-run complete; all changes rolled back.'))

        self.stdout.write(self.style.SUCCESS(self.format_stats(stats)))

    def migrate_source_product(self, source, stats):
        parsed = parse_product_name(source.name, source.brand)
        canonical_key = canonical_key_for(source.brand, parsed['product_name'], source.category)
        product, product_created = Product.objects.get_or_create(
            canonical_key=canonical_key,
            defaults={
                'brand': source.brand,
                'name': parsed['product_name'],
                'category': source.category,
                'texture': source.texture,
                'finish': source.finish,
                'representative_image_url': source.image_url,
                'description': source.description,
                'naver_category1': source.naver_category1,
                'naver_category2': source.naver_category2,
                'naver_category3': source.naver_category3,
                'naver_category4': source.naver_category4,
            },
        )
        stats['products_created' if product_created else 'products_updated'] += 1

        product_changed = False
        for field in ['texture', 'description', 'naver_category1', 'naver_category2', 'naver_category3', 'naver_category4']:
            if not getattr(product, field) and getattr(source, field):
                setattr(product, field, getattr(source, field))
                product_changed = True
        if not product.representative_image_url and source.image_url:
            product.representative_image_url = source.image_url
            product_changed = True
        if product_changed:
            product.save()

        option_key = option_key_for(parsed['option_no'], parsed['option_name'], source.hex_code)
        option, option_created = ProductOption.objects.get_or_create(
            product=product,
            option_key=option_key,
            defaults={
                'option_no': parsed['option_no'],
                'option_name': parsed['option_name'],
                'image_url': source.image_url,
                'color_family': source.color_family,
                'analyzed_tone_tag': normalize_profile_tone_key(source.tone_tag),
                'hex_code': source.hex_code,
                'rgb_r': source.rgb_r,
                'rgb_g': source.rgb_g,
                'rgb_b': source.rgb_b,
                'brightness': source.brightness,
                'saturation': source.saturation,
                'coolness': source.coolness,
                'warmth': source.warmth,
                'depth': source.depth,
                'softness': source.softness,
                'contrast': source.contrast,
            },
        )
        stats['options_created' if option_created else 'options_updated'] += 1
        if not option_created:
            update_option_from_source(option, source, parsed)

        _, offer_created = ProductOffer.objects.get_or_create(
            option=option,
            mall_name=source.mall_name,
            price=source.price,
            product_url=source.product_url,
            naver_product_id=source.naver_product_id,
            defaults={'is_representative': False},
        )
        stats['offers_created'] += int(offer_created)
        mark_representative_offer(option)

        target_tone = normalize_profile_tone_key(source.tone_tag)
        user_profile = build_user_tone_profile(target_tone)
        match = calculate_option_match(option, user_profile, source.category)
        if source.match_score:
            match['match_score'] = source.match_score
            match['grade'] = grade_from_score(source.match_score)
        if source.reason:
            match['reason'] = source.reason
        ProductOptionToneScore.objects.update_or_create(
            option=option,
            target_tone=target_tone,
            defaults={
                'match_score': match['match_score'],
                'grade': match['grade'],
                'reason': match['reason'],
            },
        )
        stats['scores_upserted'] += 1

        if parsed['needs_review']:
            stats['needs_review'] += 1
            self.stdout.write(
                safe_console_text(
                    f"NEEDS_REVIEW source_id={source.id} brand={source.brand} "
                    f"name={source.name} parsed_product={parsed['product_name']} "
                    f"parsed_option={parsed['option_no']} {parsed['option_name']}"
                )
            )

    def format_stats(self, stats):
        return ' '.join(f'{key}={value}' for key, value in stats.items())


def update_option_from_source(option, source, parsed):
    fields = {
        'option_no': parsed['option_no'],
        'option_name': parsed['option_name'],
        'image_url': source.image_url,
        'color_family': source.color_family,
        'analyzed_tone_tag': normalize_profile_tone_key(source.tone_tag),
        'hex_code': source.hex_code,
        'rgb_r': source.rgb_r,
        'rgb_g': source.rgb_g,
        'rgb_b': source.rgb_b,
        'brightness': source.brightness,
        'saturation': source.saturation,
        'coolness': source.coolness,
        'warmth': source.warmth,
        'depth': source.depth,
        'softness': source.softness,
        'contrast': source.contrast,
    }
    changed = False
    for field, value in fields.items():
        if value not in ['', None] and getattr(option, field) != value:
            setattr(option, field, value)
            changed = True
    if changed:
        option.save()


def mark_representative_offer(option):
    offers = list(option.offers.order_by('price', 'id'))
    if not offers:
        return
    representative = next((offer for offer in offers if offer.price), offers[0])
    option.offers.exclude(id=representative.id).update(is_representative=False)
    if not representative.is_representative:
        representative.is_representative = True
        representative.save(update_fields=['is_representative'])


def parse_product_name(name, brand=''):
    text = clean_text(name, brand)
    patterns = [
        re.compile(r'(?:\b[Nn][Oo]\.?\s*)?(?P<no>\d{1,3})\s*(?:호|번)?\s*(?P<option>[가-힣A-Za-z][가-힣A-Za-z0-9\s\'-]{1,32})(?=\s*(?:\(|\[|,|$))'),
        re.compile(r'(?P<option>[가-힣A-Za-z][가-힣A-Za-z0-9\s\'-]{1,24})\s+(?P<no>\d{1,3})\s*(?:호|번)?$'),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        option_no = compact(match.group('no'))
        option_name = compact(match.group('option'))
        parent_name = compact(f'{text[:match.start()]} {text[match.end():]}') or text
        parent_name = clean_parent_name(parent_name)
        return {
            'product_name': parent_name,
            'option_no': option_no,
            'option_name': option_name,
            'needs_review': len(parent_name) < 4 or len(option_name) < 2,
        }

    return {
        'product_name': clean_parent_name(text),
        'option_no': '',
        'option_name': 'default',
        'needs_review': True,
    }


def clean_text(value, brand=''):
    text = re.sub(r'<[^>]+>', ' ', str(value or ''))
    if brand and brand not in {'UNKNOWN', '브랜드 미상'}:
        text = re.sub(re.escape(brand), ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[[^\]]+\]', ' ', text)
    text = re.sub(r'\([^)]*(?:출고|배송|Pack|개|ml|g|color)[^)]*\)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+(?:\.\d+)?\s*(?:ml|g|oz|Ounce)\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\s*(?:개|종|color|컬러)\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:무료배송|정품|국내백화점|기획|증정|단품|세트|택1|1\+1|2개|3개)', ' ', text)
    return compact(text.replace('/', ' ').replace('_', ' '))


def clean_parent_name(value):
    text = re.sub(r'\([^)]*(?:봄웜|여름쿨|가을웜|겨울쿨|웜톤|쿨톤|라이트|브라이트|뮤트|딥)[^)]*\)', ' ', str(value or ''))
    text = re.sub(r'(?:봄웜|여름쿨|가을웜|겨울쿨|웜톤|쿨톤|라이트|브라이트|뮤트|딥)$', ' ', text)
    return compact(text.strip(' ,-_/'))


def canonical_key_for(brand, product_name, category):
    base = f'{normalize_key(brand)}|{normalize_key(category)}|{normalize_key(product_name)}'
    digest = hashlib.sha1(base.encode('utf-8')).hexdigest()[:12]
    return f'{base[:220]}|{digest}'


def option_key_for(option_no, option_name, hex_code):
    base = compact(f'{option_no} {option_name}') or 'default'
    key = normalize_key(base)
    if key == 'default' and hex_code:
        key = f'default-{normalize_key(hex_code)}'
    return key[:220] or 'default'


def normalize_key(value):
    text = str(value or '').strip().lower()
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'[^0-9a-z가-힣#]+', '', text)
    return text or 'unknown'


def compact(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def safe_console_text(value):
    encoding = sys.stdout.encoding or 'utf-8'
    return str(value).encode(encoding, errors='replace').decode(encoding, errors='replace')
