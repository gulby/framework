from base.models.model import Model
from base.descriptors import ValueSubfield


class Countable(Model):
    class Meta:
        proxy = True

    # data subfields
    count = ValueSubfield("data", float, null=False, create_only=True)
