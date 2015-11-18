from django.shortcuts import render
from django.http import HttpResponseForbidden, JsonResponse
from .utils import resolve_path, list_directories, format_children


def show_path(request, ds, path):
    item = resolve_path(ds, path)

    if item is False:
        return HttpResponseForbidden()

    if request.is_ajax():
        fetch = request.GET.get('fetch', None)

        if fetch == 'tree':
            return JsonResponse(format_children(item), safe=False)

        if fetch == 'content':
            # Must list directories explicitly, as this method loads
            # parts in this directory. It is normally called by rendering
            # navigation, but that does not happen when rendering only content.
            list_directories(item)
            return render(request, 'zwp/dir_content.html', {
                'zwp_dir': item
            })

        return HttpResponseForbidden()
    
    return render(request, 'zwp/dir.html', {
        'zwp_dir': item
    })
