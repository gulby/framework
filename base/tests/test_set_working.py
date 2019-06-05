from base.enums import Status
from base.transaction import Transaction
from base.tests import BaseNoTransactionTestCase
from base.models import Dummy


class SetWorkingTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy.objects.create()
            instance.set_working()
            instance.save()

        assert instance.status == Status.WORKING

    def test2(self):
        with Transaction():
            instance = Dummy.objects.create()

        with self.assertRaises(AssertionError):
            instance.set_working()

        assert instance.status == Status.NORMAL
