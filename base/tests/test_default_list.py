from base.tests import BaseTestCase
from base.models import Dummy


class DafaultListSubfieldTest(BaseTestCase):
    def test(self):
        instance = Dummy.objects.create()

        assert instance.default_list_test == [1, 2, 3, 4, 5]
