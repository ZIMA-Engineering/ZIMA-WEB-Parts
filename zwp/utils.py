from django.conf import settings
from django.utils import translation
import os
from .models import DataSource, Directory
from .settings import ZWP_METADATA_DIR


def resolve_path(ds_name, path):
    try:
        ds = DataSource(ds_name, settings.ZWP_DATA_SOURCES[ds_name])

    except KeyError:
        return False

    is_root = not path
    abs_path = os.path.abspath(os.path.join(ds.path, path))

    if not abs_path.startswith(ds.path):
        return False

    return Directory(
        ds,
        os.path.dirname(path),
        os.path.basename(abs_path), root=is_root
    )


def list_directories(d):
    dirs = []
    abs_path = d.data_path

    for f in os.listdir(abs_path):
        item_abs_path = os.path.join(abs_path, f)

        if os.path.isdir(item_abs_path):
            if f != ZWP_METADATA_DIR:
                dirs.append(Directory(d.ds, d.full_path, f))

        elif os.path.isfile(item_abs_path):
            d.add_part(f)

    return dirs


def short_lang():
    return translation.get_language().split('-')[0]
