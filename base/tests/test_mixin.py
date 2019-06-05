from base.tests import ProxyModelTestMixin, BaseTestCase, LogicTestMixin


class ProxyModelTestMixinTest(BaseTestCase):
    def test(self):
        with self.assertRaises(NotImplementedError):
            ProxyModelTestMixin.get_proxy_model_class()


class LogicTestMixinTest(BaseTestCase):
    def test(self):
        with self.assertRaises(NotImplementedError):
            LogicTestMixin.get_logic_class()
