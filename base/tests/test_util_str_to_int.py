from base.tests import BaseTestCase
from base.utils import str_num_to_int_num


class StrNumToIntNumTest(BaseTestCase):
    def test(self):
        assert str_num_to_int_num("1234") == 1234

        with self.assertRaises(AssertionError):
            assert str_num_to_int_num("zxcv") == 0

        # TODO: 주석풀고 통과하도록 구현
        # with self.assertRaises(AssertionError):
        #     assert str_num_to_int_num('1,2,3,4') == 1234
        #     assert str_num_to_int_num('1a2a3a4a') == 1234

        assert str_num_to_int_num("1,234,567,890") == 1234567890
        assert str_num_to_int_num("8,800") == 8800
        assert str_num_to_int_num("100,000") == 100000

        # TODO: 주석풀고 통과하도록 구현
        # assert str_num_to_int_num('100,000.345') == 100000.345
