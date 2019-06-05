from base.tests import BaseNoTransactionSpecTestCase
from base.transaction import Transaction
from base.models import Dummy


class NoTransactionTest(BaseNoTransactionSpecTestCase):
    def test(self):
        temp = self.input_from_user(1)
        name = self.input(example="test")
        with Transaction():
            instance = Dummy.objects.create(temp=temp, name=name)
        assert instance.temp == temp
        assert instance.name == name

        self.render("{} {}".format(name, temp))
        self.print("{} {}".format(name, temp))

        with self.assertRaises(AssertionError):
            instance = Dummy.objects.create(name="test")
