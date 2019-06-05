from base.models import SingletonDummy
from base.tests import BaseTestCase


class SingletonTest(BaseTestCase):
    def test(self):
        instance_1 = SingletonDummy.objects.create(name="test")
        assert instance_1.name == "test"

        singleton = SingletonDummy.get_instance()
        # 2개이상의 객체를 생성하는경우 에러 발생
        with self.assertRaises(AssertionError):
            instance_2 = SingletonDummy.objects.create(name="test2")

        assert SingletonDummy.objects.count() == 1
        assert instance_1 is singleton

        instance_1.name = "test1"
        instance_1.save()
        assert instance_1.name == singleton.name

        singleton.name = "test2"
        singleton.save()
        assert singleton.name == instance_1.name

        assert singleton.uname == "SingletonDummy"
        assert singleton.uri == "/uri/base/singletons/SingletonDummy/"
