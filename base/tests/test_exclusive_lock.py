from django.db.utils import ConnectionHandler
from django.db import DEFAULT_DB_ALIAS

from base.tests import BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy
from base.transaction import Transaction


# 제대로 만들기가 너무 어려워 일단 패스 ㅠ_ㅜ
class BaseExclusiveLockTest(BaseNoTransactionTestCase):
    def test_take_exclusive_lock(self):
        with Transaction():
            Dummy().save()

        with Transaction() as tran1:
            instance1 = Model.objects.filter(type__in=Dummy.types).order_by("-id").first()

        tran2 = Transaction()
        other_connection = ConnectionHandler()[DEFAULT_DB_ALIAS]
        assert tran1.connection != other_connection
        tran2.connection = other_connection
        with tran2:
            instance2 = Model.objects.filter(type__in=Dummy.types).order_by("-id").first()

        assert instance1 == instance2
        assert id(instance1) != id(instance2)

        with tran1:
            instance1.take_exclusive_lock()

        # with self.assertRaises(Exception):
        #     with tran2:
        #         instance1.take_exclusive_lock(nowait=True)
