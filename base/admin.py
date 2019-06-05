from django.contrib.admin import ModelAdmin as DjangoModelAdmin, register
from django.utils.functional import cached_property
from prettyjson import PrettyJSONWidget

from base.models.model import Model
from base.models.samples import Nothing, Dummy
from base.fields import JSONField


class ModelAdmin(DjangoModelAdmin):
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget(attrs={"initial": "parsed"})}}

    @cached_property
    def readonly_fields(self):
        field_names = Model.field_names
        return tuple(f for f in field_names if f not in ("data", "computed", "raw"))

    @cached_property
    def list_display(self):
        return "__str__", "id", "type", "uri"


@register(Nothing)
class NothingAdmin(ModelAdmin):
    pass


@register(Dummy)
class DummyAdmin(ModelAdmin):
    pass
