from base.enums import Status
from base.transaction import Transaction
from base.tests import BaseNoTransactionTestCase
from base.models import Dummy


class RollBackWorkingTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy.objects.create()
            assert instance.status == Status.NEW
            instance.set_working()
            assert instance.status == Status.WORKING
        assert instance.status == Status.WORKING

        with Transaction():
            instance = Dummy.objects.get(id=instance.id)
            assert instance.status == Status.WORKING
            instance.rollback_working()
            assert instance.status == Status.NORMAL
        assert instance.status == Status.NORMAL
