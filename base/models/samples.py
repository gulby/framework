from datetime import datetime

from base.models import Singleton, Actor
from base.types import Type
from base.enums import Status
from base.models.model import Model
from base.descriptors import (
    ForeignKeySubfield,
    ReverseForeignKeySubfield,
    DictSubfield,
    ValueSubfield,
    ListSubfield,
    DerivedUnameSubfield,
    SubfieldWrapper,
)
from base.utils import convert_bool


class Nothing(Model):
    class Meta:
        proxy = True


class Dummy(Model):
    class Meta:
        proxy = True

    # data subfields
    d = DictSubfield("data", {"a": int, "b": int, "c": datetime})
    temp = ValueSubfield("data", int)
    patent = DictSubfield("data", {"raw": str, "plain": str, "html": str})
    monitors = ListSubfield("data", [int])
    modified_dates = ListSubfield("data", [datetime])
    test_status = ValueSubfield("data", Status)
    default_dict_test = DictSubfield("data", {"default_test": str}, default={"default_test": "test"})
    tax_office_name = ValueSubfield("data", str, default=lambda self: self.get_tax_office_name())
    check_test = ValueSubfield("data", int, default=10, check=lambda v: v >= 2, null=False)
    check_test2 = ValueSubfield("data", int, default=10, check=lambda v: v >= 2)
    wrapper_test1 = ValueSubfield("data", int, alias="wrapper_test2")
    bool_test = ValueSubfield("data", bool, normalize=convert_bool)
    create_only_test = ValueSubfield("data", int, create_only=True)
    alias_test1 = ValueSubfield("data", str, alias="wrapper_alias")
    alias_test2 = ValueSubfield("data", str, alias="wrapper_alias2")
    result_labels = DictSubfield(
        "data", {"STA_y": str, "STA_prob": float, "STA2_y": str, "STA2_prob": float, "TTS_y": str, "TTS_prob": float}
    )
    default_list_test = ListSubfield("data", [int], default=[1, 2, 3, 4, 5])

    # computed subfields
    patent_summary = DictSubfield("computed", {"len": int, "summary": str})
    # default 에 callable 을 넘길 때는 self 를 인자로 받는 lambda 로 싸서 넘김
    monitors_count = ValueSubfield("computed", int, default=lambda self: self.compute_monitors_count())

    # relational subfields
    container = ForeignKeySubfield("data", Type.DummyContainer)
    group = ForeignKeySubfield("data", Type.Dummy)
    members = ReverseForeignKeySubfield("computed", Type.Dummy, "group")
    proprietor = ForeignKeySubfield("data", Type.DummyContainer)
    alias_test3 = ForeignKeySubfield("data", Type.DummyContainer, alias="wrapper_alias3")
    alias_test4 = ForeignKeySubfield("data", Type.DummyContainer, alias="wrapper_alias4")

    def compute_patent_summary(self):
        patent = self.patent
        if not patent:
            return {}
        raw = self.patent.raw
        return {"len": raw and len(raw), "summary": raw and raw[0]}

    def compute_monitors_count(self):
        return len(self.monitors)

    def get_tax_office_name(self):
        return "동수원세무서"

    def onchange_wrapper_test2(self, old, new):
        self.__dict__["_wrapper_test"] = True


class SingletonDummy(Singleton):
    class Meta:
        proxy = True


class DummyContainer(Model):
    class Meta:
        proxy = True

    # data subfields
    uname = DerivedUnameSubfield(default=lambda self: self.uname_source)
    uname_source = ValueSubfield("data", str)

    # relational subfields
    dummies = ReverseForeignKeySubfield("computed", Type.Dummy, "container")
    properties = ReverseForeignKeySubfield("computed", Type.Dummy, "proprietor")


class DummyContainer2(DummyContainer):
    class Meta:
        proxy = True


class SubDummy(Dummy):
    class Meta:
        proxy = True

    alias_test1 = ValueSubfield("data", str, alias="sda")
    alias_test3 = ForeignKeySubfield("data", Type.DummyContainer2, alias="wrapper_alias3")
    alias_test4 = ForeignKeySubfield("data", Type.DummyContainer2)


class DummyActor(Actor):
    class Meta:
        proxy = True

    container = ForeignKeySubfield("data", Type.User, alias="user")
    human = SubfieldWrapper("container")
