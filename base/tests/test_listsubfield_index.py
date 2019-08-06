from base.tests import BaseTestCase
from base.models import Dummy


class ListSubfieldIndexTest(BaseTestCase):
    def test(self):
        instance = Dummy.objects.create()

        assert instance.default_list_test.index(3) == 2

        instance2 = Dummy.objects.create(default_list_test=[10, 2, 5, 90])

        assert instance2.default_list_test.index(90) == 3
        assert instance2.default_list_test.index(2) == 1
