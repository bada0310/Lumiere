from django.core.management.base import BaseCommand, CommandError

from diagnosis.domain.palette_seed_data import validate_palette_payload
from diagnosis.domain.tone_keys import CANONICAL_TONE_KEYS
from diagnosis.models import PersonalColorPalette
from diagnosis.services.palettes import serialize_palette


class Command(BaseCommand):
    help = 'Validate fixed personal color palette rows for all canonical toneKeys.'

    def handle(self, *args, **options):
        rows = {palette.tone_key: palette for palette in PersonalColorPalette.objects.all()}
        errors = []

        missing = [tone_key for tone_key in CANONICAL_TONE_KEYS if tone_key not in rows]
        extra = sorted(set(rows.keys()) - set(CANONICAL_TONE_KEYS))
        if missing:
            errors.append('Missing rows: ' + ', '.join(missing))
        if extra:
            errors.append('Unknown rows: ' + ', '.join(extra))
        if len(rows) != len(CANONICAL_TONE_KEYS):
            errors.append(f'Expected {len(CANONICAL_TONE_KEYS)} rows, found {len(rows)}')

        for tone_key in CANONICAL_TONE_KEYS:
            palette = rows.get(tone_key)
            if not palette:
                continue
            if palette.is_placeholder:
                errors.append(f'{tone_key}: is_placeholder must be False')
            errors.extend(validate_palette_payload(tone_key, serialize_palette(palette)))

        if errors:
            raise CommandError('Invalid PersonalColorPalette rows:\n' + '\n'.join(errors))

        self.stdout.write(
            self.style.SUCCESS(
                f'Validated {len(CANONICAL_TONE_KEYS)} PersonalColorPalette rows. all is_placeholder=False'
            )
        )
