from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse, \
                        HttpResponseRedirect, HttpResponseServerError
from .models import Directory, DownloadBatch
from .forms import PartDownloadFormSet
from .utils import format_children, get_or_create_download_batch, get_or_none


class DirectoryContentView(View):
    def dispatch(self, request, ds, path):
        d = Directory.from_path(ds, path, load=True)

        if d is False:
            return HttpResponseForbidden()

        return super(DirectoryContentView, self).dispatch(request, d)

    def get(self, request, d):
        if request.is_ajax():
            fetch = request.GET.get('fetch', None)

            if fetch == 'tree':
                return JsonResponse(format_children(d), safe=False)

            if fetch == 'content':
                return render(request, 'zwp/dir_content.html', {
                    'zwp_dir': d
                })

            return HttpResponseForbidden()

        batch = get_or_none(request.session, 'zwp_download_batch', DownloadBatch)

        return render(request, 'zwp/dir.html', {
            'zwp_dir': d,
            'formset': self._formset(request, batch, d),
        })

    def post(self, request, d):
        batch = get_or_create_download_batch(request.session)
        formset = self._formset(request, batch, d)

        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(request.path)

        return HttpResponseServerError()

    def _formset(self, request, batch, d):
        part_downloads = batch and {
            dl.part_model.hash: dl
            for dl in batch.partdownload_set.select_related('part_model').all()
        }

        return PartDownloadFormSet(request.POST or None, initial=[
            {
                'batch': batch,
                'part': part,
                'dl': part_downloads and part_downloads.get(part.hash, None),
            } for part in d.parts
        ])
