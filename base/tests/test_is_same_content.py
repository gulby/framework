from base.tests import BaseTestCase
from base.models import Dummy, Actor


class IsSameContentTest(BaseTestCase):
    def test(self):
        dummy1 = Dummy.objects.create(uname="1")
        dummy2 = Dummy.objects.create(uname="2")
        assert dummy1.is_same_content(dummy2)
        dummy1.owner = Actor.objects.create()
        dummy1.save()
        assert dummy1.is_same_content(dummy2)
        dummy2.temp = 2
        dummy2.save()
        assert not dummy1.is_same_content(dummy2)
