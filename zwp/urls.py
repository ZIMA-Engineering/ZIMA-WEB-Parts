from django.conf.urls import include, url
from . import views

urlpatterns = [
    url('^downloads$', views.DownloadsView.as_view(), name='zwp_downloads'),
    url(
        '^download/(?P<key>[a-zA-Z0-9]+)$',
        views.download,
        name='zwp_download'
    ),
    url(
        '^(?P<ds>[a-zA-Z0-9\-_]+)/(?P<path>.*)$',
        views.DirectoryContentView.as_view(),
        name='zwp_dir'
    ),
]
