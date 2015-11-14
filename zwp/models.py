from django.core.urlresolvers import reverse
import os
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
        return self._opts['static_url']


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
    def __init__(self, *args, **kwargs):
        super(Directory, self).__init__(*args, **kwargs)
        self._is_dir = True
        self._icon = None
        self._text_icon = None
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


class Part:
    def __init__(self, d, name):
        self._dir = d
        self._name = name
   
    @property
    def ds(self):
        return self._dir.ds

    @property
    def label(self):
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
            return self._dir.metadata_for(self.base_name)[n]

        except KeyError:
            return None
