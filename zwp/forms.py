from django import forms
from django.forms.widgets import HiddenInput
from django.forms import BaseFormSet, formset_factory
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.utils.functional import cached_property
from django.db import IntegrityError, transaction
from .models import Directory, PartModel, PartDownload


class PartDownloadForm(forms.Form):
    download = forms.BooleanField(label=_('download'), required=False)

    def __init__(self, *args, **kwargs):
        self.part = kwargs.pop('part')
        self.user = kwargs.pop('user')
        self.was_marked = kwargs['initial']['download']

        super(PartDownloadForm, self).__init__(*args, **kwargs)

    def is_marked(self):
        return self.cleaned_data['download']

    def get_part_model(self):
        return PartModel.objects.get_or_create(
            ds_name=self.part.dir.ds.name,
            dir_path=self.part.dir.full_path,
            name=self.part.name,
        )[0]

    def save(self, batch):
        is_marked = self.is_marked()

        print('{}: is_marked={}; was={}'.format(self.part.name, is_marked, self.was_marked))

        if is_marked == self.was_marked:
            return

        if is_marked:
            PartDownload.objects.create(
                download_batch=batch,
                part_model=self.get_part_model(),
            )
            return 1

        return PartDownload.objects.filter(
            download_batch=batch,
            part_model__ds_name=self.part.dir.ds.name,
            part_model__dir_path=self.part.dir.full_path,
            part_model__name=self.part.name,
        ).delete()[0] * -1


class BasePartDownloadFormSet(BaseFormSet):
    def __init__(self, request, d, batch):
        self.request = request
        self.dir = d
        self.batch = batch
        self.marked_parts = batch and {
            dl.part_model.name: dl
            for dl in batch.partdownload_set.select_related('part_model').filter(
                part_model__ds_name=self.dir.ds.name,
                part_model__dir_path=self.dir.full_path,
            )
        }

        kwargs = {'initial': []}
        kwargs['initial'] = [
            {
                'download': batch and part.name in self.marked_parts,
            } for part in d.parts
        ]

        super(BasePartDownloadFormSet, self).__init__(request.POST or None, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super(BasePartDownloadFormSet, self).get_form_kwargs(index)
        kwargs['part'] = self.dir.parts[index]
        kwargs['user'] = self.request.user
        return kwargs

    def save(self):
        self.marked = 0
        self.unmarked = 0

        with transaction.atomic():
            for form in self.forms:
                ret = form.save(self.batch)

                if ret == 1:
                    self.marked += 1

                elif ret == -1:
                    self.unmarked += 1

    @cached_property
    def marked_count(self):
        return len(self.marked_parts) if self.marked_parts else 0


PartDownloadFormSet = formset_factory(
    PartDownloadForm,
    formset=BasePartDownloadFormSet,
    extra=0
)
