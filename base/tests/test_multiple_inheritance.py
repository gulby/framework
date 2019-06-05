from base.tests import BaseTestCase
from base.models.samples import Dummy, DummyContainer


class MultipleInheritanceTest(BaseTestCase):
    def test(self):
        dummy1 = Dummy.objects.create()
        dummy2 = Dummy.objects.create()
        container1 = DummyContainer.objects.create()
        container2 = DummyContainer.objects.create()

        assert Dummy.objects.count() == 2
        assert DummyContainer.objects.count() == 2

        assert dummy1.container is None
