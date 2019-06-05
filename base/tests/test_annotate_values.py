from django.db.models import Count, Sum
from django.contrib.postgres.fields.jsonb import KeyTextTransform as DjangoKeyTextTransform

from base.tests import BaseTestCase, BaseBulkTestCase
from base.models.samples import Dummy
from base.fields import KeyTextTransform, SF


class AnnotateValuesTest(BaseTestCase):
    def test(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=1)

        qs = Dummy.objects.annotate(temp=DjangoKeyTextTransform("temp", "data"))
        assert str(qs.query).find("GROUP BY") == -1
        assert qs._result_cache is None
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.values("temp")
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") == -1
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.annotate(count=Count("*"))
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") != -1
        assert len(qs) == 2
        assert qs._result_cache


class AnnotateValuesTest2(BaseTestCase):
    def test(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=1)

        qs = Dummy.objects.annotate(temp=KeyTextTransform("data__temp"))
        assert str(qs.query).find("GROUP BY") == -1
        assert qs._result_cache is None
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.values("temp")
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") == -1
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.annotate(count=Count("*"))
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") != -1
        assert len(qs) == 2
        assert qs._result_cache


class AnnotateValuesTest3(BaseTestCase):
    def test(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=1)

        qs = Dummy.objects.values("temp")
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") == -1
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.annotate(count=Count("*"))
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") != -1
        assert len(qs) == 2
        assert qs._result_cache


class AnnotateValuesTest4(BaseTestCase):
    def test(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=1)

        qs = Dummy.objects.annotate(temp=SF("temp"))
        assert str(qs.query).find("GROUP BY") == -1
        assert qs._result_cache is None
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.values("temp")
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") == -1
        assert len(qs) == 3
        assert qs._result_cache
        qs = qs.annotate(count=Count("*"))
        assert qs._result_cache is None
        assert str(qs.query).find("GROUP BY") != -1
        assert len(qs) == 2
        assert qs._result_cache


class AnnotateValuesTest5(BaseTestCase):
    def test(self):
        Dummy.objects.create(temp=1, check_test=10)
        Dummy.objects.create(temp=2, check_test=10)
        Dummy.objects.create(temp=1, check_test=20)

        counts = list(
            Dummy.objects.values("temp", "check_test").annotate(count=Count("*")).order_by("temp", "check_test")
        )
        assert len(counts) == 3
        assert counts == [
            {"temp": 1, "check_test": 10, "count": 1},
            {"temp": 1, "check_test": 20, "count": 1},
            {"temp": 2, "check_test": 10, "count": 1},
        ]
        counts = list(Dummy.objects.values("temp").annotate(sum=Sum(SF("check_test"))).order_by("temp"))
        assert len(counts) == 2
        assert counts == [{"temp": 1, "sum": 30}, {"temp": 2, "sum": 10}]


class AnnotateTest(BaseBulkTestCase):
    def test(self):
        Dummy.objects.create()
        assert str(Dummy.objects.annotate(uname=SF("uname")))


class AnnotateTest2(BaseBulkTestCase):
    def test(self):
        Dummy.objects.create()
        with self.assertRaises(AssertionError):
            str(Dummy.objects.annotate(uname=SF("temp")))
        with self.assertRaises(ValueError):
            str(Dummy.objects.annotate(version=SF("temp")))


class AnnotateTest3(BaseBulkTestCase):
    def test(self):
        instance = Dummy.objects.create(temp=1)
        assert str(Dummy.objects.annotate(temp=SF("temp")))
        assert instance.temp == 1
        assert instance.data["temp"] == 1
