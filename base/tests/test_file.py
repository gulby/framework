from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.core.files.base import File as DjangoFile
from xxhash import xxh64

from base.tests import BaseTestCase, get_uploaded_file, BaseNoTransactionTestCase
from base.utils import compute_file_hash
from base.models.file import Blob, File
from base.transaction import Transaction


def get_blob_path(file_hash):
    return "{}/{}/{}".format(file_hash[0:2], file_hash[2:4], file_hash)


class UploadedFileTest(BaseTestCase):
    def test(self):
        uploaded_file = get_uploaded_file("base/apps.py")
        assert isinstance(uploaded_file, DjangoFile)

        x = xxh64()
        x.update(uploaded_file.read())
        file_hash = x.hexdigest()

        file_path = get_blob_path(file_hash)
        if not default_storage.exists(file_path):
            default_storage.save(file_path, uploaded_file)

        disk_file = default_storage.open(file_path)
        file_hash2 = compute_file_hash(disk_file)
        assert file_hash == file_hash2


class DjangoFileTest(BaseTestCase):
    def test(self):
        f = open("base/apps.py", "rb")
        file = DjangoFile(f)
        assert file.name == "base/apps.py"
        file.open()
        file_hash = compute_file_hash(file)
        assert file_hash
        assert file.size


class BlobTest(BaseTestCase):
    def test(self):
        uploaded_file = get_uploaded_file("base/apps.py")
        file_hash = compute_file_hash(uploaded_file)
        blob = Blob.objects.create(uname=file_hash, file=uploaded_file)
        assert blob.name == "apps.py"
        assert blob.ext == "py"
        assert blob.size == 83

        with self.assertRaises(IntegrityError):
            Blob(file=uploaded_file, uname=file_hash)


class BlobTest2(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            uploaded_file = get_uploaded_file("base/apps.py")
            file_hash = compute_file_hash(uploaded_file)
            Blob.objects.create(file=uploaded_file, file_hash=file_hash)
        with Transaction():
            blob = Blob.objects.order_by("-id").first()
            assert blob._file is None
            file = blob.file
            assert isinstance(file, DjangoFile)
            file_hash = compute_file_hash(file)
            assert blob.uname == file_hash
            file2 = blob.file
            file_hash2 = compute_file_hash(file2)
            assert file_hash2 == file_hash


class BlobUnameTest(BaseTestCase):
    def test(self):
        uploaded_file = get_uploaded_file("base/apps.py")
        blob = Blob()
        fake_hash_value = "1234567890ABCDEF1234567890ABCDEF".lower()
        blob.uname = fake_hash_value
        blob.file = uploaded_file
        assert blob.name == "apps.py"
        assert blob.ext == "py"
        assert blob.size == 83


class FileTest(BaseTestCase):
    def test(self):
        uploaded_file = get_uploaded_file("base/apps.py")
        file = File.objects.create(file=uploaded_file)
        assert file.name == "apps.py"
        assert file.ext == "py"
        assert file.size == 83

        uploaded_file.open()
        file2 = File.objects.create(file=uploaded_file, name="apps2.py")
        assert file2
        assert file2 != file
        assert file2.blob == file.blob
        assert file2.name == "apps2.py"
        assert file2.ext == "py"
        assert file2.size == 83
