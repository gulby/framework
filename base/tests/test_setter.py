from copy import deepcopy

from base.models.samples import Dummy
from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.transaction import Transaction
from base.fields import ForceChanger
from base.json import json_encode


class FieldSetterTest(BaseTestCase):
    def test_data_setter(self):
        instance = Dummy()
        old_computed = deepcopy(instance.computed)
        old_data = deepcopy(instance.data)
        with ForceChanger(instance):
            instance.uri = "/uri/1/"
        assert instance.computed["uri"] == "/uri/1/"
        old_computed["uri"] = "/uri/1/"
        old_computed["uri_hash"] = json_encode(instance.uri_hash)
        assert instance.computed == old_computed

        instance.data = {"temp": 1}
        assert instance.data["temp"] == 1
        old_data["temp"] = 1
        assert instance.data == old_data

        instance.data = {"temp": 0}
        assert instance.data["temp"] == 0
        old_data["temp"] = 0
        assert instance.data == old_data

        instance.monitors.append(0)
        assert instance.data["monitors"] == [0]
        old_data["monitors"] = [0]
        assert instance.data == old_data


class FieldSetterTest2(BaseNoTransactionTestCase):
    def test_data_setter(self):
        with Transaction() as tran:
            instance = Dummy.objects.create()
        old_data = deepcopy(instance.data)
        old_computed = deepcopy(instance.computed)
        old_transaction_id = tran.id
        with tran:
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()

        with Transaction():
            instance_old = instance
            instance = Dummy.objects.get(id=instance.id)
            assert id(instance_old) != id(instance)
            assert instance.computed["uri"] == "/uri/1/"
            old_computed["uri"] = "/uri/1/"
            old_computed["uri_hash"] = json_encode(instance.uri_hash)
            old_computed["_mjson_revert_patch"] = {
                "data": {},
                "status": 10,
                "version": 1,
                "computed": {"uri": None, "uri_hash": None},
                "computed_uri_hash": None,
                "last_transaction": old_transaction_id,
            }
            assert instance.computed == old_computed
            instance.data = {"temp": 1}
            instance.save()

        with Transaction():
            instance_old = instance
            instance = Dummy.objects.get(id=instance.id)
            assert id(instance_old) != id(instance)
            assert instance.data["temp"] == 1
            old_data["temp"] = 1
            assert instance.data == old_data
            instance.data = {"temp": 0}
            instance.save()

        with Transaction():
            instance_old = instance
            instance = Dummy.objects.get(id=instance.id)
            assert id(instance_old) != id(instance)
            assert instance.data["temp"] == 0
            old_data["temp"] = 0
            assert instance.data == old_data
            instance.monitors.append(0)
            instance.save()

        with Transaction():
            instance_old = instance
            instance = Dummy.objects.get(id=instance.id)
            assert id(instance_old) != id(instance)
            assert instance.data["monitors"] == [0]
            old_data["monitors"] = [0]
            assert instance.data == old_data


class JsonFieldSetterTest(BaseTestCase):
    def test_standalone(self):
        uri = "/uri/patent/usa/granted/1/"
        instance = Dummy()

        with ForceChanger(instance):
            instance.uri = uri
        self.assertDictContainsSubset({"uri": uri}, instance.computed)
        instance.data["temp"] = None
        instance.temp = 0
        self.assertDictContainsSubset({"temp": 0}, instance.data)

        with self.assertRaises(AttributeError):
            del instance.temp
        with self.assertRaises(TypeError):
            del instance["temp"]

        instance.patent.update({"raw": "ttt", "plain": "ttt"})
        self.assertDictContainsSubset({"patent": {"raw": "ttt", "plain": "ttt", "html": None}}, instance.data)
        instance.patent.update({"raw": "u", "html": "u"})
        self.assertDictContainsSubset({"patent": {"raw": "u", "plain": "ttt", "html": "u"}}, instance.data)

        instance.data["monitors"] = []
        instance.monitors.append(1)
        self.assertDictContainsSubset({"monitors": [1]}, instance.data)
        instance.monitors.append(2)
        self.assertDictContainsSubset({"monitors": [1, 2]}, instance.data)

    def test_model_setter(self):
        uri = "/uri/patent/usa/granted/1/"
        instance = Dummy()

        with ForceChanger(instance):
            instance.uri = uri
        self.assertDictContainsSubset({"uri": uri}, instance.computed)
        instance.temp = 1
        self.assertDictContainsSubset({"temp": 1}, instance.data)

        with self.assertRaises(AttributeError):
            del instance.temp
        with self.assertRaises(TypeError):
            del instance["temp"]

        instance.patent.update({"raw": "ttt", "plain": "ttt"})
        self.assertDictContainsSubset({"patent": {"raw": "ttt", "plain": "ttt", "html": None}}, instance.data)
        instance.patent.update({"raw": "u", "html": "u"})
        self.assertDictContainsSubset({"patent": {"raw": "u", "plain": "ttt", "html": "u"}}, instance.data)

        instance.data["monitors"] = []
        instance.monitors.append(1)
        self.assertDictContainsSubset({"monitors": [1]}, instance.data)
        instance.monitors.append(2)
        self.assertDictContainsSubset({"monitors": [1, 2]}, instance.data)

    def test_model_setter2(self):
        instance = Dummy(raw={"patent": "aaa"})
        with ForceChanger(instance):
            instance.uri = "/uri/patent/usa/granted/1/"
        assert instance.computed["uri"] == "/uri/patent/usa/granted/1/"
        instance.save()
        assert instance.computed["uri"] == "/uri/patent/usa/granted/1/"

        assert instance.computed["uri"] == "/uri/patent/usa/granted/1/"
        with ForceChanger(instance):
            instance.uri = "/uri/patent/usa/granted/2/"
        assert instance.computed["uri"] == "/uri/patent/usa/granted/2/"
        instance.save()
        assert instance.computed["uri"] == "/uri/patent/usa/granted/2/"

        instance.delete()
        with self.assertRaises(AssertionError):
            with ForceChanger(instance):
                instance.uri = "/uri/patent/usa/granted/3/"
        assert instance.computed["uri"] == "/uri/patent/usa/granted/2/"


class JsonFieldModifyWithNoSetterTest(BaseNoTransactionTestCase):
    def test_model_modfiy_with_no_setter(self):
        with Transaction():
            instance = Dummy.objects.create()
        with self.assertRaises(AssertionError):
            with Transaction():
                instance = Dummy.objects.get(id=instance.id)
                instance.computed["uri"] = "/uri/patent/usa/granted/1/"
                instance.temp = 1
                instance.save()
