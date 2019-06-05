from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.enums import Status
from base.models.samples import Dummy
from base.exceptions import DuplicateUriException
from base.transaction import Transaction


class DeleteDestroyTest(BaseNoTransactionTestCase):
    def test_delete_destroy(self):
        with Transaction():
            assert Dummy.objects.count() == 0
            instance = Dummy.objects.create()
            instance_id = instance.id
            assert instance.status == Status.NEW
            assert Dummy.objects.count() == 1
            assert instance.status == Status.NORMAL
            instance._mark_delete()
            instance._mark_delete()
            instance.delete()
            assert instance.status == Status.DELETED
            assert instance.id is not None
            assert Dummy.objects.count() == 0
            assert Dummy.objects.get_deleted(id=instance_id)
            instance._destroy()
            assert instance.id is None
            assert Dummy.objects.count() == 0
            with self.assertRaises(Dummy.DoesNotExist):
                Dummy.objects.get_deleted(id=instance_id)

    def test_delete_with_new_status(self):
        with Transaction() as tran:
            instance = Dummy()
            assert instance.status == Status.NEW
            instance.delete()
            assert instance.status == Status.DELETED
            assert instance.id is not None
        with tran:
            instance._destroy()
            assert instance.id is None


class DeleteUnameTest(BaseTestCase):
    def setUp(self):
        self.instance = Dummy.objects.create(uname="1")

    def test1(self):
        with self.assertRaises(DuplicateUriException):
            Dummy.objects.create(uname="1")

    def test2(self):
        self.instance.delete()
        assert Dummy.objects.create(uname="1")
