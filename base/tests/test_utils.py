from base.tests import BaseTestCase
from base.utils import findall


class FindAllTest(BaseTestCase):
    def test(self):
        s = "a a a"
        assert list(findall("a", s)) == [0, 2, 4]
        assert list(findall("a a", s)) == [0, 2]

        s = "정신이 정신에 정신의"
        assert list(findall("정신", s)) == [0, 4, 8]
        assert list(findall("의", s)) == [10]
        assert list(findall("굴", s)) == []
