from django.db import transaction

from base.tests import BaseNoTransactionTestCase, BaseTestCase
from base.models.model import Model
from base.models.samples import Dummy, DummyActor
from base.models.actor import User
from base.transaction import Transaction, TransactionManager, ReadonlyTransaction, TryTransaction, UnitTestTransaction
from base.fields import ForceChanger


class TransactionTest(BaseNoTransactionTestCase):
    def test_transaction(self):
        with Transaction():
            instance = Dummy()
            instance.save()
        assert instance.last_transaction is not None
        old_last_transaction = instance.last_transaction

        with Transaction() as tran1:
            tran2 = TransactionManager.get_transaction()
            assert id(tran1) == id(tran2)
            instance1 = Model.objects.get(id=instance.id)

        # 중간에 다른 트랜잭션에서 치고 들어온 것을 simulation
        with Transaction() as tran3:
            assert tran3 != tran1
            tran4 = TransactionManager.get_transaction()
            assert id(tran3) == id(tran4)
            instance2 = Model.objects.get(id=instance1.id)
            assert instance2 == instance1
            assert id(instance1) != id(instance2)
            with ForceChanger(instance2):
                instance2.uri = "/uri/1/"
            instance2.save()
        assert instance2.last_transaction > old_last_transaction
        old_last_transaction = instance2.last_transaction

        with tran1:
            tran6 = TransactionManager.get_transaction()
            assert id(tran6) == id(tran1)
            assert instance1.computed["uri"] is None

        with Transaction():
            instance3 = Model.objects.get(id=instance1.id)
            assert instance3.computed["uri"] == "/uri/1/"
            instance3.delete()
        assert instance3.last_transaction > old_last_transaction

    def test_no_transaction(self):
        with Transaction():
            Dummy().save()
            Dummy().save()
            Dummy().save()

        assert Model.objects.count() == 3
        assert len(Model.objects.filter(type__in=Dummy.types).all()) == 3
        assert not Model.objects.filter(type__in=Dummy.types).query.order_by
        assert Model.objects.order_by("-id").query.order_by
        assert Model.objects.filter(type__in=Dummy.types).order_by("-id").query.order_by
        instance1 = Model.objects.filter(type__in=Dummy.types).order_by("-id").first()
        assert instance1
        instance2 = Model.objects.get(id=instance1.id)
        assert instance1 == instance2
        assert id(instance1) != instance2

        with self.assertRaises(AssertionError):
            with ForceChanger(instance2):
                instance2.uri = "/uri/2/"

    def test_transaction_checkin(self):
        with Transaction():
            human = User.objects.create()
            actor = DummyActor.objects.create(user=human)
            dummy = Dummy.objects.create()
        with Transaction(checkin_actor=actor) as tran:
            assert tran.checkin_actor == actor
            assert id(tran.checkin_actor) == id(actor)
            assert tran.login_user == human
            assert TransactionManager.get_checkin_actor() == actor
        with self.assertRaises(AssertionError):
            with Transaction(checkin_actor=dummy):
                pass

    def test_transaction_checkin2(self):
        with Transaction():
            human = User.objects.create()
            human2 = User.objects.create()
            actor = DummyActor.objects.create(user=human)
            actor2 = DummyActor.objects.create()
        with Transaction() as tran:
            tran.checkin(actor)
            assert tran.login_user == human
            assert tran.checkin_actor == actor
            tran.logout()
            assert tran.login_user is None
            assert tran.checkin_actor is None
        with Transaction() as tran:
            tran.login(human2)
            assert tran.login_user == human2
            assert tran.checkin_actor is None
            tran.checkin(actor)
            assert tran.login_user == human2
            assert tran.checkin_actor == actor
            tran.checkout()
            assert tran.login_user == human2
            assert tran.checkin_actor is None
            tran.checkin(actor2)
            assert tran.login_user == human2
            assert tran.checkin_actor == actor2
            tran.checkout()
            assert tran.login_user == human2
            assert tran.checkin_actor is None
            human2.logout()
            assert tran.login_user is None
            assert tran.checkin_actor is None

    def test_transaction_immedialtely_all(self):
        with Transaction():
            instance = Dummy()
            instance.save()
        assert instance.last_transaction is not None
        old_last_transaction = instance.last_transaction

        with Transaction() as tran1:
            tran2 = TransactionManager.get_transaction()
            assert id(tran1) == id(tran2)
            instance1 = Model.objects.get(id=instance.id)

        # 중간에 다른 트랜잭션에서 치고 들어온 것을 simulation
        with Transaction() as tran3:
            assert tran3 != tran1
            tran4 = TransactionManager.get_transaction()
            assert id(tran3) == id(tran4)
            instance2 = Model.objects.get(id=instance1.id)
            assert instance2 == instance1
            assert id(instance1) != id(instance2)
            with ForceChanger(instance2):
                instance2.uri = "/uri/1/"
            instance2.save()
        assert instance2.last_transaction > old_last_transaction
        old_last_transaction = instance2.last_transaction

        with tran1:
            tran6 = TransactionManager.get_transaction()
            assert id(tran6) == id(tran1)
            assert instance1.computed["uri"] is None

        with Transaction():
            instance3 = Model.objects.get(id=instance1.id)
            assert instance3.computed["uri"] == "/uri/1/"
            instance3.delete()
        assert instance3.last_transaction > old_last_transaction

    def test_readonly_transaction(self):
        with Transaction():
            Dummy.objects.create()
            Dummy.objects.create()

        with ReadonlyTransaction():
            instance1 = Dummy.objects.first("-id")
            instance2 = Dummy.objects.first("-id")
            assert id(instance1) == id(instance2)

        with self.assertRaises(AssertionError):
            with ReadonlyTransaction():
                Dummy.objects.create()

    def test_nested_transaction(self):
        with Transaction():
            with Transaction():
                Dummy.objects.create()

        with self.assertRaises(AssertionError):
            with ReadonlyTransaction():
                with Transaction():
                    Dummy.objects.create()

        with Transaction():
            with ReadonlyTransaction():
                assert Dummy.objects.count() == 1

        with Transaction():
            with Transaction():
                with Transaction():
                    with Transaction():
                        with Transaction():
                            with ReadonlyTransaction():
                                assert Dummy.objects.count() == 1
                            Dummy.objects.create()
                            assert Dummy.objects.count() == 2
                            with ReadonlyTransaction():
                                assert Dummy.objects.count() == 2
                Dummy.objects.create()
                with Transaction():
                    assert Dummy.objects.count() == 3
            with ReadonlyTransaction():
                assert Dummy.objects.count() == 3
        with ReadonlyTransaction():
            assert Dummy.objects.count() == 3

    def test_try_transaction(self):
        assert Dummy.objects.count() == 0
        with Transaction():
            Dummy.objects.create()
        assert Dummy.objects.count() == 1
        with TryTransaction():
            assert Dummy.objects.create()
        assert Dummy.objects.count() == 1

        with TryTransaction():
            with Transaction():
                assert Dummy.objects.create()
                assert Dummy.objects.count() == 2
            assert Dummy.objects.count() == 2
        assert Dummy.objects.count() == 1

        with self.assertRaises(ZeroDivisionError):
            with TryTransaction():
                a = 1 / 0


class ErrorInNestedTransactionTest(BaseTestCase):
    def test_error_in_nested_transaction(self):
        with self.assertRaises(AssertionError):
            with transaction.atomic():
                Dummy.objects.create()
                raise AssertionError


class ErrorInNestedTransactionTest2(BaseTestCase):
    def test_error_in_nested_transaction(self):
        with self.assertRaises(AssertionError):
            with Transaction():
                Dummy.objects.create()
                raise AssertionError


class ErrorInNestedTransactionTest3(BaseNoTransactionTestCase):
    def test_error_in_nested_transaction(self):
        with self.assertRaises(AssertionError):
            with UnitTestTransaction():
                with Transaction():
                    Dummy.objects.create()
                    raise AssertionError
