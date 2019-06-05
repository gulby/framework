from base.tests import BaseNoTransactionTestCase
from base.models.samples import Dummy
from base.transaction import Transaction


class PatchJsonFieldTest(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy()
            # 테스트를 위한 어거지 코드이므로 일반적인 상황에서는 절대 이렇게 하면 안됨
            del instance.data["temp"]
            del instance.computed["monitors_count"]
            instance.save()
            assert "temp" not in instance.data
            assert "monitors_count" not in instance.computed
        assert "temp" not in instance.data
        assert "monitors_count" not in instance.computed

        instance = Dummy.objects.get(id=instance.id)
        assert instance.data["temp"] is None
        assert instance.computed["monitors_count"] == 0


class PatchJsonFieldTest2(BaseNoTransactionTestCase):
    def test(self):
        with Transaction():
            instance = Dummy()
            instance.monitors = [1, 2]
            # 테스트를 위한 어거지 코드이므로 일반적인 상황에서는 절대 이렇게 하면 안됨
            try:
                del instance.computed["monitors_count"]
                del instance.data["temp"]
            except KeyError:
                pass
            instance.save()
            assert "temp" not in instance.data
            assert "monitors_count" not in instance.computed
        assert "temp" not in instance.data
        assert "monitors_count" not in instance.computed

        instance = Dummy.objects.get(id=instance.id)
        assert instance.temp is None
        assert instance.monitors_count == 2
