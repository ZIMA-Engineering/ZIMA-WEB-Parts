from django.core.exceptions import PermissionDenied
import os
import configparser
import pam
from .settings import ZWP_METADATA_DIR, ZWP_METADATA_FILE, ZWP_USERS_FILE, ZWP_ACL_FILE, \
                      ZWP_PART_THUMBNAIL_DIR
from .signals import part_meta_load


class Parameter:
    def __init__(self, lang, handle):
        self._lang = lang
        self._labels = {}
        self.handle = handle
        self.type = None

    def set_label(lang, label):
        self._labels[lang] = label

    @property
    def label(self):
        if not self._labels:
            return self.handle

        if self._lang in self._labels:
            return self._labels[self._lang]

        return self._labels[ list(self._labels.keys())[0] ]


class Metadata:
    def __init__(self, d):
        from .utils import short_lang

        self._dir = d
        self._path = os.path.join(d.data_path, ZWP_METADATA_DIR, ZWP_METADATA_FILE)
        self._lang = short_lang()
        self._data_includes = []
        self.thumbnail_paths = [os.path.join(d.data_path, ZWP_PART_THUMBNAIL_DIR)]

    def exists(self):
        return os.path.exists(self._path)

    def parse(self):
        self.cfg = configparser.ConfigParser(interpolation=None)
        self.cfg.read(self._path)

        from .models import Directory

        def tmp(x):
            meta = Metadata(Directory.from_path(
                self._dir.ds.name,
                self._resolve_path(x.strip()),
                user=self._dir.user
            ))
            meta.parse()
            return meta

        if self.cfg.has_option('Directory', 'IncludeParameters'):
            self._data_includes = list(map(tmp, self.cfg['Directory']['IncludeParameters'].split(',')))

        if self.cfg.has_option('Directory', 'IncludeThumbnails'):
            self.thumbnail_paths += list(map(
                lambda x: os.path.join(self._resolve_path(x.strip()), ZWP_PART_THUMBNAIL_DIR),
                self.cfg['Directory']['IncludeThumbnails'].split(',')
            ))

        return self.cfg.has_section('Parameters') or self._data_includes

    @property
    def label(self):
        label_opt = 'Label/{}'.format(self._lang)

        if self.cfg.has_option('Directory', label_opt):
            return self.cfg['Directory'][label_opt].replace('"', '')

        return None

    @property
    def columns(self):
        cols = {}

        for meta in self._data_includes:
            cols.update(meta._parse_columns())

        cols.update(self._parse_columns())

        return list(map(lambda x: x[1], sorted(cols.items())))

    @property
    def parts_data(self):
        data = {}

        for meta in self._data_includes:
            data.update(meta._parse_parts_data())

        data.update(self._parse_parts_data())

        return data

    def _resolve_path(self, path):
        if path.startswith('/'):
            return os.path.abspath(path)

        return os.path.abspath(os.path.join(self._dir.data_path, path))

    def _parse_columns(self):
        if not self.cfg.has_section('Directory'):
            return {}

        handles = [v.strip() for v in self.cfg['Directory']['Parameters'].split(',')]
        params = {}  # handle: {Parameter}

        # Load options from all languages
        for raw_opt in self.cfg.options('Parameters'):
            handle, param, opt = self._parse_opt(raw_opt)

            if not handle in params:
                params[handle] = Parameter(self._lang, handle)

            if param == 'Label':
                params[handle].set_label(
                    opt,
                    self.cfg['Parameters'][raw_opt].replace('"', '')
                )
            elif param == 'Type':
                params[handle].type = self.cfg['Parameters'][raw_opt].replace('"', '')

        return params

    def _parse_parts_data(self):
        ret = {}

        if not self.cfg.has_section('Parts'):
            return {}

        for raw_opt in self.cfg.options('Parts'):
            part, param, lang = [None, None, None]
            components = self._parse_opt(raw_opt)
            opts = {}

            if len(components) == 2:
                part, param = components
            elif len(components) == 3:
                part, param, lang = components
            else:
                continue

            if part not in ret:
                for _, data in part_meta_load.send(sender=self.__class__, name=param, cfg=self.cfg):
                    opts.update(data)

                ret[part] = opts

            if lang == self._lang or param not in ret[part]:
                ret[part][param] = self.cfg['Parts'][raw_opt]

        return ret

    def _parse_opt(self, raw_opt):
        parts = []

        if '/' in raw_opt:
            parts = raw_opt.split('/')

        elif '\\' in raw_opt:
            parts = raw_opt.split('\\')

        else:
            parts = [raw_opt]

        if len(parts) > 1:
            return parts

        return [parts[0]]


class Users:
    def __init__(self, ds):
        self._path = os.path.join(ds.path, ZWP_METADATA_DIR, ZWP_USERS_FILE)
        self.parse()

    def parse(self):
        if os.path.exists(self._path):
            self.cfg = configparser.ConfigParser()
            self.cfg.read(self._path)

        else:
            self.cfg = None

    def authenticate(self, username, password):
        if self.cfg is None or not self.cfg.has_section(username):
            return False

        source = 'internal'

        if self.cfg.has_option(username, 'source'):
            source = self.cfg[username]['source']

        if source == 'internal':
            return self.cfg[username]['password'] == password

        elif source == 'pam':
            p = pam.pam()
            return p.authenticate(username, password)

        raise PermissionDenied()

    def get_parts(self, username=None):
        if username is None:
            username = 'anonymous'

        if self.cfg is None or not self.cfg.has_option(username, 'parts'):
            return []

        return self.cfg[username]['parts'].split(',')


class Acl:
    def __init__(self, d):
        self._path = os.path.join(d.data_path, ZWP_METADATA_DIR, ZWP_ACL_FILE)

    def exists(self):
        return os.path.exists(self._path)

    def parse(self):
        self.cfg = configparser.ConfigParser()
        self.cfg.read(self._path)

        return True

    def is_accessible(self, user):
        if self.cfg.has_section('allow'):
            if self.cfg.has_option('allow', 'users'):
                if user is None:
                    return False

                elif user.username in self.cfg['allow']['users'].split(','):
                    return True

                else:
                    return False

        return True
