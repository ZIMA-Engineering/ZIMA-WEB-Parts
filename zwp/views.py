from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse, \
                        HttpResponseRedirect, HttpResponseServerError, HttpResponseBadRequest
from django.forms import modelformset_factory
from .models import Directory, DownloadBatch, PartDownload
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


class DownloadView(View):
    DownloadFormSet = modelformset_factory(
        PartDownload,
        fields=(),
        can_delete=True,
        extra=0
    )

    def get(self, request):
        batch = get_or_none(request.session, 'zwp_download_batch', DownloadBatch)

        return render(request, 'zwp/downloads.html', {
            'batch': batch,
            'formset': batch and DownloadView.DownloadFormSet(
                queryset=self._queryset(batch)
            ),
        })

    def post(self, request):
        batch = get_or_none(request.session, 'zwp_download_batch', DownloadBatch)

        if batch is None:
            return HttpResponseBadRequest()

        formset = DownloadView.DownloadFormSet(
            request.POST,
            queryset=self._queryset(batch)
        )

        print(request.POST)
        if formset.is_valid():
            if 'download' in request.POST:
                # TODO: create a ZIP file
                pass

            elif 'update' in request.POST:
                formset.save()

            else:
                return HttpResponseBadRequest()

            return HttpResponseRedirect(request.path)

        return render(request, 'zwp/downloads.html', {
            'batch': batch,
            'formset': formset,
        })

    def _queryset(self, batch):
        return batch.partdownload_set.select_related('part_model').all() \
            .order_by('part_model__name')
