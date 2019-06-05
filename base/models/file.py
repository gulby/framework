import os

from django.core.files.storage import default_storage
from django.core.files.base import File as DjangoFile
from django.utils.functional import cached_property
from django.conf import settings

from base.types import Type
from base.models.model import Model
from base.descriptors import ValueSubfield, UnameSubfield, ForeignKeySubfield, DerivedUnameSubfield
from base.utils import compute_file_hash


def normalize_ext(ext):
    MAPPING = {"jpeg": "jpg"}
    ext = ext.lower() if ext else ""
    return MAPPING.get(ext, ext)


def normalize_file_name(path):
    return path.split("/")[-1]


class File(Model):
    class Meta:
        proxy = True

    uname = DerivedUnameSubfield(default=lambda self: "{}/{}".format(self.blob.id, self.name))
    # data subfields
    name = ValueSubfield("data", str, null=False, create_only=True, normalize=normalize_file_name)

    # relational subfields
    blob = ForeignKeySubfield("data", Type.Blob)

    # computed subfields
    file_hash = ValueSubfield("computed", str, null=False)
    ext = ValueSubfield("computed", str, null=False)
    size = ValueSubfield("computed", int, null=False)

    def __init__(self, *args, **kwargs):
        file = kwargs.pop("file", None)
        super().__init__(*args, **kwargs)
        self._file = None
        if file:
            self.file = file

    def compute_file_hash(self):
        return self.blob.file_hash

    def compute_ext(self):
        return self.blob.ext

    def compute_size(self):
        return self.blob.size

    # property
    @property
    def file(self):
        return self.blob.file

    @file.setter
    def file(self, v):
        assert isinstance(v, DjangoFile)
        if not self.name:
            self.name = v.name

        file_hash = compute_file_hash(v)
        try:
            blob = Blob.objects.get(uname=file_hash)
        except Blob.DoesNotExist:
            blob = Blob.objects.create(uname=file_hash, file=v)
        self.blob = blob

    @cached_property
    def file_path(self):
        return self.blob.file_path

    @property
    def file_abs_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.file_path)


# 직접 사용하지 말고 File 을 통해서만 사용
class Blob(Model):
    class Meta:
        proxy = True

    # data subfields
    uname = UnameSubfield(null=False, create_only=True, alias="file_hash")
    name = ValueSubfield("data", str, null=False, create_only=True, normalize=normalize_file_name)
    ext = ValueSubfield("data", str, null=False, create_only=True, normalize=normalize_ext)
    size = ValueSubfield("data", int, null=False, create_only=True, check=lambda v: v >= 1)

    def __init__(self, *args, **kwargs):
        file = kwargs.pop("file", None)
        super().__init__(*args, **kwargs)
        self._file = None
        if file:
            self.file = file

    def onchange_uname(self, old, new):
        assert old is None
        assert new is not None

    # property
    @property
    def file(self):
        assert self.uname
        if self._file:
            try:
                self._file.open()
            except ValueError:
                self._file = None
        if not self._file:
            self._file = default_storage.open(self.file_path)
        return self._file

    @file.setter
    def file(self, v):
        assert self._file is None
        assert isinstance(v, DjangoFile)
        self._file = v
        assert self.uname, "Blob 세팅 시에는 반드시 file_hash(uname) 을 먼저 세팅해 주어야 합니다."
        self.name = name = v.name
        self.ext = name.split(".")[-1] if "." in name else ""
        self.size = v.size

    @cached_property
    def file_path(self):
        file_hash = self.uname
        assert file_hash
        return "{}/{}/{}".format(file_hash[0:2], file_hash[2:4], file_hash)

    def on_syncdb_insert(self):
        # 단위 테스트에서는 DB 가 리셋되기 때문에 같은 hash 의 파일이 계속 write 시도될 수가 있음. 이를 회피
        if settings.IS_UNIT_TEST and default_storage.exists(self.file_path):
            return
        # DB 에 insert 가 끝난 후 File 을 생성. 에러 발생 시 DB 는 롤백이 되므로
        default_storage.save(self.file_path, self.file)
