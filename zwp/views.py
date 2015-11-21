from django.shortcuts import render
from django.http import HttpResponseForbidden, JsonResponse
from .models import Directory
from .utils import format_children


def show_path(request, ds, path):
    d = Directory.from_path(ds, path, load=True)

    if d is False:
        return HttpResponseForbidden()

    if request.is_ajax():
        fetch = request.GET.get('fetch', None)

        if fetch == 'tree':
            return JsonResponse(format_children(d), safe=False)

        if fetch == 'content':
            return render(request, 'zwp/dir_content.html', {
                'zwp_dir': d
            })

        return HttpResponseForbidden()
    
    return render(request, 'zwp/dir.html', {
        'zwp_dir': d
    })
