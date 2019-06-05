from base.tests import BaseTestCase
from server.settings_unittest import IS_CHECK_PERFORMANCE_PROBLEM


class IsCheckPerformanceProblemTest(BaseTestCase):
    def test(self):
        assert IS_CHECK_PERFORMANCE_PROBLEM is True
