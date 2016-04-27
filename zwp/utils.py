from django.conf import settings
from django.utils import translation
from django.contrib.staticfiles.storage import staticfiles_storage
import os
import sys
from .models import DataSource, Directory, DownloadBatch
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
    lang = translation.get_language()

    if lang is None:
        return 'en'

    return lang.split('-')[0]


def static_url(ds, path):
    if ds.static_url:
        return os.path.join(ds.static_url, path)
    else:
        return staticfiles_storage.url('zwp_ds_{}/{}'.format(ds.name, path))


def get_or_create_object(session, key, model, user=None):
    kwargs = {}

    if user and user.is_authenticated():
        kwargs['user'] = user

    if not session.session_key or key not in session:
        obj = model.objects.create(**kwargs)
        session[key] = obj.pk

    else:
        try:
            obj = model.objects.get(pk=session[key])

        except model.DoesNotExist:
            obj = model.objects.create(**kwargs)
            session[key] = obj.pk

    return obj


def get_or_create_download_batch(request):
    return get_or_create_object(
        request.session,
        'zwp_download_batch',
        DownloadBatch,
        user=request.user
    )


def get_or_none(session, key, model):
    if not session.session_key or key not in session:
        return None

    try:
        return model.objects.get(pk=session[key])

    except model.DoesNotExist:
        return None


def find_interpreter():
    """
    Attempt to locate the Python interpreter. sys.executable is not useful
    if the application is running e.g. under uwsgi.

    For example, if os.__file__ returns something like '/usr/lib64/python3.4/os.py',
    the interpreter should be located at ../../bin/python. If that is not the case,
    it reverts to sys.executable.
    """
    path = os.path.join(os.path.dirname(os.__file__), '..', '..', 'bin', 'python')

    if os.path.exists(path):
        return path

    return sys.executable
