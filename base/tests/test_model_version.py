from base.tests import BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy
from base.transaction import Transaction
from base.fields import ForceChanger


class ModelVersionTest(BaseNoTransactionTestCase):
    def test_model_version(self):
        with Transaction():
            instance = Dummy()
            assert instance.version == 0
            with ForceChanger(instance):
                instance.uri = "/uri/patent/usa/granted/1/"
            assert instance.uri == "/uri/patent/usa/granted/1/"
            assert instance.version == 0
            instance.save()
        assert instance.version == 1

        with Transaction():
            instance2 = Model.objects.get(id=instance.id)
            assert instance2.version == 1
            with ForceChanger(instance2):
                instance2.uri = "/uri/patent/usa/granted/2/"
            assert instance2.version == 1
            instance2.save()
        assert instance2.version == 2

        with Transaction() as tran:
            instance3 = Model.objects.get(type__in=Dummy.types)
            assert instance3.version == 2
            tran.remove(instance3)
            instance_db = Model.objects.get(id=instance3.id)
            assert id(instance_db) != id(instance3)
            assert instance_db.version == 2
            instance_db.delete()
            assert instance_db.version == 2
        assert instance_db.version == 3
        assert instance3.version == 2
