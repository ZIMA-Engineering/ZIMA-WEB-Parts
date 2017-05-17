from django.db import models, IntegrityError
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
import hashlib
import os
import sys
import subprocess
import re
import random
import string
from .metadata import Users, Metadata, Acl
from .settings import *


class DataSource(object):
    def __init__(self, opts):
        self._opts = opts

    @property
    def name(self):
        return self._opts['name']

    @property
    def label(self):
        return self._opts.get('label', self._opts['name'])

    @property
    def path(self):
        return self._opts['path']

    @property
    def url(self):
        return reverse('zwp_dir', args=(self.name, ''))

    @property
    def static_url(self):
        return self._opts.get('static_url', None)


class Item(object):
    def __init__(self, ds, path, name, root=False, user=None):
        self._ds = ds
        self._path = path
        self._name = name
        self._label = None
        self._children = []
        self._is_dir = False
        self._is_root = root
        self.user = user
        return
        print("new {}: ds={}, path={}, name={}".format(
            self.__class__.__name__,
            self.ds.name,
            path,
            name
        ))

    def __str__(self):
        return "[{}] {}: {}".format(self._ds.name, self._path, self._name)

    @property
    def ds(self):
        return self._ds

    @property
    def path(self):
        return self._path

    @cached_property
    def data_path(self):
        return os.path.join(self._ds.path, self._path, self._name)

    @cached_property
    def full_path(self):
        if self._is_root:
            return self.path
        else:
            return os.path.join(self._path, self._name)

    @property
    def name(self):
        return self._name

    @property
    def label(self):
        return self._label if self._label else self._name

    @cached_property
    def url(self):
        base = reverse('zwp_dir', args=(self._ds.name, ''))

        if self._is_root:
            return base

        else:
            return os.path.join(base, self._path, self._name)

    @property
    def is_dir(self):
        return self._is_dir


