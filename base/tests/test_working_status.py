from base.tests import BaseNoTransactionTestCase
from base.models import Dummy
from base.enums import Status
from base.transaction import Transaction
from base.exceptions import OptimisticLockException


class WorkingStatusTest(BaseNoTransactionTestCase):
    def setUp(self):
        with Transaction():
            Dummy.objects.create()

    def test(self):
        with Transaction() as tran:
            instance = Dummy.objects.first("-id")
            assert instance.status == Status.NORMAL

            instance.set_working()
            assert instance.status == Status.WORKING

            instance.temp = 1
            assert instance.status == Status.DIRTY

            instance.save()
            assert instance.status == Status.DIRTY

        with tran:
            assert instance.status == Status.NORMAL

            instance.delete()
            assert instance.status == Status.DELETED


class WorkingStatusTest2(BaseNoTransactionTestCase):
    def setUp(self):
        with Transaction() as tran:
            instance = Dummy.objects.create()
            assert instance.status == Status.NEW
        assert instance.status == Status.NORMAL

        with tran:
            instance.set_working()
            assert instance.status == Status.WORKING
        assert instance.status == Status.WORKING

        with tran:
            assert instance.status == Status.WORKING
            instance = Dummy.objects.first("-id")
            assert instance
            assert instance.status == Status.WORKING

    def test(self):
        with Transaction():
            instance = Dummy.objects.first("-id")
            assert instance
            assert instance.status == Status.WORKING
            assert Dummy.objects.filter(status=Status.NORMAL).count() == 0
            assert Dummy.objects.filter(status=Status.WORKING).count() == 1


class SetWorkingTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction() as tran1:
            instance = Dummy.objects.create()
            assert instance.version == 0
        assert instance.version == 1

        with Transaction() as tran2:
            instance2 = Dummy.objects.first("-id")
            assert instance2.id == instance.id
            assert instance2.version == 1

        with tran2:
            assert instance2.version == 1
            instance2.set_working()
            assert instance2.version == 2

        with self.assertRaises(OptimisticLockException):
            with tran1:
                instance.temp = 1
                assert instance.version == 1
                instance.save()
                assert instance.version == 1
            assert instance.version == 2


class SetWorkingTest2(BaseNoTransactionTestCase):
    def test(self):
        with Transaction() as tran1:
            instance = Dummy.objects.create()
            assert instance.version == 0
        assert instance.version == 1

        with Transaction() as tran2:
            instance2 = Dummy.objects.first("-id")
            assert instance2.id == instance.id
            assert instance2.version == 1

        with tran1:
            instance.temp = 1
            assert instance.version == 1
            instance.save()
            assert instance.version == 1
        assert instance.version == 2

        with self.assertRaises(OptimisticLockException):
            with tran2:
                assert instance2.version == 1
                instance2.set_working()
