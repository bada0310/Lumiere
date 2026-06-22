from django.core.management.base import BaseCommand

from diagnosis.services.makeup_generation import process_next_makeup_job


class Command(BaseCommand):
    help = 'Process queued diagnosis GenAI makeup image jobs.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10)

    def handle(self, *args, **options):
        processed = 0
        for _ in range(options['limit']):
            job = process_next_makeup_job()
            if not job:
                break
            processed += 1
            self.stdout.write(f'processed job={job.pk} status={job.status}')
        self.stdout.write(self.style.SUCCESS(f'Processed {processed} makeup generation job(s).'))
