from base.models.singleton import Singleton
from base.tests import BaseTestCase, ProxyModelTestMixin, get_uploaded_file
from base.models.samples import Dummy, Nothing, DummyContainer, SubDummy, DummyContainer2, SingletonDummy
from base.models.actor import Actor, User
from base.models.countable import Countable
from base.models.file import Blob, File
from base.fields import ForceChanger
from base.utils import compute_file_hash


class DummyModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Dummy


class SubDummyModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return SubDummy


class NothingModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Nothing


class DummyContainerModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return DummyContainer


class DummyContainer2ModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return DummyContainer2


class ActorModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Actor


class UserModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return User


class CountableModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Countable

    def _get_inited_instance(self):
        cls = self.get_proxy_model_class()
        return cls(count=0)


class BlobModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Blob

    def _get_inited_instance(self):
        cls = self.get_proxy_model_class()
        file = get_uploaded_file("base/apps.py")
        file_hash = compute_file_hash(file)
        instance = cls(uname=file_hash, file=file)
        assert instance.name == "apps.py"
        return instance


class FileModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return File

    def _get_inited_instance(self):
        cls = self.get_proxy_model_class()
        file = get_uploaded_file("base/apps.py")
        instance = cls(file=file)
        assert instance.name == "apps.py"
        return instance

    def test_write(self):
        cls = self.get_proxy_model_class()
        if not cls.__dict__.get("ABSTRACT", False):
            assert cls.objects.count() == 0
            instance = self._get_inited_instance()
            assert cls.objects.count() == 0
            instance.save()
            assert cls.objects.count() == 1
            with ForceChanger(instance):
                instance.optimistic_lock_count += 1
            instance.save()
            assert cls.objects.count() == 1
            instance.delete()
            assert cls.objects.count() == 0
            instance._destroy()
            assert cls.objects.count() == 0
            assert instance.id is None
        else:
            with self.assertRaises(AssertionError):
                cls.objects.create()


class SingletonModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Singleton


class SingletonDummyModelTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return SingletonDummy
