from django.conf.urls import include, url
from . import views

urlpatterns = [
    url('^downloads$', views.DownloadView.as_view(), name='zwp_downloads'),
    url(
        '^(?P<ds>[a-zA-Z0-9\-_]+)/(?P<path>.*)$',
        views.DirectoryContentView.as_view(),
        name='zwp_dir'
    ),
]
