from django.utils.functional import cached_property

from base.json import json_encode
from base.constant import LOOKUP_SEP
from base.fields import ForceChanger
from base.enums import Status
from base.types import Type
from base.agents import Agent

from .value_subfields import ValueSubfield, ListSubfield


class ForeignKeySubfield(ValueSubfield):
    def __init__(self, field_name, subfield_type, create_only=False, null=True, alias=None):
        assert field_name == "data"
        super().__init__(field_name, subfield_type, create_only=create_only, null=null, alias=alias)

    @cached_property
    def related_model(self):
        return self.subfield_type.model

    def __set__(self, instance, value):
        # Agent 변환
        if isinstance(value, Agent):
            value = value.get_master(instance)
        # set
        old = super().__set__(instance, value)
        if old != value:
            # computed field 에 저장
            computed_field_name = self.computed_field_name
            if computed_field_name:
                with ForceChanger(instance):
                    setattr(instance, computed_field_name, value)
                    if instance.status in (Status.NORMAL, Status.WORKING):
                        setattr(instance, "status", Status.DIRTY)
                    instance._mjson_revert_patch[computed_field_name] = json_encode(old)
            else:
                pass
                # TODO : reverse computed subfield 에 저장
        return old

    def convert_filter(self, model, parts, value, lookup_type, raw):
        computed_field_name = self.computed_field_name
        if computed_field_name:
            assert "computed_{}".format(parts[0]) == computed_field_name
            return {"computed_{}__{}".format(LOOKUP_SEP.join(parts), lookup_type): value}
        return super().convert_filter(model, parts, value, lookup_type, raw)


class ReverseForeignKeySubfield(ListSubfield):
    RELATED_NAME_MAPPING = {
        "owner": "computed_possessions",
        "container": "computed_elements",
        "proprietor": "computed_properties",
    }

    def __init__(self, field_name, subfield_type, source_name, alias=None):
        assert field_name == "computed"
        super().__init__(field_name, [subfield_type], default=(), alias=alias)
        self.source_name = source_name

    @cached_property
    def resolved_source_name(self):
        return self.related_model.resolve_subfield_name(self.source_name)

    @cached_property
    def related_model(self):
        return self.subfield_type[0].model

    @cached_property
    def related_subfield(self):
        return getattr(self.related_model, self.resolved_source_name)

    def get_manager(self, instance):
        # TODO : 땜빵 제대로 구현
        source_name, related_model, mapping = (self.resolved_source_name, self.related_model, self.RELATED_NAME_MAPPING)
        if source_name in mapping:
            manager = getattr(instance, mapping[source_name])
            manager.model = related_model
            if related_model != Type.Model.model:
                manager.core_filters["type__in"] = related_model.types
            return manager
        else:
            # TODO : computed subfield 에 값들을 넣고, 이를 활용하여 manager 를 만들어 리턴
            raise NotImplementedError("computed field 가 없는 경우 아직 ReverseForeignKeySubfield 관련 구현이 완료되지 않았음.")

    def __get__(self, instance, owner):
        if not instance:
            return self
        return self.get_manager(instance)

    def __set__(self, instance, value):
        assert value is None, "delete() 를 위한 None 세팅만 허용됩니다."
        manager = self.get_manager(instance)
        old = list(manager.all())
        for related_instance in old:
            related_instance.owner = None
            related_instance.save()
        return old

    def _check_validation(self):
        super()._check_validation()
        assert isinstance(self.related_subfield, ForeignKeySubfield)
        assert issubclass(self.owner, self.related_subfield.related_model)
