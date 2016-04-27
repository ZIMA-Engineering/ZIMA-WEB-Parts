from django.conf import settings
from .models import DataSource


def data_sources(request):
    return {
        'zwp_data_sources': list(map(
            lambda opts: DataSource(opts),
            settings.ZWP_DATA_SOURCES
        )),
    }
