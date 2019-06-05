from base.utils import now
from base.tests import BaseTestCase
from base.models.samples import Dummy
from base.models.actor import Actor
from base.fields import ForceChanger
from base.types import Type


class ComputedDefaultTest(BaseTestCase):
    def test(self):
        instance = Dummy()
        assert instance.data["owner"] is None
        assert instance.data["creator"] is None
        assert instance.data["container"] is None
        assert instance.computed["members"] == []


class ComputedRelationalFieldTest(BaseTestCase):
    def test(self):
        instance = Dummy()
        instance.d = {"a": 1, "b": 2, "c": now()}
        actor = Actor()
        with ForceChanger(instance):
            assert instance.data["owner"] is None
            instance.owner = actor
            assert instance.data["owner"] == actor.id
            instance.owner = None
            assert instance.data["owner"] is None
            instance.owner = actor
            assert instance.data["owner"] == actor.id


class TypeIsInstanceTest(BaseTestCase):
    def test(self):
        instance = Dummy()
        assert isinstance(instance, Type.Dummy)
        assert not isinstance(instance, Type.DummyContainer)
        assert isinstance(instance, Type.Model)
        assert isinstance(Type.Dummy, Type)


class LinkSaveTest(BaseTestCase):
    def setUp(self):
        self.instance = Dummy.objects.create()
        self.actor = Actor.objects.create()

    def test(self):
        assert self.instance.owner is None
        instance = Dummy.objects.get(id=self.instance.id)
        actor = Actor.objects.get(id=self.actor.id)
        instance.owner = actor
        instance.save()
        assert instance.owner == actor
        assert self.instance.owner == actor
