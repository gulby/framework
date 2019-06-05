from base.tests import BaseTestCase, ProxyModelTestMixin
from human.models import Human, HumanIdentifier, Email, LoginID


class HumanModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Human


class HumanIdentifierModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return HumanIdentifier


class EmailModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Email


class HumanLoginidModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return LoginID