class Directory(Item):
    @staticmethod
    def get(ds, path, name, user=None, **kwargs):
        """
        This method is used instead of the constructor, as it does not create a new object
        when it's already in cache.
        """
        full_path = os.path.join(path, name)

        key = make_template_fragment_key(
            'zwp_dir_instance',
            [ds.name, full_path, user and user.username]
        )
        v = cache.get(key)

        if v:
            print('get: cache hit for ds={}; dir={}; user={}'.format(ds.name, full_path, user))
            return v

        d = Directory(ds, path, name=name, user=user, **kwargs)
        cache.set(key, d, 60)
        print('cache miss for ds={}; dir={}; user={}'.format(ds.name, full_path, user))
        return d

    @staticmethod
    def from_path(ds_name, path, user=None, load=False, **kwargs):
        """
        Cached version of ``from_path``.
        """
        key = make_template_fragment_key(
            'zwp_dir_instance',
            [ds_name, path, user and user.username]
        )
        v = cache.get(key)

        if v:
            print('from_path: cache hit for ds={}; dir={}; user={}'.format(ds_name, path, user))

            if load:
                v.load()

            return v

        d = Directory._from_path(ds_name, path, user=user, load=load, **kwargs)
        cache.set(key, d, 60)
        print('cache miss for ds={}; dir={}; user={}'.format(ds_name, path, user))
        return d

    @staticmethod
    def _from_path(ds_name, path, load=False, user=None):
        """
        This method does not check the cache and always creates a new instance.
        """
        ds = None

        for opts in settings.ZWP_DATA_SOURCES:
            if opts['name'] == ds_name:
                ds = DataSource(opts)
                break
        else:
            return False

        is_root = not path
        abs_path = os.path.abspath(os.path.join(ds.path, path))

        if not abs_path.startswith(ds.path):
            return False

        d = Directory(
            ds,
            os.path.dirname(path),
            os.path.basename(abs_path),
            root=is_root,
            user=user
        )

        if load:
            d.load()

        return d

    def __init__(self, *args, **kwargs):
        super(Directory, self).__init__(*args, **kwargs)
        self._is_dir = True
        self._loaded = False
        self._icon = None
        self._text_icon = None
        self._indexes = None
        self._parts = []
        self._columns = []
        self._parts_meta = {}
        self._part_thumbnails = None

        self._load_acl()
        self._load_metadata()

    @cached_property
    def data_path(self):
        if self._is_root:
            return self._ds.path

        else:
            return super(Directory, self).data_path

    @property
    def is_root(self):
        return self._is_root

    @cached_property
    def icon(self):
        if self._icon is False or self._icon:
            return self._icon

        self._icon = self._find_icon(ZWP_DIR_ICON)
        return self._icon

    @cached_property
    def text_icon(self):
        if self._text_icon is False or self._text_icon:
            return self._text_icon

        self._text_icon = self._find_icon(ZWP_DIR_TEXT_ICON)
        return self._text_icon

    @property
    def children(self):
        if not self._loaded:
            self.load()

        return self._children

    @cached_property
    def has_children(self):
        if self._loaded:
            return len(self._children) > 0

        for f in os.listdir(self.data_path):
            if f != ZWP_METADATA_DIR and os.path.isdir(os.path.join(self.data_path, f)):
                return True

        return False

    @property
    def parts(self):
        return self._parts

    @property
    def columns(self):
        return self._columns

    @cached_property
    def part_thumbnails(self):
        if self._part_thumbnails:
            return self._part_thumbnails

        self._part_thumbnails = {}

        for thumb_path in self._meta.thumbnail_paths:
            if not os.path.exists(thumb_path):
                continue

            if os.path.commonprefix([self.ds.path, thumb_path]) != self.ds.path:
                print("Ignoring thumbnail path '{}': left data source directory".format(
                    thumb_path
                ))
                continue

            rel_path = os.path.relpath(thumb_path, self.ds.path)

            for f in os.listdir(thumb_path):
                parts = f.split('.')

                if parts[-1].lower() not in ['jpg', 'png']:
                    continue

                self._part_thumbnails['.'.join(parts[0:-1])] = os.path.join(
                    rel_path, f
                )

        return self._part_thumbnails

    def load(self):
        if self._loaded:
            return

        self._children = []
        abs_path = self.data_path
        parts = {}

        for f in sorted(os.listdir(abs_path)):
            item_abs_path = os.path.join(abs_path, f)

            if os.path.isdir(item_abs_path):
                if f == ZWP_METADATA_DIR:
                    continue

                d = Directory.get(self.ds, self.full_path, f, user=self.user)

                if d.accessible:
                    self._children.append(d)

            elif os.path.isfile(item_abs_path):
                p = self.make_part(f.encode('utf8', 'replace').decode('utf-8'))

                if p and p.type in ZWP_VERSIONED_PARTS:
                    if p.version_name in parts:
                        if p.version > parts[p.version_name].version:
                            self._parts.remove(parts[p.version_name])
                            parts[p.version_name] = p

                        else:
                            continue

                    else:
                        parts[p.version_name] = p

                if p:
                    self._parts.append(p)

        self._loaded = True

    def make_part(self, name):
        p = Part(self, name)

        if ZWP_PART_FILTERS and p.type not in ZWP_PART_FILTERS:
            return

        if self.user and self.user.part_acl.can_access(self.ds, p):
            p.accessible = True

        return p

    def metadata_for(self, name):
        return self._parts_meta[name]

    def _load_acl(self):
        acl = Acl(self)

        if not acl.exists():
            self.accessible = True
            return

        elif not acl.parse():
            self.accessible = False
            return

        self.accessible = acl.is_accessible(self.user)

    def _load_metadata(self):
        self._meta = Metadata(self)

        if not self._meta.exists() or not self._meta.parse():
            return

        self._label = self._meta.label
        self._columns = self._meta.columns
        self._parts_meta = self._meta.parts_data

    def _find_icon(self, name):
        ret = False
        path = os.path.join(self.data_path, ZWP_METADATA_DIR, name)

        if not os.path.exists(path):
            return ret

        ret = os.path.join(self.full_path, ZWP_METADATA_DIR, name)
        return ret

    def _find_index(self, name):
        if self._indexes is None:
            self._find_indexes()

        return self._indexes.get(name, False)

    def _index_url(self, name):
        if not self._indexes.get(name, False):
            return None

        if self.ds.static_url:
            return os.path.join(
                self.ds.static_url,
                self.full_path,
                ZWP_METADATA_DIR,
                self._indexes[name]
            )

        return staticfiles_storage.url('zwp_ds_{}/{}'.format(
            self.ds.name,
            os.path.join(
                self.full_path,
                ZWP_METADATA_DIR,
                self._indexes[name]
            )
        ))

    def _find_indexes(self):
        self._indexes = {}
        indexes = {
            'tech_spec': re.compile(r'^index([_a-z{2}]*)\.html$'),
            'parts_index': re.compile(r'^parts-index([_a-z{2}]*)\.html$')
        }
        path = os.path.join(self.data_path, ZWP_METADATA_DIR)

        if not os.path.exists(path):
            return False

        from .utils import short_lang

        current_lang = short_lang()
        tmp = {}
        is_lang = {k: False for k in indexes}

        for f in os.listdir(path):
            for name, rx in indexes.items():
                match = rx.match(f)

                if not match:
                    continue

                lang = match.group(1)[1:]

                if lang == current_lang:
                    self._indexes[name] = f
                    break

                if tmp.get(name, None) is None:
                    tmp[name] = f
                    is_lang[name] = len(lang) > 0

                elif is_lang[name] and not lang:
                    tmp[name] = f

            if len(self._indexes) == len(indexes):
                break

        for k, v in tmp.items():
            if k not in self._indexes:
                self._indexes[k] = v


