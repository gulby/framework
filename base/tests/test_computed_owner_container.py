from base.tests import BaseTestCase
from base.models import Dummy, Actor, User
from human.models import Email
from common.models import Post


class ComputedFieldNameTest(BaseTestCase):
    def test(self):
        assert Dummy.owner.computed_field_name == "computed_owner"
        assert Dummy.container.computed_field_name == "computed_container"
        assert Email.email_address.field_name == "data"
        assert User.actors.field_name == "computed"
        assert Post.resolve_subfield_name("board") == "container"


class ForeignKeyFilterTest(BaseTestCase):
    def setUp(self):
        actor = Actor.objects.create()
        dummy = Dummy.objects.create()
        dummy.owner = actor
        dummy.save()

    def test(self):
        actor = Actor.objects.order_by("-id").first()
        dummy = Dummy.objects.order_by("-id").first()
        assert dummy.owner == actor
        assert list(Dummy.objects.all()) == [dummy]
        qs = Dummy.objects.filter(owner=actor)
        assert qs.order_by("-id").first() == dummy


class ForeignKeyFilterTest2(BaseTestCase):
    def test(self):
        actor = Actor.objects.create()
        assert not Dummy.objects.filter(owner=actor)
        dummy = Dummy.objects.create(owner=actor)
        assert Dummy.objects.get() == dummy
        assert Dummy.objects.get(owner=actor) == dummy

    def test2(self):
        actor = Actor.objects.create()
        dummy = Dummy.objects.create()
        assert not Dummy.objects.filter(owner=actor)
        dummy.owner = actor
        dummy.save()
        assert Dummy.objects.get(owner=actor) == dummy
