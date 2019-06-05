from django.utils.functional import cached_property


class Subfield(object):
    def __init__(self, field_name, subfield_type, unique=False):
        assert field_name in ("data", "computed", "sources", "targets", "_wrapper")
        self.owner = None
        self.field_name = field_name
        self.subfield_type = subfield_type
        self.unique = unique

    def __str__(self):
        return "({}, {}, {}, {})".format(
            self.__class__.__name__, self.owner.__name__, self.field_name, self.subfield_name
        )

    def __repr__(self):
        return self.__str__()

    def _check_validation(self):
        subfield_name = self.subfield_name
        assert subfield_name
        model_name = self.owner.__name__
        assert subfield_name != model_name, "subfield name 은 model name 과 달라야 합니다."
        assert subfield_name[0] != "_", "subfield name 은 _(under bar) 로 시작하면 안됩니다."

    def set_owner(self, owner):
        self.owner = owner

    @cached_property
    def subfield_name(self):
        return self.owner.subfields["_total_reverse"][self]

    @cached_property
    def computed_field_name(self):
        field_names, subfield_name = self.owner.field_names, self.subfield_name
        field_name = "computed_{}".format(subfield_name)
        return field_name if field_name in field_names else None

    def __get__(self, instance, owner):
        raise NotImplementedError

    def __set__(self, instance, value):
        raise NotImplementedError

    def convert_filter(self, model, parts, value, lookup_type, raw):
        raise NotImplementedError


class SubfieldWrapper(Subfield):
    def __init__(self, original_subfield_name):
        super().__init__("_wrapper", None)
        self.original_subfield_name = original_subfield_name

    @cached_property
    def original(self):
        original_subfield = getattr(self.owner, self.original_subfield_name)
        assert isinstance(original_subfield, Subfield) and not isinstance(original_subfield, SubfieldWrapper)
        return original_subfield

    def _check_validation(self):
        self.original._check_validation()

    @cached_property
    def subfield_name(self):
        return self.original.subfield_name

    @cached_property
    def wrapper_subfield_name(self):
        return self.owner.subfields["_total_reverse"][self]

    def __get__(self, instance, owner):
        return self.original.__get__(instance, owner)

    def __set__(self, instance, value):
        return self.original.__set__(instance, value)

    def convert_filter(self, model, parts, value, lookup_type, raw):
        return self.original.convert_filter(model, parts, value, lookup_type, raw)
