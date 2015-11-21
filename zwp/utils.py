from django.conf import settings
from django.utils import translation
from django.contrib.staticfiles.storage import staticfiles_storage
import os
from .models import DataSource, Directory
from .settings import ZWP_METADATA_DIR


def format_children(d):
    ret = []

    for child in d.children:
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

            for child in d.children:
                ret['children'].append(format_dir(child, target))

        else:
            ret['children'] = d.has_children

    else:
        ret['children'] = d.has_children

    return ret


def short_lang():
    return translation.get_language().split('-')[0]


def static_url(ds, path):
    if ds.static_url:
        return os.path.join(ds.static_url, path)
    else:
        return staticfiles_storage.url('zwp_ds_{}/{}'.format(ds.name, path))
