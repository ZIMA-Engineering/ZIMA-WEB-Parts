from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse, \
                        HttpResponseRedirect
from .models import Directory, DownloadBatch
from .forms import PartDownloadFormSet
from .utils import format_children, get_or_create_download_batch, get_or_none


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

    if request.method == 'POST':
        return download_part(request, d)
  
    batch = get_or_none(request.session, 'zwp_download_batch', DownloadBatch)

    part_downloads = batch and {
        dl.part_model.hash: dl
        for dl in batch.partdownload_set.select_related('part_model').all()
    }
   
    formset = PartDownloadFormSet(initial=[
        {
            'batch': batch,
            'part': part,
            'dl': part_downloads and part_downloads.get(part.hash, None),
        } for part in d.parts
    ])

    return render(request, 'zwp/dir.html', {
        'zwp_dir': d,
        'formset': formset,
    })


def download_part(request, d):
    batch = get_or_create_download_batch(request.session)
    
    part_downloads = batch and {
        dl.part_model.hash: dl
        for dl in batch.partdownload_set.select_related('part_model').all()
    }

    formset = PartDownloadFormSet(request.POST, initial=[
        {
            'batch': batch,
            'part': part,
            'dl': part_downloads and part_downloads.get(part.hash, None),
        } for part in d.parts
    ])

    if formset.is_valid():
        print('valid, save!')
        formset.save()
        return HttpResponseRedirect(request.path)

    for form in formset:
        for f in form:
            if f.errors:
                print(f.errors)

    return None
