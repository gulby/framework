from base.tests import BaseTestCase
from base.models import Dummy, DummyContainer


class PropTest(BaseTestCase):
    def test(self):
        dummy_1 = Dummy.objects.create()
        dummy_2 = Dummy.objects.create()

        dummy_container = DummyContainer.objects.create()

        dummy_1.proprietor = dummy_container
        dummy_1.save()
        dummy_2.proprietor = dummy_container
        dummy_2.save()

        assert Dummy.objects.filter(proprietor=dummy_container).order_by("-id").first() == dummy_2
        assert Dummy.objects.filter(proprietor=dummy_container).order_by("id").first() == dummy_1

        assert dummy_container.properties.order_by("-id").first() == dummy_2
        assert dummy_container.properties.order_by("id").first() == dummy_1
