from base.tests import BaseNoTransactionTestCase
from base.models.samples import Dummy
from base.enums import Status
from base.transaction import Transaction


class RevertPatchTest(BaseNoTransactionTestCase):
    def test_revert_patch(self):
        with Transaction() as tran0:
            instance = Dummy.objects.create()
            assert instance.computed["_mjson_revert_patch"] is None
            assert instance._syncdb_required is True
            assert instance.status == Status.NEW
        assert instance.computed["_mjson_revert_patch"] is None
        assert instance._syncdb_required is False
        assert instance.status == Status.NORMAL

        with Transaction() as tran1:
            instance = Dummy.objects.get(id=instance.id)
            instance.temp = 1
            assert instance.computed["_mjson_revert_patch"] is None
            instance.save()
        assert instance.computed["_mjson_revert_patch"] == {
            "data": {"temp": None},
            "computed": {},
            "status": Status.NORMAL,
            "version": 1,
            "last_transaction": tran0.id,
        }

        with Transaction() as tran2:
            instance = Dummy.objects.get(id=instance.id)
            instance.temp = 2
            instance.save()
        assert instance.computed["_mjson_revert_patch"] == {
            "data": {"temp": 1},
            "computed": {},
            "status": Status.NORMAL,
            "version": 2,
            "last_transaction": tran1.id,
        }

        with Transaction() as tran3:
            instance = Dummy.objects.get(id=instance.id)
            instance.patent = {"raw": "raw1", "plain": "plain1", "html": "html1"}
            instance.save()
        assert instance.computed["_mjson_revert_patch"] == {
            "data": {"patent": {"raw": None, "plain": None, "html": None}},
            "computed": {"patent_summary": {"len": None, "summary": None}},
            "status": Status.NORMAL,
            "version": 3,
            "last_transaction": tran2.id,
        }

        with Transaction() as tran4:
            instance = Dummy.objects.get(id=instance.id)
            instance.patent = {"raw": "raw2"}
            instance.save()
        assert instance.computed["_mjson_revert_patch"] == {
            "data": {"patent": {"raw": "raw1", "plain": "plain1", "html": "html1"}},
            "computed": {},
            "status": Status.NORMAL,
            "version": 4,
            "last_transaction": tran3.id,
        }
        assert instance.data["patent"] == {"raw": "raw2", "plain": "plain1", "html": "html1"}

        with Transaction() as tran5:
            instance = Dummy.objects.get(id=instance.id)
            instance.patent = {"raw": "raw3"}
            instance.save()
        assert instance.computed["_mjson_revert_patch"] == {
            "data": {"patent": {"raw": "raw2", "plain": "plain1", "html": "html1"}},
            "computed": {},
            "status": Status.NORMAL,
            "version": 5,
            "last_transaction": tran4.id,
        }
        assert instance.data["patent"] == {"raw": "raw3", "plain": "plain1", "html": "html1"}
