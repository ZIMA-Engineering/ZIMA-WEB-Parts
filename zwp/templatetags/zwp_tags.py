from django import template
from django.http import Http404
from django.utils.safestring import mark_safe
from zwp.utils import format_dir, static_url
from zwp.models import Directory
import os
import json
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

        parent = Directory(context['zwp_dir'].ds, parent_path, parent_name, root=root, user=context['request'].user)

    try:
        context.update({
            'zwp_parent': parent,
            'zwp_dirs': context['zwp_dir'].children
        })

    except FileNotFoundError as e:
        raise e
        raise Http404

    return context


@register.simple_tag(takes_context=True)
def zwp_json_tree(context):
    ret = []
    d = context['zwp_dir']
    path = d.full_path.split('/')

    root = Directory(d.ds, '', os.path.basename(d.ds.path), root=True, user=context['request'].user)

    for child in root.children:
        ret.append(format_dir(child, path))

    return mark_safe(json.dumps(ret))


@register.filter
def part_column(part, c):
    v = part.get_column(c.handle)

    if v is None:
        return ''
    else:
        return v


@register.inclusion_tag('zwp/part_thumbnail.html')
def part_thumbnail(part):
    ret = {'part': part}

    if not part.thumbnail:
        return ret

    ret.update(part.thumbnail_context)

    return ret

@register.simple_tag
def zwp_static(ds, path):
    return static_url(ds, path)

@register.inclusion_tag('zwp/dir_label.html')
def dir_label(d):
    return {'dir': d}
