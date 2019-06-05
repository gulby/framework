from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.models import Dummy, Countable
from base.transaction import Transaction


class CallableDefaultTest(BaseTestCase):
    def test1(self):
        instance = Dummy()
        assert callable(instance.data["tax_office_name"])
        assert instance.tax_office_name == "동수원세무서"
        assert not callable(instance.data["tax_office_name"])
        assert instance.data["tax_office_name"] == "동수원세무서"

    def test2(self):
        instance = Dummy()
        assert callable(instance.computed["monitors_count"])
        assert instance.monitors_count == 0
        assert not callable(instance.computed["monitors_count"])


class NoneDefaultCheckTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Countable()
            assert instance.count is None

        with self.assertRaises(AssertionError):
            with Transaction():
                instance = Countable()
                assert instance.count is None
                instance.save()
