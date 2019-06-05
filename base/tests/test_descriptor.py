from django.utils.timezone import now

from base.tests import BaseTestCase, BaseNoTransactionTestCase
from base.models.model import Model
from base.models.samples import Dummy
from base.descriptors.value_subfields import ListSubfieldHelper, DictSubfieldHelper
from base.enums import Status
from base.transaction import Transaction, TransactionManager, get_datetime_from_key, KeyGenerator


class SubfieldDescriptorTest(BaseTestCase):
    def test_subfields(self):
        assert "uri" in Model.subfields["computed"]
        assert "uri" in Dummy.subfields["computed"]

    def test_dict_subfield_dict(self):
        instance = Dummy.objects.create()
        assert isinstance(instance.d, DictSubfieldHelper)
        assert instance.d["a"] is None
        instance.d["a"] = 1
        assert instance.d["a"] == 1
        with self.assertRaises(AssertionError):
            instance.d["a"] = "1"
        assert instance.d.a == 1
        with self.assertRaises(AssertionError):
            instance.d = None
        assert instance.d == {"a": 1, "b": None, "c": None}
        instance.d = {"b": 2}
        assert instance.d == {"a": 1, "b": 2, "c": None}
        with self.assertRaises(AssertionError):
            instance.d = {"none": 3}
        _now = now()
        instance.d["c"] = _now
        assert instance.d == {"a": 1, "b": 2, "c": str(_now)}
        assert instance.d.c == _now
        d2 = instance.d
        with self.assertRaises(AssertionError):
            instance.d = d2
        d3 = instance.data["d"]
        with self.assertRaises(AssertionError):
            instance.d = d3
        instance.save()

    def test_dict_subfield_int(self):
        instance = Dummy.objects.create()
        assert instance.temp is None
        instance.temp = 1
        assert type(instance.temp) is int
        assert instance.temp == 1
        instance.temp = None
        assert instance.temp is None
        instance.save()

    def test_dict_subfield_compute(self):
        instance = Dummy.objects.create()
        assert isinstance(instance.patent, DictSubfieldHelper)
        assert instance.patent == {"raw": None, "plain": None, "html": None}
        instance.patent.update({"raw": "raw", "plain": "plain"})
        assert instance.patent == {"raw": "raw", "plain": "plain", "html": None}
        assert instance.computed["patent_summary"] == {"len": 3, "summary": "r"}
        instance.patent.raw = "kkkkk"
        assert instance.computed["patent_summary"] == {"len": 5, "summary": "k"}
        instance.patent["raw"] = "patent"
        assert instance.computed["patent_summary"] == {"len": 6, "summary": "p"}
        instance.save()

    def test_list_subfield(self):
        instance = Dummy.objects.create()
        assert isinstance(instance.monitors, ListSubfieldHelper)
        assert instance.monitors == []
        instance.monitors.append(1)
        assert instance.monitors == [1]
        instance.monitors.append(2)
        instance.monitors[0] = 0
        assert instance.monitors == [0, 2]
        instance.monitors.remove(2)
        assert instance.monitors == [0]
        instance.monitors = [1]
        assert instance.monitors == [1]
        instance.save()


class ListSubfieldDescriptorTest(BaseTestCase):
    def test(self):
        t0 = now()
        instance = Dummy.objects.create()
        assert isinstance(instance.modified_dates, ListSubfieldHelper)
        assert instance.modified_dates == []
        t1 = now()
        instance.modified_dates.append(t1)
        assert instance.modified_dates == [str(t1)]
        assert instance.modified_dates[0] == t1
        t2 = now()
        instance.modified_dates.append(t2)
        instance.modified_dates[0] = t0
        assert instance.modified_dates == [str(t0), str(t2)]
        assert instance.modified_dates[0] == t0
        assert instance.modified_dates[1] == t2
        instance.modified_dates.remove(t2)
        assert instance.modified_dates == [str(t0)]
        assert instance.modified_dates[0] == t0
        instance.save()


class DatetimeSubfieldDescriptorTest(BaseTestCase):
    def setUp(self):
        tran = TransactionManager.get_transaction()
        self.t_before_tran = get_datetime_from_key(tran.id)

    def test(self):
        tran = TransactionManager.get_transaction()
        # setUp() 시점에 이미 transaction 이 만들어져 있어서 instance.last_transaction_date <= t0 가 성립하지 않을 수 있어 교체
        tran.key_gen = KeyGenerator()
        t00 = now()
        instance = Dummy.objects.create()
        assert instance.last_transaction
        t0 = now()
        assert t00 <= instance.created_date <= t0
        assert self.t_before_tran <= instance.last_transaction_date <= t0
        instance.created_date = t0
        assert instance.created_date == t0
        assert instance.data["created_date"] == str(t0)
        t1 = now()
        instance.created_date = t1
        assert instance.created_date == t1
        assert instance.data["created_date"] == str(t1)
        instance.created_date = None
        assert instance.created_date is None
        assert instance.data["created_date"] is None
        instance.save()


class GetDatetimeFromKeyTest(BaseTestCase):
    def test(self):
        date1 = get_datetime_from_key(31362272886522096)
        date2 = get_datetime_from_key(31362272888619690)
        # 반올림이 아니라 내림 처리가 되는지 확인
        assert date1 == date2


class IntEnumSubfieldDescriptorTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy.objects.create()
            assert instance.test_status is None
            instance.test_status = Status.NORMAL
            assert instance.test_status is Status.NORMAL
            instance.save()
        with Transaction():
            instance = Dummy.objects.get(id=instance.id)
            assert instance.test_status is Status.NORMAL
            instance.test_status = Status.DIRTY
            assert instance._mjson_revert_patch["data"]["test_status"] is Status.NORMAL.value
            assert instance.test_status is Status.DIRTY
            instance.test_status = None
            assert instance.test_status is None
            instance.save()
