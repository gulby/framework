from base.tests import BaseTestCase
from base.utils import safe_multiply_by_log


class SafeMultiplyByLogTest(BaseTestCase):
    def test(self):
        e = 0.00001
        assert safe_multiply_by_log(1) == 1.0
        assert 2.0 - e <= safe_multiply_by_log(2) <= 2.0 + e
        assert 3.0 - e <= safe_multiply_by_log(3) <= 3.0 + e
        assert 14.0 - e <= safe_multiply_by_log(14) <= 14.0 + e
        assert 210.0 - e <= safe_multiply_by_log(14, 15) <= 210.0 + e
        assert 3360.0 - e <= safe_multiply_by_log(14, 15, 16) <= 3360.0 + e
        # log(0) 은 허용되지 않음
        with self.assertRaises(ValueError):
            assert 120.0 - e <= safe_multiply_by_log(*[x for x in range(5)]) <= 120.0 + e

        assert 24.0 - e <= safe_multiply_by_log(*[x for x in range(1, 5)]) <= 24.0 + e
