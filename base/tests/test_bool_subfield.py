from base.tests import BaseNoTransactionTestCase, BaseTestCase
from base.models import Dummy
from base.transaction import Transaction


class BoolSubfieldTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy.objects.create()
            instance.bool_test = 1 == 1
            assert instance.bool_test is True
            assert instance.data["bool_test"] == 1
            instance.bool_test = 1 == 0
            assert instance.bool_test is False
            instance.bool_test = 1
            assert instance.bool_test is True
            instance.bool_test = 0
            assert instance.bool_test is False
            instance.bool_test = "True"
            assert instance.bool_test is True
            instance.bool_test = "False"
            instance.bool_test = False
            assert instance.data["bool_test"] == 0
            assert instance.bool_test is False
            instance.save()
        with Transaction():
            instance = Dummy.objects.order_by("-id").first()
            assert instance.data["bool_test"] == 0
            assert Dummy.objects.filter(bool_test=False).count() == 1
            assert Dummy.objects.filter(bool_test=0).count() == 1
            assert Dummy.objects.filter(bool_test=True).count() == 0
            assert Dummy.objects.filter(bool_test=1).count() == 0


class BoolSubfieldTest2(BaseTestCase):
    def test(self):
        instance = Dummy.objects.create()
        instance.bool_test2 = "False"
        instance.save()
        assert instance.bool_test2 is False

        instance.bool_test2 = True
        assert instance.bool_test2 is True
