from django.dispatch import Signal


part_meta_load = Signal(providing_args=['name', 'cfg'])
