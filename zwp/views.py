from django.views.generic.base import View
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse, \
                        HttpResponseRedirect, HttpResponseServerError, HttpResponseBadRequest
from django.forms import modelformset_factory
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from .models import Directory, DownloadBatch, PartDownload
from .forms import PartDownloadFormSet
from .utils import format_children, get_or_create_download_batch, get_or_none
from .settings import ZWP_DIR_SHOW_LABEL
from .cache import clear_dir_content_cache


class DirectoryContentView(View):
    def dispatch(self, request, ds, path):
        d = Directory.from_path(ds, path, user=request.user, load=True)

        if d is False or not d.accessible:
            return HttpResponseForbidden()

        return super(DirectoryContentView, self).dispatch(request, d)

    def get(self, request, d):
        batch = get_or_none(request.session, 'zwp_download_batch', DownloadBatch)
        formset = self._formset(request, batch, d)

        if request.is_ajax():
            fetch = request.GET.get('fetch', None)

            if fetch == 'tree':
                return JsonResponse(format_children(d), safe=False)

            if fetch == 'content':
                return render(request, 'zwp/dir_content.html', {
                    'zwp_dir': d,
                    'formset': formset,
                    'show_label': ZWP_DIR_SHOW_LABEL,
                })

            return HttpResponseForbidden()

        return render(request, 'zwp/dir.html', {
            'zwp_dir': d,
            'formset': formset,
            'show_label': ZWP_DIR_SHOW_LABEL,
        })

    def post(self, request, d):
        batch = get_or_create_download_batch(request)
        formset = self._formset(request, batch, d)
        clear_dir_content_cache(request, d)

        if formset.is_valid():
            formset.save()

            if formset.marked > 0 and formset.unmarked == 0:
                messages.info(
                    request,
                    _('Marked {} files for download.').format(formset.marked)
                )

            elif formset.marked == 0 and formset.unmarked > 0:
                messages.info(
                    request,
                    _('Unmarked {} files for download.').format(formset.unmarked)
                )

            else:
                messages.info(
                    request,
                    _('Marked {marked} files for download, unmarked {unmarked} files.').format(
                        marked=formset.marked,
                        unmarked=formset.unmarked
                    )
                )

            return HttpResponseRedirect(request.path)

        return render(request, 'zwp/dir.html', {
            'zwp_dir': d,
            'formset': formset,
            'show_label': ZWP_DIR_SHOW_LABEL,
        })

    def _formset(self, request, batch, d):
        return PartDownloadFormSet(
            request,
            d,
            batch
        )


class DownloadsView(View):
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
            'formset': batch and DownloadsView.DownloadFormSet(
                queryset=self._queryset(batch)
            ),
        })

    def post(self, request):
        batch = get_or_none(request.session, 'zwp_download_batch', DownloadBatch)

        if batch is None:
            return HttpResponseBadRequest()

        formset = DownloadsView.DownloadFormSet(
            request.POST,
            queryset=self._queryset(batch)
        )

        if formset.is_valid():
            for dl in self._queryset(batch):
                clear_dir_content_cache(request, dl.part_model.part.dir)

            if 'download' in request.POST:
                if batch.make_zip():
                    del request.session['zwp_download_batch']
                    return HttpResponseRedirect(reverse('zwp_download', kwargs={
                        'key': batch.key,
                    }))

                else:
                    messages.error(
                        request,
                        _('Unable to generate the ZIP file. Please try again or contact '+
                           'the provider for support.')
                    )

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


def download(request, key):
    batch = get_object_or_404(
        DownloadBatch,
        key=key
    )

    if batch.user and batch.user != request.user:
        raise PermissionDenied()

    if request.is_ajax():
        return JsonResponse({
            'state': batch.state,
            'approx_size': batch.size,
            'real_size': batch.zip_size,
            'url': batch.zip_url,
        })

    return render(request, 'zwp/download.html', {
        'batch': batch,
    })
