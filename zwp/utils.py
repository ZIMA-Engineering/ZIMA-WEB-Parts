from django.conf import settings
from django.utils import translation
from django.contrib.staticfiles.storage import staticfiles_storage
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


def has_children(d):
    for f in os.listdir(d.data_path):
        if f != '0000-index' and os.path.isdir(os.path.join(d.data_path, f)):
            return True

    return False


def format_children(d):
    ret = []

    for child in list_directories(d):
        ret.append(format_dir(child))

    return ret


def format_dir(d, path = []):
    ret = {
        'id': d.full_path,
        'text': d.label,
        'state': {
            'opened': False,
            'disabled': False,
            'selected': False
        },
        'url': d.url
    }

    if d.icon:
        ret['text'] = '<img src="{}" alt="{}">'.format(
            static_url(d.ds, d.icon),
            d.label
        )

    elif d.text_icon:
        ret['icon'] = static_url(d.ds, d.text_icon)

    if path and d.name == path[0]:
        if len(path) == 1:
            ret['state']['selected'] = True
   
        target = path[1:]

        if target:
            ret['state']['opened'] = True
            ret['children'] = []

            for child in list_directories(d):
                ret['children'].append(format_dir(child, target))

        else:
            ret['children'] = has_children(d)

    else:
        ret['children'] = has_children(d)

    return ret


def short_lang():
    return translation.get_language().split('-')[0]


def static_url(ds, path):
    if ds.static_url:
        return os.path.join(ds.static_url, path)
    else:
        return staticfiles_storage.url('zwp_ds_{}/{}'.format(ds.name, path))
