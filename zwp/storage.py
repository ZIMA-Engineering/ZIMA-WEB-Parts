from django.core.files.storage import FileSystemStorage
import os


class DataSourceStorage(FileSystemStorage):
    def __init__(self, ds, *args, **kwargs):
        kwargs['location'] = ds.path
        super(DataSourceStorage, self).__init__(*args, **kwargs)

    def path(self, name):
        # Do not use safe_join(), as the data source is not located under
        # MEDIA_ROOT and safe_join() raises SuspiciousFileOperation.
        return os.path.join(self.location, name)
