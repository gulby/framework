from base.tests import BaseTestCase
from base.importers import Importer


class ImporterTest(BaseTestCase):
    def test(self):
        path = "/test/path/"
        importer = Importer(path)

        with self.assertRaises(NotImplementedError):
            importer.do()

        with self.assertRaises(NotImplementedError):
            importer.do_item(None)
