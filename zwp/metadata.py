from django.core.exceptions import PermissionDenied
import os
import configparser
import pam
from .settings import ZWP_METADATA_DIR, ZWP_METADATA_FILE, ZWP_USERS_FILE, ZWP_ACL_FILE
from .signals import part_meta_load


class Metadata:
    def __init__(self, d):
        from .utils import short_lang

        self._dir = d
        self._path = os.path.join(d.data_path, ZWP_METADATA_DIR, ZWP_METADATA_FILE)
        self._lang = short_lang()

    def exists(self):
        return os.path.exists(self._path)

    def parse(self):
        self.cfg = configparser.ConfigParser()
        self.cfg.read(self._path)

        return self.cfg.has_section('params')

    @property
    def label(self):
        label_opt = '{}/label'.format(self._lang)

        if self.cfg.has_option('params', label_opt):
            return self.cfg['params'][label_opt].replace('"', '')

        return None

    @property
    def columns(self):
        return list(map(lambda x: x[1], sorted(self._parse_columns().items())))

    @property
    def parts_data(self):
        ret = {}

        for sec in self.cfg.sections():
            if sec == 'params':
                continue

            part = {}

            for _, data in part_meta_load.send(sender=self.__class__, name=sec, cfg=self.cfg):
                part.update(data)

            for raw_opt in self.cfg.options(sec):
                lang, opt = self._parse_opt(raw_opt)

                if lang not in part:
                    part[lang] = {}

                if not opt.isdigit():
                    continue

                part[lang][int(opt)] = self.cfg[sec][raw_opt]

            # Select language
            for lang in part:
                if lang == self._lang:
                    ret[sec] = part[lang]

            if sec not in ret and len(part) > 0:
                ret[sec] = part[ list(part.keys())[0] ]

        return ret

    def _parse_columns(self):
        columns = {}  # lang: [columns]

        # Load options from all languages
        for raw_opt in self.cfg.options('params'):
            lang, opt = self._parse_opt(raw_opt)

            if not lang in columns:
                columns[lang] = {}

            if not opt.isdigit():
                continue

            columns[lang][int(opt)] = self.cfg['params'][raw_opt].replace('"', '')

        # Select language
        for lang in columns:
            if lang == self._lang:
                return columns[lang]

        if len(columns) == 0:
            return []

        return columns[ list(columns.keys())[0] ]

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

        return [None, parts[0]]


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
