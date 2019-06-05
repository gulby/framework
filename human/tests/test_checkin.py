from base.tests import BaseTestCase
from base.types import Type
from base.models import DummyActor

from human.models import Human
from human.exceptions import CheckinException


class CheckInTest(BaseTestCase):
    def test(self):
        human1 = Human.objects.create()
        employee1 = DummyActor.objects.create(human=human1)
        actor = human1.checkin(Type.DummyActor)
        assert actor == employee1

    def test2(self):
        human1 = Human.objects.create()
        employee1 = DummyActor.objects.create(human=human1)
        employee2 = DummyActor.objects.create(human=human1)
        assert human1.checkin(Type.DummyActor) == employee2

    def test3(self):
        human2 = Human.objects.create()
        human3 = Human.objects.create()
        with self.assertRaises(CheckinException):
            assert human2.checkin(Type.DummyActor)

        with self.assertRaises(CheckinException):
            assert human3.checkin(Type.DummyActor)

    def test4(self):
        human2 = Human.objects.create()
        employee2 = DummyActor.objects.create(human=human2)
        employee2.human = None
        employee2.save()

        with self.assertRaises(CheckinException):
            assert human2.checkin(Type.DummyActor)