def index_fn(v, m):
    @property
    def method(self):
        return getattr(self, m)(v)
    return method


for i in ['tech_spec', 'parts_index']:
     setattr(Directory, 'has_{}'.format(i), index_fn(i, '_find_index'))
     setattr(Directory, '{}_url'.format(i), index_fn(i, '_index_url'))


class Part:
    def __init__(self, d, name, accessible=False):
        self._dir = d
        self._name = name
        self.accessible = accessible

    def __str__(self):
        return 'Part {}/{}/{}'.format(self.ds.name, self.dir.full_path, self.name)

    @property
    def ds(self):
        return self._dir.ds

    @property
    def dir(self):
        return self._dir

    @property
    def label(self):
        return self.base_name

    @property
    def name(self):
        return self._name

    @cached_property
    def base_name(self):
        if self.type in ZWP_VERSIONED_PARTS and self.version > 0:
            return '.'.join(self._name.split('.')[0:-2])

        return '.'.join(self._name.split('.')[0:-1])

    @cached_property
    def version_name(self):
        if self.type in ZWP_VERSIONED_PARTS:
            return '.'.join(self._name.split('.')[0:-1])

        return self.base_name

    @cached_property
    def type(self):
        """
        Get part type, which is its extension.
        """
        parts = self._name.split('.')

        # .prt files are versioned, i.e. they end with a number
        if parts[-1].isdigit() and len(parts) > 1:
            self.version = int(parts[-1])
            return parts[-2]

        else:
            self.version = 0
            return parts[-1]

    @cached_property
    def version(self):
        """
        Get part version. The version is specified only for PRT files
        as a number after the extension, e.g. some-part.prt.1, where 1
        is the version.
        """
        self.type  # sets self.version
        return self.version

    @cached_property
    def data_path(self):
        return os.path.join(
            self.dir.data_path,
            self.name,
        )

    @cached_property
    def hash(self):
        return hashlib.sha256(''.join(os.path.join(
            self.ds.name,
            self.dir.full_path,
            self.name
        )).encode('utf-8')).hexdigest()

    @cached_property
    def size(self):
        return os.stat(self.data_path).st_size

    @cached_property
    def thumbnail(self):
        try:
            return self._dir.part_thumbnails[self.base_name]

        except KeyError:
            return None

    @cached_property
    def thumbnail_context(self):
        if not self.thumbnail:
            return {}

        from .thumbnails import get_thumbnail_backend
        return get_thumbnail_backend()(self)

    def get_column(self, n):
        try:
            return self._meta[n]

        except KeyError:
            return None

    @cached_property
    def _meta(self):
        try:
            return self._dir.metadata_for(self.base_name)

        except KeyError:
            return {}


