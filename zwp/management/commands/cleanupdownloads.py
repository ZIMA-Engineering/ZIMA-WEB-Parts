from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from zwp.models import DownloadBatch
from datetime import timedelta
import os
from zwp.settings import ZWP_DOWNLOAD_ROOT


class Command(BaseCommand):
    help = 'Delete ZIP files of expired download batches'
    
    def add_arguments(self, parser):
        parser.add_argument('seconds', type=int)

    def handle(self, *args, **options):
        batches = DownloadBatch.objects.filter(
            state=DownloadBatch.DONE,
            updated_at__lt=(timezone.now() - timedelta(seconds=options['seconds']))
        )

        for batch in batches:
            d = os.path.join(ZWP_DOWNLOAD_ROOT, batch.key)
            f = os.path.join(d, batch.zip_file + '.zip')

            if os.path.exists(f):
                os.unlink(f)

            if os.path.exists(d):
                os.rmdir(d)

            batch.state = batch.CLOSED
            batch.updated_at = timezone.now()
            batch.save()
