from base.models.samples import Dummy
from base.tests import BaseTestCase
from base.fields import ForceChanger


class JsonFieldGetterTest(BaseTestCase):
    def test_standalone(self):
        instance = Dummy()

        uri = "/uri/patent/usa/granted/1/"
        with ForceChanger(instance):
            instance.uri = uri
        assert instance.uri == uri

        instance.d = {"a": 1, "b": 2, "c": None}
        assert instance.d == {"a": 1, "b": 2, "c": None}
        assert instance.d["a"] == 1

        instance.d = {"a": 11}
        assert instance.d == {"a": 11, "b": 2, "c": None}
        instance.d = {"b": 22}
        assert instance.d == {"a": 11, "b": 22, "c": None}
        instance.d = {}
        assert instance.d == {"a": 11, "b": 22, "c": None}

    def test_model_getter(self):
        instance = Dummy()

        uri = "/uri/patent/usa/granted/1/"
        with ForceChanger(instance):
            instance.uri = uri
        assert instance.uri == uri

        instance.d = {"a": 1, "b": 2, "c": None}
        assert instance.d == {"a": 1, "b": 2, "c": None}
        assert instance.d["a"] == 1
