import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS
from products.models import Product, ProductOffer, ProductOption, ProductOptionToneScore
from products.services.recommendation import grade_from_score


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = 'Seed curated Product catalog data from products/fixtures/catalog JSON files.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Validate and preview without saving.')
        parser.add_argument('--commit', action='store_true', help='Persist catalog seed data.')
        parser.add_argument('--reset-catalog', action='store_true', help='Delete seeded Product rows before importing.')
        parser.add_argument(
            '--fixtures-dir',
            default=None,
            help='Directory containing products_catalog.json, product_options.json, product_offers.json, option_tone_scores.json.',
        )

    def handle(self, *args, **options):
        if options['dry_run'] == options['commit']:
            raise CommandError('Use exactly one of --dry-run or --commit.')

        fixtures_dir = Path(options['fixtures_dir']) if options['fixtures_dir'] else default_fixtures_dir()
        payload = load_catalog_payload(fixtures_dir)
        validate_catalog_payload(payload)

        stats = Counter()
        try:
            with transaction.atomic():
                if options['reset_catalog']:
                    product_ids = [row['product_id'] for row in payload['products']]
                    deleted, _ = Product.objects.filter(id__in=product_ids).delete()
                    stats['reset_deleted'] = deleted

                product_map = import_products(payload['products'], stats)
                option_map = import_options(payload['options'], product_map, stats)
                import_offers(payload['offers'], option_map, stats)
                import_scores(payload['scores'], option_map, stats)
                mark_representative_offers(option_map.values())

                if options['dry_run']:
                    raise DryRunRollback()
        except DryRunRollback:
            self.stdout.write(self.style.WARNING('dry-run complete; all changes rolled back.'))

        self.stdout.write(self.style.SUCCESS(format_stats(stats)))


def default_fixtures_dir():
    return Path(__file__).resolve().parents[2] / 'fixtures' / 'catalog'


def load_catalog_payload(fixtures_dir):
    files = {
        'products': 'products_catalog.json',
        'options': 'product_options.json',
        'offers': 'product_offers.json',
        'scores': 'option_tone_scores.json',
    }
    payload = {}
    for key, filename in files.items():
        path = fixtures_dir / filename
        if not path.exists():
            raise CommandError(f'Missing catalog fixture: {path}')
        with path.open('r', encoding='utf-8') as source:
            data = json.load(source)
        if not isinstance(data, list):
            raise CommandError(f'{filename} must contain a JSON array.')
        payload[key] = data
    return payload


def validate_catalog_payload(payload):
    errors = []
    products = payload['products']
    options = payload['options']
    offers = payload['offers']
    scores = payload['scores']

    if not 30 <= len(products) <= 50:
        errors.append(f'products_catalog.json must contain 30-50 products; found {len(products)}.')

    product_ids = require_unique(products, 'product_id', errors, 'products_catalog.json')
    option_ids = require_unique(options, 'option_id', errors, 'product_options.json')
    offer_ids = require_unique(offers, 'offer_id', errors, 'product_offers.json')

    product_required = {
        'product_id',
        'brand',
        'product_name',
        'category',
        'texture',
        'finish',
        'representative_image_url',
        'description',
    }
    option_required = {
        'option_id',
        'product_id',
        'option_no',
        'option_name',
        'hex_code',
        'rgb',
        'brightness',
        'saturation',
        'coolness',
        'warmth',
        'depth',
        'softness',
        'contrast',
        'tone_tag',
        'color_family',
    }
    offer_required = {'offer_id', 'product_id', 'option_id', 'mall_name', 'price', 'product_url'}
    score_required = {'option_id', 'target_tone', 'match_score', 'grade', 'reason'}

    option_counts = Counter()
    option_product = {}

    for row in products:
        require_fields(row, product_required, errors, 'products_catalog.json')
        if row.get('category') not in Product.Category.values:
            errors.append(f'Invalid product category for product_id={row.get("product_id")}: {row.get("category")}')
        if row.get('finish') not in Product.Finish.values:
            errors.append(f'Invalid product finish for product_id={row.get("product_id")}: {row.get("finish")}')
        if int_or_none(row.get('product_id')) is None:
            errors.append(f'Invalid product_id={row.get("product_id")}')

    for row in options:
        require_fields(row, option_required, errors, 'product_options.json')
        product_id = row.get('product_id')
        option_id = row.get('option_id')
        if product_id not in product_ids:
            errors.append(f'option_id={option_id} references missing product_id={product_id}')
        option_counts[product_id] += 1
        option_product[option_id] = product_id
        if row.get('color_family') not in Product.ColorFamily.values:
            errors.append(f'Invalid color_family for option_id={option_id}: {row.get("color_family")}')
        if not isinstance(row.get('rgb'), list) or len(row.get('rgb')) != 3:
            errors.append(f'option_id={option_id} rgb must be [r, g, b].')
        for key in ['brightness', 'saturation', 'coolness', 'warmth', 'depth', 'softness', 'contrast']:
            if not in_range(row.get(key), 0, 100):
                errors.append(f'option_id={option_id} {key} must be 0-100.')
        for index, channel in enumerate(row.get('rgb') if isinstance(row.get('rgb'), list) else []):
            if not in_range(channel, 0, 255):
                errors.append(f'option_id={option_id} rgb[{index}] must be 0-255.')

    for product_id in product_ids:
        count = option_counts[product_id]
        if not 3 <= count <= 10:
            errors.append(f'product_id={product_id} must have 3-10 options; found {count}.')

    for row in offers:
        require_fields(row, offer_required, errors, 'product_offers.json')
        option_id = row.get('option_id')
        product_id = row.get('product_id')
        if option_id not in option_ids:
            errors.append(f'offer_id={row.get("offer_id")} references missing option_id={option_id}')
        if option_id in option_product and option_product[option_id] != product_id:
            errors.append(f'offer_id={row.get("offer_id")} product_id does not match option product_id.')
        if not in_range(row.get('price'), 0, 10_000_000):
            errors.append(f'offer_id={row.get("offer_id")} price must be a positive integer.')

    score_tones_by_option = defaultdict(set)
    for row in scores:
        require_fields(row, score_required, errors, 'option_tone_scores.json')
        option_id = row.get('option_id')
        target_tone = row.get('target_tone')
        if option_id not in option_ids:
            errors.append(f'score references missing option_id={option_id}')
        if target_tone not in CANONICAL_TONE_KEYS:
            errors.append(f'Invalid target_tone for option_id={option_id}: {target_tone}')
        if not in_range(row.get('match_score'), 0, 100):
            errors.append(f'Invalid match_score for option_id={option_id}: {row.get("match_score")}')
        expected_grade = str(grade_from_score(row.get('match_score'))).upper()
        if str(row.get('grade')).upper() != expected_grade:
            errors.append(
                f'Invalid grade for option_id={option_id}, target_tone={target_tone}: '
                f'{row.get("grade")} should be {expected_grade}'
            )
        score_tones_by_option[option_id].add(target_tone)

    canonical_set = set(CANONICAL_TONE_KEYS)
    for option_id in option_ids:
        missing = canonical_set - score_tones_by_option[option_id]
        if missing:
            errors.append(f'option_id={option_id} missing {len(missing)} tone scores.')

    if errors:
        raise CommandError('Invalid catalog fixtures:\n' + '\n'.join(errors[:80]))


