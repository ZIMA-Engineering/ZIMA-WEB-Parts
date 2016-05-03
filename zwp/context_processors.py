from django.conf import settings
from .models import DataSource, DownloadBatch
from .utils import get_or_none


def data_sources(request):
    return {
        'zwp_data_sources': list(map(
            lambda opts: DataSource(opts),
            settings.ZWP_DATA_SOURCES
        )),
    }


def download_batch(request):
    return {
        'download_batch': get_or_none(request.session, 'zwp_download_batch', DownloadBatch),
    }
