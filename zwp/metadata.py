from django.utils import translation
import os
import configparser
from .settings import ZWP_METADATA_DIR, ZWP_METADATA_FILE


class Metadata:
    def __init__(self, d):
        self._dir = d
        self._path = os.path.join(d.data_path, ZWP_METADATA_DIR, ZWP_METADATA_FILE)
        self._lang = translation.get_language().split('-')[0]

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
        columns = {}  # lang: [columns]

        # Load options from all languages
        for raw_opt in self.cfg.options('params'):
            parts = raw_opt.split('/')
            
            if len(parts) > 1:
                lang, opt = parts

            else:
                lang = None
                opt = parts[0]
            
            if not lang in columns:
                columns[lang] = []

            if not opt.isdigit():
                continue

            columns[lang].append(self.cfg['params'][raw_opt].replace('"', ''))

        # Select language
        for lang in columns:
            if lang == self._lang:
                return columns[lang]

        if len(columns) == 0:
            return []

        return columns[ columns.keys()[0] ]

    @property
    def parts_data(self):
        ret = {}

        for sec in self.cfg.sections():
            if sec == 'params':
                continue

            part = {}

            for opt in self.cfg.options(sec):
                if not opt.isdigit():
                    continue

                part[int(opt)] = self.cfg[sec][opt]
                
            ret[sec] = part

        return ret
