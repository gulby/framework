import time
from base.tests import BaseTestCase
from base.utils import DurationChecker, console_log


class DurationCheckerTest(BaseTestCase):
    def test(self):
        checker = DurationChecker()
        with checker:
            time.sleep(0.01)

        assert 0.01 <= checker.duration <= 0.01 + 0.01

    def test_2(self):
        with DurationChecker(render_func_test) as checker:
            time.sleep(0.01)

        assert 0.01 <= checker.duration <= 0.01 + 0.01


def render_func_test(duration):
    console_log("test duration {}".format(duration))
