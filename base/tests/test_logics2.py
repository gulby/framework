from base.tests import BaseTestCase
from base.logics import Logic


class LogicTest(BaseTestCase):
    def test(self):
        logic = Logic()
        with self.assertRaises(NotImplementedError):
            logic.do()
