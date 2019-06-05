from base.tests import BaseTestCase
from base.models import DummyActor

from human.exceptions import PasswordNotMatchException
from human.models import Human, LoginID, Email, HumanIdentifier


class HumanTest(BaseTestCase):
    def test(self):
        human1 = Human.objects.create()
        employee1 = DummyActor.objects.create(human=human1)
        assert employee1.human == human1

        token = human1.get_human_token()
        assert human1.check_human_token(token) is True
        token2 = human1.get_human_token()
        assert human1.check_human_token(token2) is True


class HumanTest2(BaseTestCase):
    def test(self):
        human1 = Human.objects.create(uname="hyunsoo_human")
        login_id = LoginID.objects.create(uname="leehyunsoo_user_login_id", password="password", human=human1)
        employee1 = DummyActor.objects.create(human=human1)
        assert employee1.human == human1

        token = human1.get_human_token()
        assert human1.check_human_token(token) is True
        assert login_id.login_id == "leehyunsoo_user_login_id"
        assert login_id.human == human1

        login_id.password = "new_password"
        login_id.save()

        assert login_id.check_password("new_password") is True
        login_id.set_password("new_password")
        login_id.save()

        assert login_id.check_password("new_password") is True

        login_id2 = LoginID.objects.create(uname="leehyunsoo_user_login_id2", password="password2", human=human1)
        assert login_id2.human == human1

        login_id2.set_password("password2")
        login_id2.save()

        assert login_id2.check_password("password2")

        assert login_id.authenticate("new_password") == login_id2.authenticate("password2")

        with self.assertRaises(PasswordNotMatchException):
            login_id.authenticate("wrong_password")


class HumanTest3(BaseTestCase):
    def test(self):
        human1 = Human.objects.create(uname="hyunsoo_human")
        employee1 = DummyActor.objects.create(human=human1)
        email = Email.objects.create(uname="test@deephigh-is-group-of-Millionaire.com", human=human1)

        assert email.email_address == "test@deephigh-is-group-of-Millionaire.com"
        otp = email.prepare()
        human2 = email.authenticate(otp)
        assert human2 is human1
        assert human1.check_human_token(human2.get_human_token()) is True


class HumanTest4(BaseTestCase):
    def test(self):
        identifier = HumanIdentifier.objects.create()
        identifier.prepare()
