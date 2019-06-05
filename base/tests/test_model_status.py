from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.enums import Status
from base.models.samples import Dummy
from base.fields import ForceChanger
from base.transaction import Transaction


class StatusTest(BaseTestCase):
    def test_route(self):
        s = Status.NEW
        assert s.check_route(Status.NORMAL)
        assert not s.check_route(Status.DIRTY)

    def test_enum(self):
        s1 = Status.NEW
        s2 = Status(2)
        assert s1 == s2
        assert type(s1) == type(s2)
        assert id(s1) == id(s2)

        s3 = Status(10)
        assert s3 != s2
        s4 = Status(s1)
        assert s4 is s1

    def test_status(self):
        instance = Dummy(raw={"patent": "aaa"})
        assert instance.status is Status.NEW
        with ForceChanger(instance):
            instance.uri = "/uri/patent/usa/granted/1/"
        assert instance.uri == "/uri/patent/usa/granted/1/"
        assert instance.status is Status.NEW
        instance.save()
        assert instance.status is Status.NEW
        assert instance.uri == "/uri/patent/usa/granted/1/"

        assert instance.status is Status.NEW
        assert instance.uri == "/uri/patent/usa/granted/1/"
        with ForceChanger(instance):
            instance.uri = "/uri/patent/usa/granted/2/"
        assert instance.uri == "/uri/patent/usa/granted/2/"
        assert instance.status is Status.NEW
        instance.save()
        assert instance.status is Status.NEW
        assert instance.uri == "/uri/patent/usa/granted/2/"

        instance.delete()
        assert instance.status is Status.DELETED
        with self.assertRaises(AssertionError):
            with ForceChanger(instance):
                instance.uri = "/uri/patent/usa/granted/3/"
        assert instance.uri == "/uri/patent/usa/granted/2/"

    def test_save_no_dirty(self):
        instance = Dummy.objects.create()
        instance.save()


class StatusTest2(BaseNoTransactionTestCase):
    def test_status(self):
        with Transaction() as tran:
            instance = Dummy(raw={"patent": "aaa"})
            assert instance.status is Status.NEW
            with ForceChanger(instance):
                instance.uri = "/uri/patent/usa/granted/1/"
            assert instance.uri == "/uri/patent/usa/granted/1/"
            assert instance.status is Status.NEW
            instance.save()
        with tran:
            assert instance.status is Status.NORMAL
            assert instance.uri == "/uri/patent/usa/granted/1/"

            assert instance.status is Status.NORMAL
            assert instance.uri == "/uri/patent/usa/granted/1/"
            with ForceChanger(instance):
                instance.uri = "/uri/patent/usa/granted/2/"
            assert instance.uri == "/uri/patent/usa/granted/2/"
            assert instance.status is Status.DIRTY
            instance.save()
            assert instance.status is Status.DIRTY
            assert instance.uri == "/uri/patent/usa/granted/2/"
            instance.delete()
        with tran:
            assert instance.status is Status.DELETED
            with self.assertRaises(AssertionError):
                with ForceChanger(instance):
                    instance.uri = "/uri/patent/usa/granted/3/"
            assert instance.uri == "/uri/patent/usa/granted/2/"
