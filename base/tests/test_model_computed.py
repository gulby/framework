from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.models.samples import Dummy
from base.transaction import Transaction
from base.fields import ForceChanger


class ModelComputedTest(BaseTestCase):
    def test_set_computed_uri_hash(self):
        instance = Dummy()
        with self.assertRaises(AssertionError):
            instance.computed_uri_hash = "/uri/0/"
        assert instance.computed_uri_hash is None
        with ForceChanger(instance):
            instance.uri = "/uri/1/"
        with self.assertRaises(AssertionError):
            instance.computed_uri_hash = None
        assert instance.computed_uri_hash is not None

    def test_computed_framework(self):
        instance = Dummy()
        with self.assertRaises(AssertionError):
            instance.computed = {}
        assert instance.computed_uri_hash is None
        with ForceChanger(instance):
            instance.uri = "/uri/1/"
        uri_hash_1 = instance.computed_uri_hash
        assert uri_hash_1
        assert instance.computed["uri_hash"] == str(uri_hash_1)
        with ForceChanger(instance):
            instance.uri = "/uri/2/"
        uri_hash_2 = instance.computed_uri_hash
        assert uri_hash_2
        assert instance.computed["uri_hash"] == str(uri_hash_2)
        assert uri_hash_1 != uri_hash_2


class ModelComputedTest2(BaseNoTransactionTestCase):
    def test_computed(self):
        with Transaction():
            instance = Dummy.objects.create()
            self.assertDictContainsSubset({"patent_summary": {"len": None, "summary": None}}, instance.computed)
            instance.patent = {"raw": "Patent is good~"}
            self.assertDictContainsSubset({"patent_summary": {"len": 15, "summary": "P"}}, instance.computed)
            instance.save()
        with Transaction():
            instance2 = Dummy.objects.get(id=instance.id)
            assert id(instance2) != id(instance)
            self.assertDictContainsSubset({"patent_summary": {"len": 15, "summary": "P"}}, instance.computed)
