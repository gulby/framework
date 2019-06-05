from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.models.samples import Dummy, DummyContainer
from base.transaction import Transaction
from base.fields import ForceChanger


class CachedQuerySetTest1(BaseTestCase):
    def test_using(self):
        qs = Dummy.objects.all()
        assert len(qs) == 0
        assert qs._result_cache is not None
        qs2 = qs.using("default")
        assert id(qs._result_cache) == id(qs2._result_cache)

    def test_order_by(self):
        qs = Dummy.objects.order_by("-id")
        assert len(qs) == 0
        assert qs._result_cache is not None
        qs2 = qs.order_by("id")
        assert id(qs._result_cache) != id(qs2._result_cache)


class CachedQuerySetTest2(BaseNoTransactionTestCase):
    def test_using(self):
        with Transaction():
            Dummy.objects.create()
            Dummy.objects.create()
            Dummy.objects.create()
            Dummy.objects.create()
        qs = Dummy.objects.all()
        assert len(qs) == 4
        assert qs._result_cache is not None
        qs2 = qs.using("default")
        assert id(qs._result_cache) == id(qs2._result_cache)

    def test_order_by(self):
        with Transaction() as tran:
            instance = Dummy.objects.create()
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.save()
            Dummy.objects.create()
            Dummy.objects.create()
            Dummy.objects.create()
        qs = Dummy.objects.order_by("id")
        assert len(qs) == 4
        assert qs._result_cache is not None
        qs2 = qs.order_by("-id")
        assert id(qs._result_cache) != id(qs2._result_cache)
        assert qs2._result_cache[0] == qs._result_cache[3]
        assert qs2._result_cache[1] == qs._result_cache[2]
        assert qs2._result_cache[2] == qs._result_cache[1]
        assert qs2._result_cache[3] == qs._result_cache[0]

    def test_filter(self):
        with Transaction() as tran:
            instance = Dummy.objects.create()
            with ForceChanger(instance):
                instance.uri = "/uri/1/"
            instance.temp = 1
            instance.monitors.extend([2, 3, 4])
            instance.save()
            Dummy.objects.create()
            other_dummy = Dummy.objects.create()
            dummy = Dummy.objects.create()
            container = DummyContainer.objects.create()
            instance.container = container
            instance.save()
            dummy.container = container
            dummy.save()
            container2 = DummyContainer.objects.create()
            assert instance.version == 0
            assert dummy.version == 0
        assert instance.version == 1
        assert dummy.version == 1

        qs1 = Dummy.objects.all()
        assert len(qs1) == 4
        assert qs1._result_cache is not None
        qs2 = qs1.filter(version=1)
        assert qs2 != qs1
        assert len(qs2) == 4
        qs3 = qs1.filter(version=2)
        assert qs3 != qs1
        assert len(qs3) == 0
        assert len(qs1.filter(version=4)) == 0
        qs5 = DummyContainer.objects.all()
        assert len(qs5) == 2
        assert qs5._result_cache is not None

        # json (DB)
        assert len(Dummy.objects.filter(data__temp=1)) == 1
        assert len(Dummy.objects.filter(data__temp=0)) == 0
        assert len(Dummy.objects.filter(data__monitors__contains=2)) == 1
        assert len(Dummy.objects.filter(data__monitors__contains=1)) == 0
        assert len(Dummy.objects.filter(data__monitors__contains=[2, 3])) == 1

        # json (cache)
        assert len(qs1.filter(data__temp=1)) == 1
        assert len(qs1.filter(data__temp=0)) == 0
        assert len(qs1.filter(data__monitors__contains=2)) == 1
        assert len(qs1.filter(data__monitors__contains=1)) == 0
        assert len(qs1.filter(data__monitors__contains=[2, 3])) == 1


class CachedQuerySetTest3(BaseNoTransactionTestCase):
    def test_transaction1(self):
        qs = Dummy.objects.all()
        qs._fetch_all()
        assert qs._result_cache is not None
        with self.assertRaises(AssertionError):
            with Transaction():
                qs.filter(version=1)

    def test_transaction2(self):
        with Transaction():
            qs = Dummy.objects.all()
            qs._fetch_all()
            assert qs._result_cache is not None
        # django admin 을 위해 Transaction 안에서 생성되었다가 트랜잭션 밖에서 filter 하는 queryset 을 허용
        # template rendering 은 view 함수 밖에서 실행되는 듯 함
        assert len(qs.filter(version=1)) == 0
        with Transaction():
            with self.assertRaises(AssertionError):
                qs.filter(version=1)
