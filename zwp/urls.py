from django.conf.urls import include, url
from . import views

urlpatterns = [
    url('^(?P<ds>[a-zA-Z0-9\-_]+)/(?P<path>.*)$', views.show_path, name='zwp_dir'),
]
