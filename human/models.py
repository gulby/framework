from random import randrange
from datetime import datetime, timedelta
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.utils.timezone import now

from base.types import Type
from base.models import Model, User
from base.descriptors import ValueSubfield, ForeignKeySubfield, ReverseForeignKeySubfield, SubfieldWrapper
from base.utils import encrypt, decrypt
from base.json import json_dumps, json_loads
from base.transaction import TransactionManager

from human.exceptions import PasswordNotMatchException, PasswordExpiredException
from human.exceptions import AuthenticationException


class Human(User):
    class Meta:
        proxy = True

    # relational subfields
    identifiers = ReverseForeignKeySubfield("computed", Type.HumanIdentifier, "human")

    def get_human_token(self):
        assert isinstance(self, Human), "Human 인스턴스여야 합니다."
        mjson_str = json_dumps(self.mjson)
        return encrypt(settings.HUMAN_TOKEN_KEY, mjson_str)

    def check_human_token(self, token):
        token_mjson_str = decrypt(settings.HUMAN_TOKEN_KEY, token)
        token_mjson = json_loads(token_mjson_str)
        if token_mjson["id"] != self.id:
            raise AuthenticationException("Human.id 값이 일치해야 합니다.")
        elif token_mjson != self.mjson:
            raise AuthenticationException("token_mjson 와 self.mjson 가 일치해야 합니다.")
        return True


class HumanIdentifier(Model):
    class Meta:
        proxy = True

    # data subfield
    encrypted_password = ValueSubfield("data", str)
    password_expire_date = ValueSubfield("data", datetime)

    # relational subfields
    container = ForeignKeySubfield("data", Type.Human, alias="human")

    def prepare(self):
        password = None
        return password

    def authenticate(self, password):
        if not self.check_password(password):
            raise PasswordNotMatchException("password 가 일치하지 않습니다.")
        password_expire_date = self.password_expire_date
        if password_expire_date and password_expire_date < now():
            raise PasswordExpiredException("패스워드가 만료되었습니다.")
        human = self.human
        assert isinstance(human, Human)
        tran = TransactionManager.get_transaction()
        if tran.login_user is not None and tran.login_user != human:
            tran.logout()
        tran.login(human)
        return human

    @property
    def password(self):
        raise AssertionError("password 조회는 불가능합니다.")

    @password.setter
    def password(self, v):
        self.set_password(v)

    def set_password(self, password):
        self.encrypted_password = make_password(password)

    def check_password(self, password):
        encrypted_password = self.encrypted_password
        if not password or not encrypted_password:
            raise PasswordNotMatchException("적절한 password 가 아닙니다.")
        return check_password(password, encrypted_password)

    def expire_password(self):
        self.password_expire_date = now() - timedelta(1)
        self.save()


class Email(HumanIdentifier):
    class Meta:
        proxy = True

    # data subfield
    email_address = SubfieldWrapper("uname")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._otp = None

    def prepare(self):
        otp = str(randrange(100000, 1000000))
        self._otp = otp
        self.password = otp
        self.password_expire_date = now() + timedelta(minutes=10)
        self.save()
        # TODO : stock_front_pb/login.py 에 구현함. 추후 view 단 framework 만들 때 추가 고민
        # email_message = "OTP:{}".format(otp)
        # send_email("models_send", email_message, self.uname)
        return otp

    def authenticate(self, password):
        human = super().authenticate(password)
        self.expire_password()
        return human


class LoginID(HumanIdentifier):
    class Meta:
        proxy = True

    # data subfields
    login_id = SubfieldWrapper("uname")
