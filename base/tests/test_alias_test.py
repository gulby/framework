from base.tests import BaseTestCase
from base.models import Dummy, SubDummy, DummyContainer, DummyContainer2
from base.types import Type


class AliasTest(BaseTestCase):
    def test(self):
        instance = Dummy.objects.create(alias_test1="test", alias_test2="test2")
        assert instance.alias_test1 == "test"
        assert instance.wrapper_alias == "test"
        assert instance.alias_test2 == "test2"
        assert instance.wrapper_alias2 == "test2"

        sub_dummy = SubDummy.objects.create(sda="test", alias_test2="test2")
        assert sub_dummy.alias_test1 == "test"
        assert sub_dummy.wrapper_alias == "test"
        assert sub_dummy.sda == "test"
        assert sub_dummy.alias_test2 == "test2"
        assert sub_dummy.wrapper_alias2 == "test2"

    def test2(self):
        dummy_container = DummyContainer.objects.create()
        dummy_container2 = DummyContainer.objects.create()
        sub_dummy_container = DummyContainer2.objects.create()
        sub_dummy_container2 = DummyContainer2.objects.create()
        dummy = Dummy.objects.create(alias_test3=dummy_container, alias_test4=dummy_container2)
        sub_dummy = SubDummy.objects.create(alias_test3=sub_dummy_container, alias_test4=sub_dummy_container2)

        assert dummy.alias_test3 == dummy_container
        assert sub_dummy.alias_test3 == sub_dummy_container

        assert dummy.wrapper_alias3 == dummy_container
        assert sub_dummy.wrapper_alias3 == sub_dummy_container
        assert sub_dummy.wrapper_alias3.type == Type.DummyContainer2

        assert dummy.wrapper_alias4 == dummy_container2
        assert sub_dummy.wrapper_alias4 == sub_dummy_container2

        # 오버라이드해서 SubDummy.alias_test3 의 타입이 Type.DummyContainer2 로 바뀜을 확인함
        with self.assertRaises(AssertionError):
            sub_dummy2 = SubDummy.objects.create(alias_test3=dummy_container)
