from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key


def clear_dir_content_cache(request, d):
    k = make_template_fragment_key(
        'zwp_dir_content',
        [d.ds.name, d.full_path, request.user.username],
    )
    cache.delete(k)
