from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy
from base.transaction import Transaction
from base.fields import ForceChanger


class ModelCreateTest(BaseNoTransactionTestCase):
    def test_create_db(self):
        with Transaction():
            self.assertEqual(Model.objects.count(), 0)
            instance = Dummy()
            self.assertEqual(Model.objects.count(), 0)
            instance.save()
            self.assertEqual(Model.objects.count(), 1)
            assert instance.version == 1
        self.assertEqual(Model.objects.count(), 1)
        assert instance.version == 1

    def test_create_db2(self):
        with Transaction():
            assert Model.objects.count() == 0
            instance = Dummy()
            assert Model.objects.count() == 0
            assert instance.version == 0
            instance.save()
            assert Model.objects.count() == 1
            assert instance.version == 1
        assert Model.objects.count() == 1
        assert instance.version == 1

    def test_create_db3(self):
        with Transaction():
            assert Model.objects.count() == 0
            instance = Dummy()
            assert Model.objects.count() == 0
            instance.save()
            assert Model.objects.count() == 1
            assert instance.version == 1
            with ForceChanger(instance):
                instance.uri = "/uri/2/"
            instance.save()
            assert instance.version == 1
        assert instance.version == 2

    def test_create_db4(self):
        with Transaction():
            assert Model.objects.count() == 0
            instance = Dummy()
            assert Model.objects.count() == 0
            instance.save()
            assert Model.objects.count() == 1
            assert instance.version == 1
            with ForceChanger(instance):
                instance.uri = "/uri/2/"
            instance.save()
            assert instance.version == 1
            instance.delete()
            assert Model.objects.count() == 0
            assert instance.version == 2
        assert instance.version == 2


class ModelIDTest(BaseTestCase):
    def test_id(self):
        instance = Dummy()
        self.assertIsNotNone(instance.id)
        old_id = instance.id
        instance.save()
        self.assertIsNotNone(instance.id)
        new_id = instance.id
        self.assertEqual(old_id, new_id)

    def test_id2(self):
        instance = Dummy()
        assert instance.id is not None
        old_id = instance.id
        instance.save()
        assert instance.id is not None
        new_id = instance.id
        assert old_id == new_id
