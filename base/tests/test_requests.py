from django.test import override_settings

from base.requests import Session, requests_get
from base.tests import BaseTestCase, only_full_test


class RequestsTest(BaseTestCase):
    def test_requests(self):
        with Session() as session:
            res = session.get("http://student.wink.co.kr/health.txt")
            assert res.status_code == 200
            assert res.content == b"OK"

            res = session.get("http://student.wink.co.kr/health.txt")
            assert res.status_code == 200
            assert res.text == "OK"

    @only_full_test()
    @override_settings(REQUESTS_IS_RECORD_RESULT=False, REQUESTS_USE_CACHE=False, REQUESTS_CACHE_FIRST=None)
    def test_requests_not_unittest(self):
        with Session() as session:
            res = session.get("http://student.wink.co.kr/health.txt")
            assert res.status_code == 200
            assert res.content == b"OK"

            res = session.get("http://student.wink.co.kr/health.txt")
            assert res.status_code == 200
            assert res.text == "OK"

    def test_requests_get(self):
        res = requests_get("http://student.wink.co.kr/health.txt")
        assert res.status_code == 200
        assert res.content == b"OK"
        assert res.text == "OK"
