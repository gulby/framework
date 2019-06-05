from base.tests import BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy
from base.transaction import Transaction
from base.exceptions import OptimisticLockException
from base.fields import ForceChanger


class BaseOptimisticLockTest(BaseNoTransactionTestCase):
    def test_optimistic_lock(self):
        with Transaction():
            Dummy().save()

        with Transaction() as tran1:
            instance1 = Model.objects.get(type__in=Dummy.types)
        with Transaction() as tran2:
            instance2 = Model.objects.get(type__in=Dummy.types)

        assert instance1 == instance2
        assert id(instance1) != id(instance2)
        assert instance1.version == instance2.version == 1

        with tran1:
            with ForceChanger(instance1):
                instance1.uri = "/uri/patent/usa/granted/1/"
            assert instance1.version == 1
            instance1.save()
            assert instance1.version == 1
        assert instance1.version == 2

        with self.assertRaises(OptimisticLockException):
            with tran2:
                with ForceChanger(instance2):
                    instance2.uri = "/uri/patent/usa/granted/2/"
                assert instance2.version == 1
                instance2.save()

    def test_take_optimistic_lock(self):
        with Transaction():
            Dummy().save()

        with Transaction() as tran1:
            instance1 = Model.objects.get(type__in=Dummy.types)
        with Transaction() as tran2:
            instance2 = Model.objects.get(type__in=Dummy.types)

        assert instance1 == instance2
        assert id(instance1) != id(instance2)
        assert instance1.optimistic_lock_count == instance2.optimistic_lock_count == 0
        assert instance1.version == instance2.version == 1

        with tran1:
            instance1.take_optimistic_lock()
            assert instance1.optimistic_lock_count == 1
            assert instance1.version == 1
        assert instance1.optimistic_lock_count == 1
        assert instance1.version == 2

        with self.assertRaises(OptimisticLockException):
            with tran2:
                with ForceChanger(instance2):
                    instance2.uri = "/uri/patent/usa/granted/2/"
                assert instance2.optimistic_lock_count == 0
                assert instance2.version == 1
                instance2.save()