class PartAcl:
    def __init__(self):
        self.rules = {}

    def add(self, ds, allowed):
        self.rules[ds.name] = allowed

    def can_access(self, ds, part):
        allowed = self.rules[ds.name]
        return part.type in allowed or '@all' in allowed


class PartModelManager(models.Manager):
    def existing(self, hash, part):
        p = self.get(hash=hash)
        p.part = part
        return p


class PartModel(models.Model):
    ds_name = models.CharField(_('data source'), max_length=50)
    dir_path = models.CharField(_('directory'), max_length=500)
    name = models.CharField(_('part'), max_length=255)
    hash = models.CharField(_('hash'), max_length=64, unique=True)
    objects = PartModelManager()

    @property
    def part(self):
        if hasattr(self, '_part'):
            return self._part

        self._part = None
        d = Directory.from_path(self.ds_name, self.dir_path, load=True)

        if not d:
            return None

        for p in d.parts:
            if p.name == self.name:
                self._part = p
                break

        return self._part

    @part.setter
    def part(self, v):
        self._part = v

    def save(self, *args, **kwargs):
        if not self.pk:
            self.hash = hashlib.sha256(''.join(os.path.join(
                self.ds_name,
                self.dir_path,
                self.name
            )).encode('utf-8')).hexdigest()

        super(PartModel, self).save(*args, **kwargs)


class DownloadBatch(models.Model):
    OPEN = 0
    PREPARING = 1
    DONE = 2
    ERROR = 3
    CLOSED = 4

    STATES = (
        (OPEN, _('Open')),
        (PREPARING, _('Preparation')),
        (DONE, _('Done')),
        (CLOSED, _('Closed')),
        (ERROR, _('Error')),
    )

    user = models.ForeignKey(User, null=True, blank=True)
    key = models.CharField(_('unique key'), max_length=40, unique=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), null=True)
    state = models.IntegerField(_('state'), default=OPEN)
    zip_file = models.CharField(_('zip file'), max_length=255, null=True)

    def __str__(self):
        return 'DownloadBatch #{}'.format(self.pk)

    def save(self, *args, **kwargs):
        if self.pk:
            return super(DownloadBatch, self).save(*args, **kwargs)

        for _ in range(5):
            try:
                self.key = self._generate_key(40)
                return super(DownloadBatch, self).save(*args, **kwargs)

            except IntegrityError:
                pass

        raise RuntimeError('unable to generate unique key')

    @property
    def size(self):
        return sum([
            dl.part_model.part.size
            for dl in self.partdownload_set.select_related('part_model').all()
        ])

    @cached_property
    def count(self):
        return self.partdownload_set.all().count()

    @cached_property
    def zip_url(self):
        return os.path.join(ZWP_DOWNLOAD_URL, self.key, self.zip_file + '.zip')

    @cached_property
    def zip_size(self):
        if not self.zip_file:
            return None

        try:
            return os.path.getsize(os.path.join(
                ZWP_DOWNLOAD_ROOT, self.key, self.zip_file + '.zip'
            ))

        except OSError:
            return None

    def make_zip(self):
        from .utils import find_interpreter

        return subprocess.call([
            find_interpreter(),
            os.path.join(settings.BASE_DIR, 'manage.py'),
            'makezip',
            str(self.pk)
        ]) == 0

    def _generate_key(self, length):
        return ''.join(
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for _ in range(length)
        )


class PartDownload(models.Model):
    download_batch = models.ForeignKey(DownloadBatch)
    part_model = models.ForeignKey(PartModel)
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)

    class Meta:
        unique_together = (('download_batch', 'part_model'),)
