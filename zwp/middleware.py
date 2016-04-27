from django.conf import settings
from zwp.metadata import Users
from zwp.models import DataSource


class PartAccessMiddleware:
    def process_request(self, request):
        part_access = {}

        if request.user.is_authenticated():
            username = request.user.username

        else:
            username = None

        for opts in settings.ZWP_DATA_SOURCES:
            u = Users(DataSource(opts))
            part_access[ opts['name'] ] = list(u.get_parts(username))

        request.user.part_access = part_access
