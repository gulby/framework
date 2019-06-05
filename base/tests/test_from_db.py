from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy
from base.transaction import TransactionManager, Transaction


class ModelCreateTest(BaseTestCase):
    def test(self):
        Dummy.objects.create()
        Dummy.objects.create()
        Dummy.objects.create()
        assert Model.objects.count() == 3
        assert len(Model.objects.filter(type__in=Dummy.types).all()) == 3


class ModelCreateTypeTest(BaseTestCase):
    def test(self):
        instance1 = Dummy.objects.create()
        assert type(instance1) is Dummy
        assert Model.objects.count() == 1
        TransactionManager._clear()
        instance2 = Model.objects.get(type__in=Dummy.types)
        assert id(instance1) != id(instance2)
        assert type(instance2) is Dummy


class PatchJsonFieldTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy()
            del instance.data["temp"]
            instance.save()
            assert "temp" not in instance.data
        assert Dummy.objects.filter(temp=None).count() == 0
        with Transaction():
            instance = Dummy.objects.order_by("-id").first()
            assert "temp" in instance.data
            instance.save()
        assert Dummy.objects.filter(temp=None).count() == 1
