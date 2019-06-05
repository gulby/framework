from base.descriptors import UnameSubfield
from base.models import Model
from base.utils import console_log
from base.enums import set_invalid_on_exception


class Singleton(Model):
    ABSTRACT = True

    class Meta:
        proxy = True

    uri_format = "/uri/base/singletons/{}/"
    # TODO: DerivedUnameSubfield 에 관한 버그 수정 후 아래의 주석으로 구현 대체
    # uname = DerivedUnameSubfield(default=lambda self: "{}".format(self.__class__.__name__))
    uname = UnameSubfield(null=False)

    @classmethod
    def get_instance(cls, *args, **kwargss):
        instance, _ = cls.objects.get_or_create(*args, **kwargss)
        return instance

    @set_invalid_on_exception
    def on_create(self):
        assert self.__class__.objects.count() == 0, console_log("Singleton 모델의 객체는 1개를 초과할 수 없습니다.")
        self.uname = self.__class__.__name__
