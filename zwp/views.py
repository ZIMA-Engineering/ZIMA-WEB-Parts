from django.shortcuts import render
from django.http import HttpResponseForbidden
from .utils import resolve_path


def show_path(request, ds, path):
    item = resolve_path(ds, path)

    if item is False:
        return HttpResponseForbidden()

    return render(request, 'zwp/dir.html', {
        'zwp_dir': item
    })
