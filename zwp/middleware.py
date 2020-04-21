from django.conf import settings
from zwp.metadata import Users
from zwp.models import DataSource, PartAcl


class PartAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        part_acl = PartAcl()

        if request.user.is_authenticated:
            username = request.user.username

        else:
            username = None

        for opts in settings.ZWP_DATA_SOURCES:
            ds = DataSource(opts)
            u = Users(ds)
            part_acl.add(ds, list(u.get_parts(username)))

        request.user.part_acl = part_acl

        response = self.get_response(request)
        return response
