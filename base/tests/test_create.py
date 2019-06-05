from base.tests import BaseTestCase
from base.models.actor import Actor
from base.models.samples import Dummy


class CreateWithForeignKeyTest(BaseTestCase):
    def test(self):
        actor = Actor.objects.create()
        instance = Dummy.objects.create(owner=actor)
        assert instance.owner == actor

        manager = actor.possessions
        assert "type__in" not in manager.core_filters
        assert actor.possessions.order_by("-id").first() is instance
