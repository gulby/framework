from base.tests import BaseTestCase, only_full_test
from base.models import DummyActor

from human.models import Human, LoginID
from human.exceptions import PasswordNotMatchException


class ActorLoginTest(BaseTestCase):
    def given(self):
        # Human 생성
        human1 = Human()
        human2 = Human()
        human3 = Human()
        human1.name = "1윤재"
        human2.name = "2윤재"
        human3.name = "3윤재"
        human1.save()
        human2.save()
        human3.save()
        assert human1
        assert human2
        assert human3

        # UserId 생성
        user_loginid1 = LoginID()
        user_loginid2 = LoginID()
        user_loginid3 = LoginID()
        user_loginid1.uname = "yoonjae1"
        user_loginid1.set_password("111111")
        user_loginid2.uname = "yoonjae2"
        user_loginid2.set_password("222222")
        user_loginid3.uname = "yoonjae3"
        user_loginid3.set_password("333333")
        user_loginid1.save()
        user_loginid2.save()
        user_loginid3.save()
        assert user_loginid1
        assert user_loginid2
        assert user_loginid3

        # Actor 생성
        employee1 = DummyActor.objects.create()
        employee2 = DummyActor.objects.create()
        employee3 = DummyActor.objects.create()

        assert employee1
        assert employee2
        assert employee3

        user_loginid1.human = human1
        user_loginid1.save()
        employee1.human = human1
        employee1.save()
        user_loginid2.human = human2
        user_loginid2.save()
        employee2.human = human2
        employee2.save()
        user_loginid3.human = human3
        user_loginid3.save()
        employee3.human = human3
        employee3.save()

    @only_full_test()
    def test(self):
        # 로그인 시도
        user_loginid1 = LoginID.objects.get(uname="yoonjae1")
        assert user_loginid1.authenticate("111111")
        assert user_loginid1.human.name == "1윤재"

    @only_full_test()
    def test2(self):
        user_loginid2 = LoginID.objects.get(uname="yoonjae2")
        assert user_loginid2.authenticate("222222")
        assert user_loginid2.human.name == "2윤재"

    @only_full_test()
    def test3(self):
        user_loginid3 = LoginID.objects.get(uname="yoonjae3")
        assert user_loginid3.authenticate("333333")
        assert user_loginid3.human.name == "3윤재"

    @only_full_test()
    def test4(self):
        user_loginid1 = LoginID.objects.get(uname="yoonjae1")
        assert user_loginid1.authenticate("111111")
        assert user_loginid1.human.name == "1윤재"

        user_loginid2 = LoginID.objects.get(uname="yoonjae2")
        # with self.assertRaises(AssertionError):
        # yoonjae1 으로 로그인한 상태에서 yoonjae2 로 로그인 시 에러나는지 확인하는 테스트
        # Human.authenticate() 가 수정되어 이제는 더이상 에러가 발생하지 않음
        user_loginid2.authenticate("222222")


class ActorLoginTest1(BaseTestCase):
    def given(self):
        human = Human.objects.create()
        loginid = LoginID()
        loginid.uname = "test_id"
        loginid.set_password("123456n")
        loginid.human = human
        loginid.save()

    @only_full_test()
    def test(self):
        user_loginid = LoginID.objects.get(uname="test_id")
        assert user_loginid.login_id == "test_id"
        assert user_loginid.authenticate("123456n")
        user_loginid.set_password("n123456")
        assert user_loginid.authenticate("n123456")
        user_loginid.set_password("")
        with self.assertRaises(PasswordNotMatchException):
            assert user_loginid.authenticate("")
        user_loginid.set_password("n123456")
        assert user_loginid.authenticate("n123456")
        user_loginid.set_password("n123456")
        assert user_loginid.authenticate("n123456")
        user_loginid.set_password(" ")
        assert user_loginid.authenticate(" ")
        user_loginid.set_password(None)
        user_loginid.save()
        with self.assertRaises(PasswordNotMatchException):
            assert user_loginid.authenticate(None)
