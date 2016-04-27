from django.conf import settings


def data_sources():
    return filter(
        lambda v: v.get('auth', False),
        settings.ZWP_DATA_SOURCES
    )
