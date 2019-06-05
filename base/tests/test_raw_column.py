from base.tests import BaseNoTransactionTestCase
from base.transaction import Transaction
from base.models.samples import Dummy


class RawColumnTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy.objects.create()
        with Transaction():
            with self.assertRaises(AssertionError):
                instance.raw = {"kkk": 1}
