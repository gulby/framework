from base.tests import BaseNoTransactionTestCase
from base.transaction import Transaction, ReadonlyTransaction
from base.models import Dummy


class ReadonlyTransactionTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            dummy = Dummy.objects.create()

        with ReadonlyTransaction():
            dummy1 = Dummy.objects.first("-id")
            with self.assertRaises(AssertionError):
                dummy1.temp = 5
