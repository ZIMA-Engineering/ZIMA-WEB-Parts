from django.conf import settings
import os


ZWP_METADATA_DIR = getattr(settings, 'ZWP_METADATA_DIR', '0000-index')
ZWP_METADATA_FILE = getattr(settings, 'ZWP_METADATA_FILE', 'metadata.ini')
ZWP_USERS_FILE = getattr(settings, 'ZWP_USERS_FILE', 'users.ini')
ZWP_ACL_FILE = getattr(settings, 'ZWP_ACL_FILE', 'acl.ini')
ZWP_DIR_ICON = getattr(settings, 'ZWP_DIR_ICON', 'logo.png')
ZWP_DIR_TEXT_ICON = getattr(settings, 'ZWP_DIR_TEXT_ICON', 'logo-text.png')
ZWP_PART_THUMBNAIL_DIR = getattr(settings, 'ZWP_PART_THUMBNAIL_DIR', ZWP_METADATA_DIR + '/thumbnails')
ZWP_PART_THUMBNAIL_SIZE = getattr(settings, 'ZWP_PART_THUMBNAIL_SIZE', (128, 128))
ZWP_THUMBNAIL_BACKEND = getattr(settings, 'ZWP_THUMBNAIL_BACKEND', 'zwp.thumbnails.direct')
ZWP_DIR_SHOW_LABEL = getattr(settings, 'ZWP_DIR_SHOW_LABEL', True)

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

ZWP_PART_FILTERS = getattr(settings, 'ZWP_PART_FILTERS', None)
