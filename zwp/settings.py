from django.conf import settings


ZWP_METADATA_DIR = getattr(settings, 'ZWP_METADATA_DIR', '0000-index')
ZWP_METADATA_FILE = getattr(settings, 'ZWP_METADATA_DIR', 'metadata.ini')
ZWP_DIR_ICON = getattr(settings, 'ZWP_DIR_ICON', 'logo.png')
ZWP_DIR_TEXT_ICON = getattr(settings, 'ZWP_DIR_TEXT_ICON', 'logo-text.png')
