from django import template
from django.http import Http404
from zwp.utils import list_directories
from zwp.models import Directory
import os
from zwp.settings import *


register = template.Library()


@register.inclusion_tag('zwp/dir_tree.html', takes_context=True)
def directory_tree(context):
    if context['zwp_dir'].is_root:
        parent = None

    else:
        parent_path = os.path.dirname(context['zwp_dir'].path)
        parent_name = os.path.basename(context['zwp_dir'].path)

        if parent_name:
            root = False

        else:
            parent_name = os.path.basename(context['zwp_dir'].ds.path)
            root = True

        print("parent_path={}, parent_name={}".format(parent_path, parent_name))

        parent = Directory(context['zwp_dir'].ds, parent_path, parent_name, root=root)

    try:
        context.update({
            'zwp_parent': parent,
            'zwp_dirs': list_directories(context['zwp_dir'])
        })

    except FileNotFoundError as e:
        raise e
        raise Http404

    return context


@register.filter
def part_column(part, n):
    return part.get_column(n)

@register.inclusion_tag('zwp/part_thumbnail.html')
def part_thumbnail(part):
    return {
        'part': part,
        'width': ZWP_PART_THUMBNAIL_WIDTH
    }

@register.simple_tag
def zwp_static(ds, path):
    print(ds, path, ds.static_url)
    return os.path.join(ds.static_url, path)

@register.inclusion_tag('zwp/dir_label.html')
def dir_label(d):
    return {'dir': d}
