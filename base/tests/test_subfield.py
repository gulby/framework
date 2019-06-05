from base.tests import BaseTestCase
from base.descriptors import Subfield
from base.models import Dummy


class LogicalFieldTest(BaseTestCase):
    def test(self):
        subfield = Subfield("data", None)

        with self.assertRaises(NotImplementedError):
            subfield.__get__("instance", "owner")

        with self.assertRaises(NotImplementedError):
            subfield.__set__("instance", "owner")

        with self.assertRaises(NotImplementedError):
            subfield.convert_filter(None, None, None, None, None)


class SubfieldCheckNullTest(BaseTestCase):
    def test1(self):
        assert Dummy.objects.create(check_test=2)
        with self.assertRaises(AssertionError):
            Dummy.objects.create(check_test=1)

    def test2(self):
        assert Dummy.objects.create(check_test=2)
        with self.assertRaises(AssertionError):
            Dummy.objects.create(check_test=1)

    def test3(self):
        with self.assertRaises(AssertionError):
            Dummy.objects.create(check_test=None)

    def test4(self):
        with self.assertRaises(AssertionError):
            Dummy.objects.create(check_test=None)


class SubfieldCheckNullTest2(BaseTestCase):
    def test1(self):
        assert Dummy.objects.create(check_test2=2)
        with self.assertRaises(AssertionError):
            Dummy.objects.create(check_test2=1)

    def test3(self):
        assert Dummy.objects.create(check_test2=None)


class SubfieldWrapperTest(BaseTestCase):
    def test(self):
        instance = Dummy()
        assert "_wrapper_test" not in instance.__dict__
        instance.wrapper_test1 = 2
        assert instance._wrapper_test is True


class SubfieldWrapperFilterTest(BaseTestCase):
    def setUp(self):
        Dummy.objects.create(wrapper_test1=1)
        Dummy.objects.create(wrapper_test1=2)
        Dummy.objects.create(wrapper_test1=3)

    def test(self):
        assert Dummy.objects.filter(wrapper_test1__lte=2).count() == 2
        assert Dummy.objects.filter(wrapper_test2__lte=2).count() == 2
