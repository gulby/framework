from base.tests import BaseTestCase
from base.descriptors import Subfield, DictSubfield, ListSubfield, ValueSubfield
from base.models.actor import Actor
from base.models import Dummy


class DescriptorTest2(BaseTestCase):
    def test(self):
        test_owner = Actor.objects.create(name="hyunsoo")
        subfield = Actor.owner
        subfield.field_name = "data"
        assert isinstance(subfield, Subfield)
        assert isinstance(subfield, ValueSubfield)
        assert subfield.field_name.__str__() == "data"
        assert subfield.field_name.__repr__() == "'data'"


class DescriptorTest3(BaseTestCase):
    def test(self):
        dummy01 = Dummy.objects.create()

        assert dummy01.default_dict_test.default_test == "test"


class DictSubfieldDescriptorTest(BaseTestCase):
    def test(self):
        with self.assertRaises(NotImplementedError):
            dict_field = DictSubfield("test", {"test_field": str}, check="check")

        dummy1 = Dummy.objects.create(default_dict_test={"default_test": "dummy"})
        dummy2 = Dummy.objects.create(default_dict_test={"default_test": "dummy"})

        assert dummy1.default_dict_test == dummy2.default_dict_test

        with self.assertRaises(NotImplementedError):
            assert dummy1.default_dict_test == "dummy"


class ListSubfieldDescriptorTest(BaseTestCase):
    def test(self):
        with self.assertRaises(NotImplementedError):
            list_subfield = ListSubfield("test_list_field", [], check="check")
        dummy1 = Dummy.objects.create(monitors=[1, 2, 3])
        dummy2 = Dummy.objects.create(monitors=[1, 2, 3])

        assert dummy1.monitors == dummy2.monitors

        with self.assertRaises(NotImplementedError):
            assert dummy1.monitors == "monitors"

        with self.assertRaises(AssertionError):
            dummy1.monitors = 1234

        with self.assertRaises(AssertionError):
            dummy2.monitors = [None, "str"]
