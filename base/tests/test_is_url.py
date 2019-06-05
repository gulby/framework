from base.tests import BaseTestCase
from base.utils import is_url


class URLTest(BaseTestCase):
    def test(self):
        url = "http://www.naver.com"
        url2 = "https://www.naver.com"

        assert is_url(url) is True
        assert is_url(url2) is True
