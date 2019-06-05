from base.tests import BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy, Nothing
from base.transaction import Transaction, TransactionManager


class ModelManagerTest(BaseNoTransactionTestCase):
    def test_manager_get(self):
        with Transaction() as tran:
            self.assertEqual(Model.objects.count(), 0)
            instance = Dummy()
            self.assertEqual(Model.objects.count(), 0)
            instance.save()
        with tran:
            self.assertEqual(Model.objects.count(), 1)
            instance2 = Model.objects.get(id=instance.id)
            assert id(instance) == id(instance2)
            TransactionManager._clear()
            instance3 = Model.objects.get(id=instance.id)
            assert instance == instance3
            assert id(instance) != id(instance3)

    def test_get_queryset(self):
        with Transaction():
            instance = Dummy.objects.create()
        assert Model.objects.get(id=instance.id)
        assert Dummy.objects.get(id=instance.id)
        with self.assertRaises(Model.DoesNotExist):
            Nothing.objects.get(id=instance.id)
