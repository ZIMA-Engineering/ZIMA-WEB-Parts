from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from zwp.models import DataSource
from zwp.metadata import Users
from zwp.auth import data_sources


class DataSourceBackend(BaseBackend):
    """
    Authenticate agains users defined in users.ini in the data directory.
    """
    def authenticate(self, request, username=None, password=None):
        for opts in data_sources():
            u = Users(DataSource(opts))

            if u.authenticate(username, password):
                try:
                    user = User.objects.get(username=username)

                except User.DoesNotExist:
                    user = User.objects.create(
                        username=username,
                        password='in users.ini',
                    )

                return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)

        except User.DoesNotExist:
            return None
