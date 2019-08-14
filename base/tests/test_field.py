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
