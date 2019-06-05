from base.tests import BaseNoTransactionTestCase
from base.models.model import Model
from base.models.history import ModelHistory
from base.models.samples import Dummy
from base.transaction import Transaction
from base.fields import ForceChanger


# TODO : ModelHistory 에 값들이 잘 세팅되는지 확인
class ModelHistoryTest(BaseNoTransactionTestCase):
    def test_fields(self):
        model_column_names = list(Model.column_names)
        model_history_field_names = [field.name for field in ModelHistory._meta.fields]
        model_column_names.extend(["history_id", "history_transaction"])
        model_column_names.sort()
        model_history_field_names.sort()
        assert model_history_field_names == model_column_names

    def test_history1(self):
        with Transaction():
            assert ModelHistory.objects.count() == 0
            instance = Dummy.objects.create()
            assert ModelHistory.objects.count() == 0
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()
            assert ModelHistory.objects.count() == 0
        assert ModelHistory.objects.count() == 1 - 1
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            with ForceChanger(instance):
                instance.uri = "/uri/2/"
            instance.save()
            assert ModelHistory.objects.count() == 1 - 1
        assert ModelHistory.objects.count() == 2 - 1
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            instance.delete()
        assert ModelHistory.objects.count() == 3 - 1
        with Transaction():
            instance = Model.objects.get_deleted(id=instance.id)
            instance._destroy()
            assert ModelHistory.objects.count() == 4 - 1
        assert ModelHistory.objects.count() == 4 - 1

    def test_history2(self):
        with Transaction():
            assert ModelHistory.objects.count() == 0
            instance = Dummy.objects.create()
            assert ModelHistory.objects.count() == 0
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()
            assert ModelHistory.objects.count() == 0
        assert ModelHistory.objects.count() == 1 - 1
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            with ForceChanger(instance):
                instance.uri = "/uri/2/"
            instance.save()
            assert ModelHistory.objects.count() == 1 - 1
        assert ModelHistory.objects.count() == 2 - 1
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            instance.delete()
            assert ModelHistory.objects.count() == 2 - 1
        assert ModelHistory.objects.count() == 3 - 1
        with Transaction():
            instance = Model.objects.get_deleted(id=instance.id)
            instance._destroy()
            assert ModelHistory.objects.count() == 4 - 1
        assert ModelHistory.objects.count() == 4 - 1

    def test_history3(self):
        with Transaction():
            assert ModelHistory.objects.count() == 0
            instance = Dummy.objects.create()
            assert ModelHistory.objects.count() == 0
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()
            assert ModelHistory.objects.count() == 0
        assert ModelHistory.objects.count() == 1 - 1
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            with ForceChanger(instance):
                instance.uri = "/uri/2/"
            instance.save()
            assert ModelHistory.objects.count() == 1 - 1
            instance.delete()
            assert ModelHistory.objects.count() == 1 - 1
        assert ModelHistory.objects.count() == 2 - 1

    def test_history4(self):
        with Transaction():
            assert ModelHistory.objects.count() == 0
            instance = Dummy.objects.create()
            assert ModelHistory.objects.count() == 0
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()
            assert ModelHistory.objects.count() == 0
        assert ModelHistory.objects.count() == 1

    def test_history5(self):
        with Transaction():
            assert ModelHistory.objects.count() == 0
            instance = Dummy.objects.create()
            assert ModelHistory.objects.count() == 0
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()
            assert ModelHistory.objects.count() == 0
        assert ModelHistory.objects.count() == 1 - 1
        with Transaction():
            instance = Model.objects.get(id=instance.id)
            assert ModelHistory.objects.count() == 1 - 1
            with ForceChanger(instance):
                instance.uri = "/uri/2/"
            instance.save()
            assert ModelHistory.objects.count() == 1 - 1
            instance.delete()
            assert ModelHistory.objects.count() == 1 - 1
        assert ModelHistory.objects.count() == 2 - 1
