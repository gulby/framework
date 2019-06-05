from base.tests import BaseTestCase, ProxyModelTestMixin
from base.models.actor import Actor


class ActorModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Actor