def import_products(rows, stats):
    product_map = {}
    for row in rows:
        product, created = Product.objects.update_or_create(
            id=row['product_id'],
            defaults={
                'brand': row['brand'],
                'name': row['product_name'],
                'canonical_key': f'catalog:{row["product_id"]}',
                'category': row['category'],
                'texture': row['texture'],
                'finish': row['finish'],
                'representative_image_url': row['representative_image_url'],
                'image_url': row['representative_image_url'],
                'description': row['description'],
            },
        )
        product_map[row['product_id']] = product
        stats['products_created' if created else 'products_updated'] += 1
    return product_map


def import_options(rows, product_map, stats):
    option_map = {}
    for row in rows:
        rgb = row['rgb']
        option, created = ProductOption.objects.update_or_create(
            id=row['option_id'],
            defaults={
                'product': product_map[row['product_id']],
                'option_no': str(row['option_no']),
                'option_name': row['option_name'],
                'option_key': option_key(row),
                'image_url': row.get('image_url', ''),
                'color_family': row['color_family'],
                'analyzed_tone_tag': row['tone_tag'],
                'hex_code': row['hex_code'],
                'rgb_r': rgb[0],
                'rgb_g': rgb[1],
                'rgb_b': rgb[2],
                'brightness': row['brightness'],
                'saturation': row['saturation'],
                'coolness': row['coolness'],
                'warmth': row['warmth'],
                'depth': row['depth'],
                'softness': row['softness'],
                'contrast': row['contrast'],
            },
        )
        option_map[row['option_id']] = option
        stats['options_created' if created else 'options_updated'] += 1
    return option_map


def import_offers(rows, option_map, stats):
    for row in rows:
        _, created = ProductOffer.objects.update_or_create(
            id=row['offer_id'],
            defaults={
                'option': option_map[row['option_id']],
                'mall_name': row['mall_name'],
                'price': row['price'],
                'product_url': row['product_url'],
                'naver_product_id': str(row.get('naver_product_id', '')),
                'is_representative': False,
            },
        )
        stats['offers_created' if created else 'offers_updated'] += 1


def import_scores(rows, option_map, stats):
    for row in rows:
        _, created = ProductOptionToneScore.objects.update_or_create(
            option=option_map[row['option_id']],
            target_tone=row['target_tone'],
            defaults={
                'match_score': row['match_score'],
                'grade': str(row['grade']).upper(),
                'reason': row['reason'],
            },
        )
        stats['scores_created' if created else 'scores_updated'] += 1


def mark_representative_offers(options):
    for option in options:
        offers = list(option.offers.order_by('price', 'id'))
        if not offers:
            continue
        representative = offers[0]
        option.offers.exclude(id=representative.id).update(is_representative=False)
        if not representative.is_representative:
            representative.is_representative = True
            representative.save(update_fields=['is_representative'])


def require_unique(rows, field, errors, filename):
    values = [row.get(field) for row in rows]
    counts = Counter(values)
    duplicates = [value for value, count in counts.items() if count > 1]
    if duplicates:
        errors.append(f'{filename} has duplicate {field}: {duplicates[:10]}')
    return set(values)


def require_fields(row, fields, errors, filename):
    missing = sorted(field for field in fields if field not in row)
    if missing:
        errors.append(f'{filename} row missing fields {missing}: {row}')


def option_key(row):
    return normalize_key(f'{row["product_id"]}-{row["option_no"]}-{row["option_name"]}')


def normalize_key(value):
    text = str(value or '').strip().lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^0-9a-z_-]+', '', text)
    return text[:220] or 'default'


def in_range(value, low, high):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return False
    return low <= number <= high


def int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def format_stats(stats):
    return ' '.join(f'{key}={stats[key]}' for key in sorted(stats))
