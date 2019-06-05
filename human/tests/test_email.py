from base.tests import BaseTestCase
from base.exceptions import DuplicateUriException
from human.models import Email


class EmailUriTest(BaseTestCase):
    def test(self):
        instance1 = Email()
        instance1.uname = "gulby@naver.com"
        instance1.save()
        instance2 = Email()
        with self.assertRaises(DuplicateUriException):
            instance2.uname = "gulby@naver.com"


class EmailUriTest2(BaseTestCase):
    def test(self):
        instance1 = Email()
        assert instance1.email_address is None
        instance1.uname = "gulby@naver.com"
        instance1.save()
        instance2 = Email()
        with self.assertRaises(DuplicateUriException):
            instance2.uname = "gulby@naver.com"


class EmailSearchByEmailAddressTest(BaseTestCase):
    def test(self):
        instance1 = Email()
        instance1.uname = "gulby@naver.com"
        instance1.save()
        assert Email.objects.filter(uname="gulby@naver.com").count() == 1
        assert Email.objects.filter(uname="jinuny@gmail.com").count() == 0


class EmailCreateTest(BaseTestCase):
    def test(self):
        instance = Email.objects.create(uname="gulby@naver.com")
        assert instance.email_address == "gulby@naver.com"
        assert instance.uri == "/uri/human/email/gulby@naver.com/"
        assert instance.uri_hash is not None
