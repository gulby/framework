from base.tests import BaseTestCase
from base.models import File
from django.conf import settings


class FileAbsPathTest(BaseTestCase):
    def test(self):
        f = self.get_uploaded_file("base/apps.py")
        file_instance = File.objects.create(file=f)
        assert file_instance.file_abs_path == "{}/{}".format(settings.MEDIA_ROOT, file_instance.file_path)
