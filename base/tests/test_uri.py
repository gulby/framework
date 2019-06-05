from base.tests import BaseTestCase
from base.models.samples import Dummy
from base.fields import ForceChanger
from base.transaction import TransactionManager
from base.enums import Status
from base.exceptions import DuplicateUriException


class UriTest(BaseTestCase):
    def test_uri_property(self):
        uri = "/uri/1/"
        assert Dummy.objects.filter(uri=uri).count() == 0
        instance = Dummy()
        assert instance.uri is None
        assert instance.computed["uri"] is None
        assert not instance.computed_uri_hash
        with ForceChanger(instance):
            instance.uri = uri
        assert instance.uri == uri
        assert instance.computed["uri"] == uri
        assert instance.computed_uri_hash
        instance.save()
        assert Dummy.objects.filter(uri=uri).count() == 1
        with ForceChanger(instance):
            instance.uri = None
        assert instance.uri is None
        assert instance.computed_uri_hash is None

        uname = "gulby@naver.com"
        instance.uname = uname
        assert instance.uname == uname
        assert instance.uri == "/uri/base/dummy/{}/".format(uname)
        assert instance.computed_uri_hash is not None
        instance.save()
        tran = TransactionManager.get_transaction()
        instance._syncdb_update(tran)
        query = str(Dummy.objects.filter(uname=uname).query)
        assert query.find("computed_uri_hash") != -1
        assert Dummy.objects.filter(uname=uname).count() == 1
        assert Dummy.objects.filter(uname="asdf").count() == 0
        with self.assertRaises(AssertionError):
            instance.uri = "asdf"

        other_uname = "yjlee@jihaepat.com"
        instance.uname = other_uname
        assert instance.uname == other_uname
        instance.uname = uname
        assert instance.uname == uname
        instance2 = Dummy()
        instance2.uname = other_uname
        assert instance2.uname == other_uname
        assert instance2.status == Status.NEW
        with self.assertRaises(DuplicateUriException):
            instance2.uname = uname
        assert instance2.status == Status.INVALID
        with self.assertRaises(AssertionError):
            instance2.uname = other_uname
        with self.assertRaises(AssertionError):
            instance2.save()
        instance.save()


class UriTest2(BaseTestCase):
    def test(self):
        instance = Dummy()
        instance.uname = "/mnt/raw/"
        assert instance.uri == "/uri/base/dummy/mnt/raw/"
