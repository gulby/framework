from base.models.samples import Dummy
from base.tests import BaseTestCase


class QuerySetExcludeTest(BaseTestCase):
    def test(self):
        d1 = Dummy.objects.create(temp=1)
        d2 = Dummy.objects.create(temp=2)
        qs = Dummy.objects.exclude(temp=1)
        assert len(qs) == 1
        assert qs.order_by("-id").first() is d2


class QuerySetSubfieldFilterTest(BaseTestCase):
    def setUp(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=3)
        instance = Dummy.objects.create()
        assert instance.temp is None
        assert instance.data["temp"] is None

    def test(self):
        assert Dummy.objects.count() == 4
        assert Dummy.objects.filter(temp__gte=0).count() == 3
        assert Dummy.objects.filter(temp=0).count() == 0
        assert Dummy.objects.filter(temp=None).count() == 1

        assert Dummy.objects.filter(temp__lt=0).exclude(temp=None).count() == 0
        assert Dummy.objects.filter(temp__lt=-1000000000).exclude(temp=None).count() == 0

        # lt 연산자에서는 subfield None 이 무한소로 취급되나, 추가 작업을 하여 문제가 없도록 만들었음
        assert Dummy.objects.filter(temp__lt=0).count() == 0
        assert Dummy.objects.filter(temp__lt=-1000000000).count() == 0

        with self.assertRaises(AssertionError):
            # isnull 연산자에서도 subfield None 은 null 이 아닌 것으로 취급된다 (무한소로 취급된다고 보면 될 듯)
            assert Dummy.objects.filter(temp__isnull=True).count() == 0
            assert Dummy.objects.filter(temp__isnull=False).count() == 4
