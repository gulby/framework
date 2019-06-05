from datetime import timedelta
from django.core import mail
from django.utils.timezone import now

from base.tests import BaseTestCase, todo_test
from base.utils import send_email

from human.models import Email, Human
from human.exceptions import PasswordExpiredException, PasswordNotMatchException


class EmailSendAndReadDataTest(BaseTestCase):
    def test(self):
        self.assertEqual(len(mail.outbox), 0)
        subject = "Test_Subject"
        body = "Test_Body"
        to = "asas1994g@gmail.com"
        send_email(subject, body, to)
        assert len(mail.outbox) == 1
        subject = "Test_Subject1"
        body = "Test_Body1"
        to = ("asas1994g1@gmail.com", "asas1994g2@gmail.com")
        send_email(subject, body, to)
        assert len(mail.outbox) == 2
        assert mail.outbox[0].subject == "Test_Subject"
        assert mail.outbox[1].subject == "Test_Subject1"
        assert mail.outbox[0].body == "Test_Body"
        assert mail.outbox[1].body == "Test_Body1"
        assert mail.outbox[0].to[0] == "asas1994g@gmail.com"
        assert mail.outbox[1].to[0] == "asas1994g1@gmail.com"
        assert mail.outbox[1].to[1] == "asas1994g2@gmail.com"


class EmailCheckPasswordTest(BaseTestCase):
    @todo_test()
    def test(self):
        # given
        email = Email()
        human = Human.objects.create()
        email.uname = "jihaepat@gmail.com"
        email.human = human
        email.save()

        # when
        assert email.email_address == "jihaepat@gmail.com"
        email.prepare()

        # then
        mail_len = len(mail.outbox)
        email_otp = mail.outbox[mail_len - 1].body.split("OTP:")[1]
        assert email.check_password(email_otp)
        assert email.authenticate(email_otp) == human
        # OTP 는 1회 사용 후 더 이상 사용이 불가해야 함
        with self.assertRaises(PasswordExpiredException):
            email.authenticate(email_otp)
        # redis 에 None 으로 되어 있는 상태에서도 None 으로는 인증 실패가 나야 함
        with self.assertRaises(PasswordNotMatchException):
            email.authenticate(None)


class EmailCheckPasswordTimeoutTest(BaseTestCase):
    @todo_test()
    def test(self):
        # given
        human = Human.objects.create()
        email = Email(human=human)
        email.uname = "jihaepat@gmail.com"
        email.save()

        # when
        assert email.email_address == "jihaepat@gmail.com"
        email.prepare()
        # expire 상황을 흉내
        email.password_expire_date = now()

        # then
        mail_len = len(mail.outbox)
        email_otp = int(mail.outbox[mail_len - 1].body.split("OTP:")[1])
        assert email.check_password(email_otp)
        with self.assertRaises(PasswordExpiredException):
            email.authenticate(email_otp)


class EmailCheckPasswordErrorTest(BaseTestCase):
    def test(self):
        human = Human.objects.create()
        email = Email.objects.create(human=human)
        email.prepare()
        email.password = "1234"
        with self.assertRaises(PasswordNotMatchException):
            email.authenticate("asdf")

        email.password = ""
        with self.assertRaises(PasswordNotMatchException):
            email.authenticate("")

        email.password = "1234"
        email.password_expire_date = now() - timedelta(1)
        with self.assertRaises(PasswordExpiredException):
            email.authenticate("1234")
