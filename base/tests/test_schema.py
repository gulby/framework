from base.tests import BaseTestCase
from base.models.samples import Dummy


class ModelSchemaTest(BaseTestCase):
    def test_check_schema(self):
        instance = Dummy()
        with self.assertRaises(AttributeError):
            instance.no_subfield = None
        with self.assertRaises(AssertionError):
            instance.d = {"c": 1}
