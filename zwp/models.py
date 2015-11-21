from django.core.urlresolvers import reverse
from django.contrib.staticfiles.storage import staticfiles_storage
import os
import re
from .metadata import Metadata
from .settings import *


class DataSource(object):
    def __init__(self, name, opts):
        self._name = name
        self._opts = opts

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._opts['path']

    @property
    def static_url(self):
        return self._opts.get('static_url', None)


class Item(object):
    def __init__(self, ds, path, name, root=False):
        self._ds = ds
        self._path = path
        self._name = name
        self._label = None
        self._children = []
        self._is_dir = False
        self._is_root = root

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

    @property
    def data_path(self):
        return os.path.join(self._ds.path, self._path, self._name)

    @property
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

    @property
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
    def from_path(ds_name, path, load=False):
        try:
            ds = DataSource(ds_name, settings.ZWP_DATA_SOURCES[ds_name])

        except KeyError:
            return False

        is_root = not path
        abs_path = os.path.abspath(os.path.join(ds.path, path))

        if not abs_path.startswith(ds.path):
            return False

        d = Directory(
            ds,
            os.path.dirname(path),
            os.path.basename(abs_path), root=is_root
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

        self._load_metadata()

    @property
    def data_path(self):
        if self._is_root:
            return self._ds.path

        else:
            return super(Directory, self).data_path

    @property
    def is_root(self):
        return self._is_root

    @property
    def icon(self):
        if self._icon is False or self._icon:
            return self._icon

        self._icon = self._find_icon(ZWP_DIR_ICON)
        return self._icon

    @property
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
    
    @property
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

    @property
    def part_thumbnails(self):
        if self._part_thumbnails:
            return self._part_thumbnails

        self._part_thumbnails = {}
        thumb_path = os.path.join(self.data_path, ZWP_PART_THUMBNAIL_DIR)

        if not os.path.exists(thumb_path):
            return self._part_thumbnails

        for f in os.listdir(thumb_path):
            parts = f.split('.')

            if parts[-1].lower() not in ['jpg', 'png']:
                continue

            self._part_thumbnails['.'.join(parts[0:-1])] = os.path.join(
                self.full_path, ZWP_PART_THUMBNAIL_DIR, f        
            )

        return self._part_thumbnails

    def load(self):
        if self._loaded:
            return

        self._children = []
        abs_path = self.data_path

        for f in sorted(os.listdir(abs_path)):
            item_abs_path = os.path.join(abs_path, f)

            if os.path.isdir(item_abs_path):
                if f != ZWP_METADATA_DIR:
                    self._children.append(Directory(self.ds, self.full_path, f))

            elif os.path.isfile(item_abs_path):
                self.add_part(f)
        
        self._loaded = True


    def add_part(self, name):
        self._parts.append(Part(self, name))

    def metadata_for(self, name):
        return self._parts_meta[name]

    def _load_metadata(self):
        meta = Metadata(self)

        if not meta.exists() or not meta.parse():
            return
        
        self._label = meta.label
        self._columns = meta.columns
        self._parts_meta = meta.parts_data

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
    def __init__(self, d, name):
        self._dir = d
        self._name = name
        self._metadata = None
   
    @property
    def ds(self):
        return self._dir.ds

    @property
    def dir(self):
        return self._dir

    @property
    def label(self):
        return self._name

    @property
    def name(self):
        return self._name
    
    @property
    def base_name(self):
        return '.'.join(self._name.split('.')[0:-1])

    @property
    def thumbnail(self):
        try:
            return self._dir.part_thumbnails[self.base_name]

        except KeyError:
            return None

    def get_column(self, n):
        try:
            return self._meta[n]

        except KeyError:
            return None

    @property
    def _meta(self):
        if self._metadata:
            return self._metadata

        try:
            self._metadata = self._dir.metadata_for(self.base_name)

        except KeyError:
            self._metadata = {}

        return self._metadata
