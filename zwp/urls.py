from django.urls import path, re_path
from . import views

urlpatterns = [
    path('downloads', views.DownloadsView.as_view(), name='zwp_downloads'),
    re_path(
        r'^download/(?P<key>[a-zA-Z0-9]+)$',
        views.download,
        name='zwp_download'
    ),
    re_path(
        r'^(?P<ds>[a-zA-Z0-9\-_]+)/(?P<path>.*)$',
        views.DirectoryContentView.as_view(),
        name='zwp_dir'
    ),
]
