from django.conf import settings
import os


ZWP_METADATA_DIR = getattr(settings, 'ZWP_METADATA_DIR', '0000-index')
ZWP_METADATA_FILE = getattr(settings, 'ZWP_METADATA_FILE', 'metadata.ini')
ZWP_USERS_FILE = getattr(settings, 'ZWP_METADATA_DIR', 'users.ini')
ZWP_DIR_ICON = getattr(settings, 'ZWP_DIR_ICON', 'logo.png')
ZWP_DIR_TEXT_ICON = getattr(settings, 'ZWP_DIR_TEXT_ICON', 'logo-text.png')
ZWP_PART_THUMBNAIL_DIR = getattr(settings, 'ZWP_PART_THUMBNAIL_DIR', ZWP_METADATA_DIR + '/thumbnails')
ZWP_PART_THUMBNAIL_WIDTH = getattr(settings, 'ZWP_PART_THUMBNAIL_WIDTH', 128)

ZWP_DOWNLOAD_ROOT = getattr(
    settings,
    'ZWP_DOWNLOAD_ROOT',
    os.path.join(settings.MEDIA_ROOT, 'zwp/downloads')
)

ZWP_DOWNLOAD_URL = getattr(
    settings,
    'ZWP_DOWNLOAD_URL',
    os.path.join(settings.MEDIA_URL, 'zwp/downloads')
)
