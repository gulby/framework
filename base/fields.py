from psycopg2.extras import Json
from django.contrib.postgres.fields.jsonb import KeyTextTransform as DjangoKeyTextTransform
from django.contrib.postgres.fields import JSONField as DjangoJSONField, ArrayField as DjangoArrayField
from django.db.models import F, Q

from base.json import json_freeze, json_dumps


class KeyTextTransform(DjangoKeyTextTransform):
    def __init__(self, *args):
        if len(args) == 1:
            splited = args[0].split("__")
            assert len(splited) == 2, "subfield 그 자체로만 가능합니다."
            field_name = splited[0]
            assert field_name in ("data", "computed", "raw"), "json field 에 대해서만 가능합니다."
            subfield_name = splited[1]
            args = [subfield_name, field_name]
        super().__init__(*args)


class SF(F):
    pass


class SQ(Q):
    pass


class JsonAdapter(Json):
    def __init__(self, adapted, dumps=None, encoder=None):
        self.encoder = encoder
        super().__init__(adapted, dumps=dumps)

    def dumps(self, obj):
        options = {"cls": self.encoder} if self.encoder else {}
        options["ensure_ascii"] = True
        return json_dumps(obj, **options)


class JSONField(DjangoJSONField):
    def get_prep_value(self, value):
        if value is not None:
            return JsonAdapter(value, encoder=self.encoder)
        return value


class ArrayField(DjangoArrayField):
    pass


class ForceChanger(object):
    def __init__(self, model):
        self.model = model

    def __enter__(self):
        force_changer_count = self.model._force_changer_count
        assert force_changer_count >= 0
        self.model._force_changer_count = force_changer_count + 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        force_changer_count = self.model._force_changer_count
        assert force_changer_count >= 1
        self.model._force_changer_count = force_changer_count - 1


class CachedClassProperty(object):
    def __init__(self, classmethod_name, is_freeze=True):
        self.classmethod_name = classmethod_name
        self.is_freeze = is_freeze

    def __get__(self, instance, owner):
        key = "_cache_{}".format(self.classmethod_name)
        try:
            return owner.__dict__[key]
        except KeyError:
            func = getattr(owner, self.classmethod_name)
            result = func()
            if self.is_freeze:
                result = json_freeze(result)
            setattr(owner, key, result)
            assert key in owner.__dict__
            assert result == owner.__dict__[key]
            return result
