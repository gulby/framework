from base.tests import BaseNoTransactionTestCase
from base.transaction import BulkTransaction, _TryException
from base.models.samples import Dummy


class BulkTransactionTest(BaseNoTransactionTestCase):
    def test(self):
        with BulkTransaction() as tran:
            instance = Dummy.objects.create()
            instance.temp = 1
            instance.save()
            instance2 = Dummy.objects.create()
            assert instance2.id == instance.id + 1
            tran.key_gen.seq = 2000000
            instance3 = Dummy.objects.create()
            assert instance3.id == instance.id - 1 + 2000000


class BulkTransactionTest2(BaseNoTransactionTestCase):
    def test(self):
        assert Dummy.objects.count() == 0
        with self.assertRaises(_TryException):
            with BulkTransaction() as tran:
                tran.MAX_INSTANCES_SIZE = 2
                assert len(tran.instances) == 0
                assert Dummy.objects.count() == 0
                Dummy.objects.create()
                assert len(tran.instances) == 1
                assert Dummy.objects.count() == 1
                Dummy.objects.create()
                assert len(tran.instances) == 2
                assert Dummy.objects.count() == 2
                Dummy.objects.create()
                assert len(tran.instances) == 1
                assert Dummy.objects.count() == 3
                raise _TryException
        assert Dummy.objects.count() == 0
