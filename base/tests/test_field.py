from base.json import json_loads
from base.tests import BaseTestCase
from base.models import Dummy


class ListSubfieldDecodeTest(BaseTestCase):
    def test(self):
        arr = "[1,2,3,4,5]"
        assert json_loads(arr) == [1, 2, 3, 4, 5]
        instance = Dummy.objects.create()
        instance.monitors = "[1,2,3,4,5]"
        instance.save()

        assert instance.monitors == [1, 2, 3, 4, 5]


class DictSubfieldDecodeTest(BaseTestCase):
    def test(self):
        dic = '{"raw": "test_raw", "plain": "test_plain", "html": "test_html"}'
        assert json_loads(dic) == {"raw": "test_raw", "plain": "test_plain", "html": "test_html"}
        instance = Dummy.objects.create()
        instance.patent = '{"raw": "test_raw", "plain": "test_plain", "html": "test_html"}'
        instance.save()

        assert instance.patent == {"raw": "test_raw", "plain": "test_plain", "html": "test_html"}
