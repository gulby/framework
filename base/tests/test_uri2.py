from base.enums import Status
from base.exceptions import DuplicateUriException
from base.tests import BaseTestCase
from base.models.samples import Dummy


# uri값을 수정하다가 오류가 발생하면 메모리 상의 uri 값 수정 사항이 롤백이 되지 않는 대신 status 가 INVALID로 바뀌고 이후 더이상 사용이 불가함을 확인하는 테스트
class UriTest2(BaseTestCase):
    def test(self):
        dummy1 = Dummy.objects.create(uname="test/uri1")
        dummy2 = Dummy.objects.create(uname="test/uri2")

        with self.assertRaises(DuplicateUriException):
            dummy2.uname = "test/uri1"
        assert dummy2.uri == "/uri/base/dummy/test/uri1/"

        with self.assertRaises(AssertionError):
            dummy2.save()

        # db 는 변경되지 않기때문에 uri2로 get 하면 dummy2 가 나옴
        assert Dummy.objects.get(uri="/uri/base/dummy/test/uri2/") == dummy2
        # status 가 INVALID 로 바뀌고 더이상 사용 불가
        assert dummy2.status == Status.INVALID
        with self.assertRaises(AssertionError):
            dummy2.uname = "test/uri3"
