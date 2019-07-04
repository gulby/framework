import os

from base.tests import BaseTestCase, clear_media_folder, todo_test
from base.models import File
from base.utils import compute_file_hash


class FileCreateTest(BaseTestCase):
    def test_1(self):
        file = self.get_uploaded_file(file_path="base/apps.py")
        file_ins = File(file=file)
        assert os.path.isfile(os.path.join("media", file_ins.file_path))

    def test_2(self):
        file = self.get_uploaded_file(file_path="base/apps.py")
        file_ins = File.objects.create(file=file)
        assert os.path.isfile(os.path.join("media", file_ins.file_path))

    def test_3(self):
        file = self.get_uploaded_file(file_path="base/apps.py")
        file_ins = File()
        file_ins.file = file
        assert os.path.isfile(os.path.join("media", file_ins.file_path))

    def test_difference_file_create(self):
        file = self.get_uploaded_file(file_path="base/apps.py")
        file_ins = File.objects.create(file=file)
        assert os.path.isfile(os.path.join("media", file_ins.file_path))

        file2 = self.get_uploaded_file(file_path="base/utils.py")
        file_ins2 = File.objects.create(file=file2)
        assert os.path.isfile(os.path.join("media", file_ins2.file_path))

        assert file_ins.file_hash != file_ins2.file_hash


class SearchFileTest(BaseTestCase):
    def setUp(self) -> None:
        # TODO: multi-thread 환경에서도 문제없이 통과하도록 수정
        clear_media_folder()

    @todo_test()
    def test(self):
        file = self.get_uploaded_file(file_path="base/apps.py")
        file_ins = File.objects.create(file=file)
        file2 = self.get_uploaded_file(file_path="base/utils.py")
        file_ins2 = File.objects.create(file=file2)

        assert file_ins.file_hash != file_ins2.file_hash
        assert file_ins.name == file.name
        assert file_ins.size == file.size
        assert compute_file_hash(file_ins.file.open()) == compute_file_hash(file.open())
        assert compute_file_hash(file_ins.file) == compute_file_hash(file.open())
        assert File.objects.get(file_hash=compute_file_hash(file.open())) is file_ins
        assert File.objects.get(file_hash=compute_file_hash(file2.open())) is file_ins2
        with file.open() as f1, file_ins.file.open() as f2:
            for v1, v2 in zip(f1, f2):
                assert v1 == v2


class FileHashTest(BaseTestCase):
    def setUp(self) -> None:
        # TODO: multi-thread 환경에서도 문제없이 통과하도록 수정
        clear_media_folder()

    @todo_test()
    def test2(self):
        file = self.get_uploaded_file("base/apps.py")
        instance = File.objects.create(file=file)
        assert instance.uname
        assert instance.name == "apps.py"
        assert instance.ext == "py"
        assert instance.file_hash == "08f44f78f5f7d68e"

        file2 = self.get_uploaded_file("base/_types.py")
        file_hash = compute_file_hash(file2.file)
        file_hash2 = compute_file_hash(file2.open())
        assert file_hash == file_hash2
        with self.assertRaises(File.DoesNotExist):
            instance2 = File.objects.get(file_hash=file_hash)
        instance2 = File.objects.create(file=file2.open())

        assert instance.uname != instance2.uname
        assert instance2.name == "_types.py"
        assert instance2.ext == "py"
        assert instance2.file_hash == file_hash
