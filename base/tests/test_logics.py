from base.tests import BaseTestCase
from base.logics import Logic


class LogicsTest(BaseTestCase):
    def test(self):
        logic = Logic()
        with self.assertRaises(NotImplementedError):
            logic.do()
