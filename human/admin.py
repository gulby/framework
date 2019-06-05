from base.admin import ModelAdmin, register
from human.models import Human, HumanIdentifier, Email, LoginID


@register(Human)
class HumanAdmin(ModelAdmin):
    pass


@register(HumanIdentifier)
class HumanIdentifierAdmin(ModelAdmin):
    pass


@register(Email)
class EmailAdmin(ModelAdmin):
    pass


@register(LoginID)
class HumanLoginidAdmin(ModelAdmin):
    pass
