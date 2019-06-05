from base.tests import BaseTestCase
from base.models import Dummy


class GetorCreateTest(BaseTestCase):
    def setUp(self) -> None:
        instance = Dummy.objects.create(name="이현수", temp=1)

    def test(self):
        instance, _ = Dummy.objects.get_or_create(name="이현수", temp=3)
        assert instance.temp == 1

        instance, _ = Dummy.objects.get_or_create(name="이현수", temp=3, is_update_if_exist=True)
        assert instance.temp == 3
