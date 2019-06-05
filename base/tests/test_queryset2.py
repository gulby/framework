from base.tests import BaseTestCase
from base.models.samples import Dummy


class QuerysetTest2(BaseTestCase):
    def setUp(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=3)
        Dummy.objects.create(temp=4)
        Dummy.objects.create(temp=5)

    def test_queryset_in(self):
        dummies = Dummy.objects.filter(temp__in=[1, 2, 3, 4])

        assert dummies.count() == 4

    def test_queryset_get_pk(self):
        dummy_01_id = Dummy.objects.first("id").id
        dummy_05_id = Dummy.objects.first("-id").id
        assert dummy_01_id != dummy_05_id
        dummy_01 = Dummy.objects.get(pk=dummy_01_id)

        assert dummy_01.temp == 1


class QuerysetTest3(BaseTestCase):
    def setUp(self):
        dummy01 = Dummy.objects.create()
        dummy02 = Dummy.objects.create()
        dummy03 = Dummy.objects.create()
        dummy04 = Dummy.objects.create()
        dummy05 = Dummy.objects.create()

        dummy01.patent.raw = "raw_01"
        dummy02.patent.raw = "raw_02"
        dummy03.patent.raw = "raw_03"
        dummy04.patent.raw = "raw_04"
        dummy05.patent.raw = "raw_05"

        dummy01.save()
        dummy02.save()
        dummy03.save()
        dummy04.save()
        dummy05.save()

    def test_queryset_in_with_memory(self):
        all_dummy = Dummy.objects.all()
        all_dummy._fetch_all()
        filter_raw_01 = all_dummy.filter(data__patent__raw__in=("raw_01", "raw_02"))
        assert filter_raw_01.count() == 2

    def test_queryset_in_with_db(self):
        filter_raw_01 = Dummy.objects.filter(data__patent__raw__in=("raw_01", "raw_02"))
        assert filter_raw_01.count() == 2

    def test_queryset_str_in_with_memory(self):
        all_dummy = Dummy.objects.all()
        all_dummy._fetch_all()
        filter_raw_01 = all_dummy.filter(data__patent__raw__in="kkkraw_01kkk")
        assert filter_raw_01.count() == 1

    def test_queryset_str_in_with_db(self):
        filter_raw_01 = Dummy.objects.filter(data__patent__raw__in="kkkraw_01kkk")
        # TODO: filter 에서 list type 에 대해 in 으로 조회가 불가능하도록 처리
        # db 에서 조회가 불가능
        # assert filter_raw_01.count() == 1
