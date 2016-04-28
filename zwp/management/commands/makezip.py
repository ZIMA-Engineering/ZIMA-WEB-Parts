from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import os
import sys
from zipfile import ZipFile
from zwp.models import DownloadBatch
from zwp.settings import ZWP_DOWNLOAD_ROOT


class Command(BaseCommand):
    help = 'Creates a ZIP file for download batch'

    def add_arguments(self, parser):
        parser.add_argument('batch_id', type=int)

    def handle(self, *args, **options):
        try:
            batch = DownloadBatch.objects.get(pk=options['batch_id'])

        except DownloadBatch.DoesNotExist:
            raise CommandError('DownloadBatch "%s" does not exist' % options['batch_id'])

        try:
            batch.state = batch.PREPARING
            batch.save()

            self.daemonize()
            self.make_zip(batch)
            batch.state = batch.DONE

        except Exception as e:
            batch.state = batch.ERROR
            raise e

        finally:
            batch.save()

    def make_zip(self, batch):
        dls = batch.partdownload_set.select_related('part_model').all() \
                .order_by('part_model__name')

        zip_name, zip_dir, zip_path = self.zip_name(batch)

        if settings.DEBUG:
            import time
            time.sleep(10)

        os.makedirs(zip_dir, exist_ok=True)

        with ZipFile(zip_path, 'w') as zip:
            for dl in dls:
                zip.write(
                    dl.part_model.part.data_path,
                    '{}/{}'.format(zip_name, dl.part_model.part.name)
                )

        batch.zip_file = zip_name
        batch.updated_at = timezone.now()

    def daemonize(self):
        from django.db import connection
        connection.close()

        if os.fork() > 0:
            sys.exit(0)

        if os.fork() > 0:
            sys.exit(0)
        
        #sys.stdin.close()
        #sys.stdout.close()
        #sys.stderr.close()

    def zip_name(self, batch):
        name = 'parts-{}'.format(batch.pk)
        d = os.path.join(ZWP_DOWNLOAD_ROOT, batch.key)
        return name, d, os.path.join(d, name + '.zip')
