from string import ascii_lowercase
from base.tests import BaseTestCase
from base.utils import convert_bool


class ConvertBoolTest(BaseTestCase):
    def test(self):
        str_true_bool = ["True", "true", "T", "1", 1, True]
        str_false_bool = ["False", "false", "F", "", "0", 0, False]

        assert [convert_bool(bool_) for bool_ in str_true_bool] == [True] * len(str_true_bool)
        assert [convert_bool(bool_) for bool_ in str_false_bool] == [False] * len(str_false_bool)

        # 알파벳 소문자입니다
        incorrect_values = list(ascii_lowercase)

        assert [convert_bool(bool_) for bool_ in incorrect_values] == [None] * len(incorrect_values)
