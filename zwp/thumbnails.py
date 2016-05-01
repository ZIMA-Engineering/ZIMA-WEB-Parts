import importlib
from .settings import ZWP_THUMBNAIL_BACKEND, ZWP_PART_THUMBNAIL_SIZE
from .utils import static_url
from .storage import DataSourceStorage

try:
    from easy_thumbnails.files import get_thumbnailer

except ImportError:
    pass


def get_thumbnail_backend():
    path = ZWP_THUMBNAIL_BACKEND.split('.')
    module = importlib.import_module('.'.join(path[0:-1]))
    return getattr(module, path[-1])


def direct(part):
    return {
        'thumb': {
            'url': static_url(part.ds, part.thumbnail),
            'width': ZWP_PART_THUMBNAIL_SIZE[0],
            'height': ZWP_PART_THUMBNAIL_SIZE[1],
        }
    }


def easy_thumbnails(part):
    thumbnailer = get_thumbnailer(DataSourceStorage(part.ds), part.thumbnail)

    return {
        'thumb': thumbnailer.get_thumbnail({'size': ZWP_PART_THUMBNAIL_SIZE}),
    }
