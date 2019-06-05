from base.tests import BaseTestCase
from base.transaction import TransactionManager
from base.exceptions import DuplicateUriException
from human.models import LoginID


class HumanLoginidUriTest(BaseTestCase):
    def test(self):
        tran = TransactionManager.get_transaction()
        instance1 = LoginID()
        instance1.uname = "gulby"
        instance1.save()
        instance2 = LoginID()
        with self.assertRaises(DuplicateUriException):
            instance2.uname = "gulby"
