from base.tests import BaseTestCase
from base.models import DummyActor
from human.models import Human, LoginID
from human.exceptions import AuthenticationException


class CheckInTest(BaseTestCase):
    def test(self):
        human_1 = Human.objects.create()
        human_2 = Human.objects.create()
        employee1 = DummyActor.objects.create()
        employee2 = DummyActor.objects.create()
        employee1.human = human_1
        employee1.save()
        human_1_token = Human.get_human_token(human_1)
        assert type(human_1_token) is str
        employee2.human = human_2
        employee2.save()
        human_2_token = Human.get_human_token(human_2)
        assert human_1_token != human_2_token
        assert human_1.check_human_token(human_1_token)
        assert Human.objects.get(id=human_1.id)
        with self.assertRaises(AuthenticationException):
            assert human_2.check_human_token(human_1_token)


class PasswordLoginGetTokenTest(BaseTestCase):
    def test(self):
        user_login_id = LoginID()
        user_login_id.uname = "test_id"
        user_login_id.set_password("123456n")
        human = Human.objects.create()
        user_login_id.human = human
        user_login_id.save()

        user_login_id2 = LoginID.objects.get(uname="test_id")
        assert user_login_id2.login_id == "test_id"
        assert user_login_id2.authenticate("123456n")
