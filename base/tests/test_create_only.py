from base.tests import BaseNoTransactionTestCase
from base.models import Dummy, Actor
from base.transaction import Transaction


class CreateOnlyTest(BaseNoTransactionTestCase):
    def setUp(self):
        with Transaction():
            self.instance = Dummy()
            self.instance.create_only_test = 1
            self.instance.save()

    def test1(self):
        with Transaction():
            with self.assertRaises(AssertionError):
                self.instance.create_only_test = 2

    def test2(self):
        with Transaction():
            with self.assertRaises(AssertionError):
                self.instance.creator = Actor.objects.create()
