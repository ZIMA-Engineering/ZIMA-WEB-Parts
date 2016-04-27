from django.apps import AppConfig
from django.conf import settings
import sys

class ZwpConfig(AppConfig):
    name = 'zwp'
    verbose_name = 'ZIMA-WEB-Parts'

    def ready(self):
        if not settings.DEBUG:
            return

        static_dirs = list(settings.STATICFILES_DIRS)

        for ds in settings.ZWP_DATA_SOURCES:
            static_dirs.append(('zwp_ds_{}'.format(ds['name']), ds['path']))

        setattr(settings, 'STATICFILES_DIRS', static_dirs)
