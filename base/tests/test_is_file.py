from base.tests import BaseTestCase
from base.utils import is_file_path


class IsFileTest(BaseTestCase):
    def test(self):
        path = "/home/hyunsoo/test.txt"
        assert is_file_path(path) is True

        path2 = "/home/hyunsoo/test"
        assert is_file_path(path2) is True

        path3 = "base/test.txt"
        assert is_file_path(path3) is True

        path4 = "test.txt"
        assert is_file_path(path4) is True

        path5 = "http://www.naver.com/test.txt"
        assert is_file_path(path5) is False

        path6 = "ftp://www.naver.com/test.txt"
        assert is_file_path(path6) is False

        string = "<html><p>test</p></html>"
        assert is_file_path(string) is False

        string2 = "<html2><p>test</p></html2>"
        assert is_file_path(string2) is False

        string3 = "test"
        assert is_file_path(string3) is True
