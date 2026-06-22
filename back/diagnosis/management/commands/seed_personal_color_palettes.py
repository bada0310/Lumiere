from copy import deepcopy

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from diagnosis.domain.palette_seed_data import PALETTE_SEED_DATA, validate_palette_seed_data
from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS, tone_key_to_personal_color_fields
from diagnosis.models import PersonalColor, PersonalColorPalette


class Command(BaseCommand):
    help = 'Seed complete fixed personal color palette master data for all canonical toneKeys.'

    def handle(self, *args, **options):
        errors = validate_palette_seed_data(PALETTE_SEED_DATA)
        if errors:
            raise CommandError('Invalid palette seed data:\n' + '\n'.join(errors))

        with transaction.atomic():
            created = 0
            updated = 0
            for tone_key in CANONICAL_TONE_KEYS:
                payload = deepcopy(PALETTE_SEED_DATA[tone_key])
                personal_color = self.upsert_personal_color(tone_key, payload)
                defaults = self.palette_defaults(payload, personal_color)
                _, was_created = PersonalColorPalette.objects.update_or_create(
                    tone_key=tone_key,
                    defaults=defaults,
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f'PersonalColorPalette seeded. rows={len(CANONICAL_TONE_KEYS)} created={created} updated={updated}'
            )
        )

    def upsert_personal_color(self, tone_key, payload):
        fields = tone_key_to_personal_color_fields(tone_key)
        axes = payload['axes']
        defaults = {
            'type_name': payload['label'],
            'base_temperature': fields['base_temperature'],
            'season': fields['season'],
            'tone': fields['tone'],
            'description': payload['description'],
            'temperature_degree': 82 if axes['temperature'] == 'cool' else 20,
            'brightness_degree': self.degree(axes['brightness']),
            'saturation_degree': self.degree(axes['chroma']),
            'turbidity_degree': 100 - self.degree(axes['chroma']),
            'glossiness_degree': 50,
            'contrast_degree': self.degree(axes['contrast']),
            'best_pccs': self.pccs_codes(tone_key),
            'sub_pccs': [],
        }
        personal_color = (
            PersonalColor.objects.filter(tone_key=tone_key).first()
            or PersonalColor.objects.filter(type_name=payload['label']).first()
            or PersonalColor(tone_key=tone_key)
        )
        for key, value in defaults.items():
            setattr(personal_color, key, value)
        personal_color.tone_key = tone_key
        personal_color.full_clean()
        personal_color.save()
        return personal_color

    def palette_defaults(self, payload, personal_color):
        makeup = payload['makeupColorGuide']
        return {
            'data': payload,
            'tone_name': payload['label'],
            'season': payload['season'],
            'temperature': payload['temperature'],
            'brightness': payload['brightness'],
            'chroma': payload['chroma'],
            'contrast': payload['contrast'],
            'description': payload['description'],
            'keywords': payload['keywords'],
            'best_colors': payload['palettes']['best'],
            'worst_colors': payload['palettes']['worst'],
            'makeup_palette': payload['makeupPalette'],
            'base_makeup_guide': makeup['base']['guide'],
            'lip_guide': makeup['lip']['guide'],
            'cheek_guide': makeup['blush']['guide'],
            'eye_guide': makeup['eye']['guide'],
            'styling_keywords': payload['stylingKeywords'],
            'recommended_product_tone_range': payload['recommendedProductToneRange'],
            'is_placeholder': False,
            'personal_color': personal_color,
        }

    def degree(self, value):
        return {
            'low': 25,
            'low_to_medium': 38,
            'medium_low': 40,
            'medium': 55,
            'medium_high': 72,
            'high': 86,
        }.get(value, 50)

    def pccs_codes(self, tone_key):
        tone = tone_key.rsplit('_', 1)[-1]
        return {
            'bright': ['b', 'v'],
            'light': ['p', 'lt'],
            'mute': ['sf', 'ltg'],
            'deep': ['dp', 'dk'],
        }.get(tone, ['lt'])
