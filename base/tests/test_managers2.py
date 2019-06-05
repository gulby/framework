from base.models.samples import Dummy, DummyContainer
from base.tests import BaseTestCase
from base.enums import Status


class DummyTest(BaseTestCase):
    def test_get_delete(self):
        assert Dummy.objects.count() == 0
        instance = Dummy()
        instance.data["d"] = {"a": 12}
        id = instance.id
        instance.save()
        assert Dummy.objects.count() == 1
        instance.delete()
        assert Dummy.objects.count() == 0
        assert Dummy.objects.get_deleted(id=id)
        assert Dummy.objects.get(id=id).status == Status.DELETED

    def test_related_manager(self):
        container1 = DummyContainer.objects.create()
        container2 = DummyContainer.objects.create()
        instance1 = Dummy.objects.create(container=container1)
        instance2 = Dummy.objects.create()
        assert instance1.optimistic_lock_count == 0
        assert instance2.optimistic_lock_count == 0
        assert container1.dummies.count() == 1
        instance1.container = None
        instance1.save()
        assert container1.dummies.count() == container2.dummies.count()
        instance1.container = container2
        instance1.save()
        instance2.container = container2
        instance2.save()
        assert container2.dummies.count() == 2
        assert instance2.optimistic_lock_count == 0

    def test_compute_patent_summary(self):
        instance = Dummy()
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] is None
        assert instance.patent_summary["summary"] is None
        instance.patent["raw"] = "1234"
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] == 4
        assert instance.patent_summary["summary"] == "1"
        instance.patent["raw"] = None
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] is None
        assert instance.patent_summary["summary"] is None
        instance.patent["raw"] = "None"
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] == 4
        assert instance.patent_summary["summary"] == "N"
        instance.patent["raw"] = "None None None None"
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] == 19
        assert instance.patent_summary["summary"] == "N"
        instance.patent["raw"] = " N"
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] == 2
        assert instance.patent_summary["summary"] == " "
        instance.patent["raw"] = "0"
        Dummy.compute_patent_summary(instance)
        assert instance.patent_summary["len"] == 1
        assert instance.patent_summary["summary"] == "0"
