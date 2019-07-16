from types import MappingProxyType
from django.conf import settings

from base.descriptors.subfields import Subfield
from base.json import json_encode, json_decode, json_walk
from base.utils import console_log, compute_hash_uuid, safe_call
from base.enums import Status, Expire
from base.constant import LOOKUP_SEP


class ValueSubfield(Subfield):
    def __init__(
        self,
        field_name,
        subfield_type,
        unique=False,
        default=None,
        check=None,
        filter=None,
        null=True,
        normalize=None,
        create_only=False,
        expire=Expire.NONE,
        raw_field=None,
        raw_value_mapping=None,
        choices=None,
        alias=None,
    ):
        assert field_name in ("data", "computed")
        assert subfield_type
        assert check is None or callable(check), "check 는 function pointer 로 넣어야 합니다."
        if normalize:
            assert callable(normalize), "normalize 는 function pointer 로 넣어야 합니다."
            try:
                normalize(None) is None, "normalize 에 None 을 넘긴 결과는 None 이거나 에러가 발생해야 합니다."
            except Exception:
                pass
        assert isinstance(raw_field, str) or raw_field is None
        assert isinstance(raw_value_mapping, dict) or raw_value_mapping is None
        assert not raw_value_mapping or raw_field
        if expire != Expire.NONE:
            assert field_name == "data", "expire 는 data subfield 에만 세팅할 수 있습니다."
            assert callable(default), "expire 가 세팅된 경우 default 는 callable 이어야 합니다."
        assert choices is None or isinstance(choices, tuple), "choices 는 tuple 만 가능합니다."
        assert alias is None or isinstance(alias, str), "alias 는 str 만 가능합니다."
        super().__init__(field_name, subfield_type, unique=unique)
        self.default = default
        self.check = check
        self.filter = filter
        self.null = null
        self.normalize = normalize
        self.create_only = create_only
        self.expire = expire
        self.raw_field = raw_field
        self.raw_value_mapping = raw_value_mapping
        self.choices = choices
        self.alias = alias
        if default is not None:
            assert self.check_schema(default)

    def check_schema(self, value):
        # callable
        if callable(value):
            return True
        # null
        if self.null is False:
            assert value is not None, console_log(
                "{}.{} 은 null 이 허용되지 않습니다.".format(self.owner.__name__, self.subfield_name)
            )
        # check, choices
        if value is not None:
            choices = self.choices
            if choices:
                if value not in choices:
                    return False
            check = self.check
            if check:
                result = check(value)
                if not result:
                    return False
        # subfield_type
        subfield_type = self.subfield_type
        if subfield_type is None or value is None:
            return True
        return isinstance(value, subfield_type)

    def __get__(self, instance, owner):
        if not instance:
            return self
        field_name, subfield_name, subfield_type, expire = (
            self.field_name,
            self.subfield_name,
            self.subfield_type,
            self.expire,
        )
        json_field = getattr(instance, field_name)
        value = json_field[subfield_name]
        if callable(value):
            try:
                value = value(instance)
            except Exception as e:
                msg = "{}: {}".format(e.__class__.__name__, str(e))
                if "NoneType" in msg or "DoesNotExist" in msg:
                    return None
                else:
                    raise e
            assert not callable(value)
            assert self.check_schema(value)
            value = json_encode(value)
            json_field[subfield_name] = value
        value_decoded = json_decode(value, subfield_type)
        return value_decoded

    def __set__(self, instance, value):
        cls, subfield_type, normalize, lf_name, field_name, subfield_name, create_only = (
            instance.__class__,
            self.subfield_type,
            self.normalize,
            self.subfield_name,
            self.field_name,
            self.subfield_name,
            self.create_only,
        )
        json_field = getattr(instance, field_name)
        if normalize and value is not None:
            old = value
            value = normalize(value)
            if instance.status == Status.NEW and old != value:
                if instance.raw is None:
                    instance.raw = {}
                instance.raw[lf_name] = old
        # value 를 subfield_type 으로 변환. 따라서 json_decode() 는 형변환도 구현해야 함
        value = json_decode(value, subfield_type)
        # old
        old = json_field[subfield_name]
        if callable(old):
            old = None
        old = json_decode(old, subfield_type)
        if old != value:
            # TODO : if 블럭 밖에 있으면 에러 발생. 장고 내부 코드 확인 후 조처 ( django.db.models.query )
            """
            if annotation_col_map:
                for attr_name, col_pos in annotation_col_map.items():
                    setattr(obj, attr_name, row[col_pos])
            """
            if create_only:
                assert instance.status in (Status.CREATING, Status.NEW), console_log(
                    "{}.{} = {} ({})".format(self.owner.__name__, self.subfield_name, value, instance.status)
                )
                assert old is None
                assert value is not None
            assert self.check_schema(value), console_log(
                "{}.check_schema({}) is fail!".format(self.subfield_name, value)
            )
            instance.assert_changeable(field_name)
            json_field[subfield_name] = json_encode(value)
            instance.onchange_subfield(field_name, subfield_name, old, value)
        return old

    def convert_filter(self, model, parts, value, lookup_type, raw):
        if self.filter:
            assert lookup_type == "exact", console_log("filter 가 지정된 subfield 에 대해서는 exact 검색만 가능합니다.", lookup_type)
            return self.filter(model, value)
        assert lookup_type not in ("isnull",), console_log("subfield 에 대해 지원되지 않는 lookup_type 입니다.", lookup_type)
        return {"{}__{}__{}".format(self.field_name, LOOKUP_SEP.join(parts), lookup_type): json_encode(value)}


class RendererValueSubfield(ValueSubfield):
    def __init__(self, *args, **kwargs):
        default_if_none = kwargs.pop("default_if_none", "")
        super().__init__(*args, **kwargs)
        self.default_if_none = default_if_none

    def __get__(self, instance, owner):
        if not instance:
            return self
        value_decoded = super().__get__(instance, owner)
        return value_decoded if value_decoded is not None else self.default_if_none


class UnameSubfield(ValueSubfield):
    def __init__(
        self, default=None, check=None, null=True, normalize=None, expire=Expire.NONE, create_only=False, alias=None
    ):
        super().__init__(
            "data",
            str,
            unique=True,
            default=default,
            check=check,
            filter=lambda cls, v: {"computed_uri_hash": compute_hash_uuid(cls.convert_uri(v))},
            null=null,
            normalize=normalize,
            expire=expire,
            create_only=create_only,
            alias=alias,
        )


class DerivedUnameSubfield(UnameSubfield):
    def __init__(self, default, check=None, null=True, normalize=None, create_only=None, alias=None):
        assert callable(default), "DerivedUnameSubfield 는 default 로 function 이 지정되어야 합니다."
        super().__init__(
            default=default,
            check=check,
            null=null,
            normalize=normalize,
            expire=Expire.ON_CHANGE,
            create_only=create_only,
            alias=alias,
        )

    def __set__(self, instance, value):
        if settings.IS_UNIT_TEST:
            assert value == safe_call(
                self.default, instance
            ), "DerivedUnameSubfield 는 값을 직접 세팅할 수 없습니다. default 를 통해 세팅되어야 합니다."
        return super().__set__(instance, value)


class DictSubfield(ValueSubfield):
    def __init__(self, field_name, subfield_type, unique=False, default=None, check=None, filter=None, alias=None):
        if check is not None:
            raise NotImplementedError
        subfield_type = MappingProxyType(subfield_type)
        total_default = {}
        total_default.update(subfield_type)
        for k in total_default:
            total_default[k] = None
        if default:
            total_default.update(default)
        super().__init__(field_name, subfield_type, unique, MappingProxyType(total_default), check, filter, alias=alias)

    def check_schema(self, value):
        if type(value) not in (dict, MappingProxyType):
            return False
        schema = self.subfield_type
        for k, v in value.items():
            if k not in schema:
                return False
            if schema[k] is None or v is None:
                continue
            if not isinstance(v, schema[k]):
                return False
        return True

    def __get__(self, instance, owner):
        def setter(patch):
            instance.assert_changeable(self.field_name)
            self.__set__(instance, patch)

        if not instance:
            return self
        result = super().__get__(instance, owner)
        assert type(result) is dict
        return DictSubfieldHelper(result, setter, self.subfield_type)

    def __set__(self, instance, patch):
        def encoder(d, k, v, storage):
            patch[k] = json_encode(v)

        instance.assert_changeable(self.field_name)
        cls, field_name, subfield_name = (instance.__class__, self.field_name, self.subfield_name)
        assert self.check_schema(patch)
        d = getattr(instance, field_name)[subfield_name]
        assert id(d) != id(patch)
        assert type(d) is dict
        old = {}
        old.update(d)
        json_walk(patch, encoder)
        d.update(patch)
        if old != d:
            instance.onchange_subfield(self.field_name, subfield_name, old, d)
        return old


class DictSubfieldHelper(object):
    def __init__(self, d, setter, subfield_type):
        self._d = d
        self._setter = setter
        self._subfield_type = subfield_type

    def __getitem__(self, key):
        value = self._d[key]
        # TODO : 튜닝
        return json_decode(value, self._subfield_type[key])

    def __getattr__(self, key):
        value = self._d[key]
        # TODO : 튜닝
        return json_decode(value, self._subfield_type[key])

    def __setitem__(self, key, value):
        patch = {key: value}
        self._setter(patch)

    def __setattr__(self, key, value):
        if key[0] == "_":
            self.__dict__[key] = json_encode(value)
            return
        patch = {key: value}
        self._setter(patch)

    def update(self, patch):
        self._setter(patch)

    def __eq__(self, other):
        if other is None:
            return False
        elif type(other) in (dict, MappingProxyType):
            return self._d == other
        elif type(other) is DictSubfieldHelper:
            return self._d == other._d
        else:
            raise NotImplementedError

    def __len__(self):
        return len(self._d)

    def __str__(self):
        return str(self._d)

    def __repr__(self):
        return repr(self._d)

    def __contains__(self, key):
        return key in self._d


class ListSubfield(ValueSubfield):
    def __init__(self, field_name, subfield_type, unique=False, default=None, check=None, filter=None, alias=None):
        if check is not None:
            raise NotImplementedError
        if default:
            assert type(default) is tuple
            assert all([isinstance(v, subfield_type[0]) for v in default])
            default = [v for v in default]
        assert type(subfield_type) is list and len(subfield_type) == 1
        subfield_type = tuple(subfield_type)
        super().__init__(field_name, subfield_type, unique, default or (), check, filter, alias=alias)

    def check_schema(self, value):
        if type(value) not in (list, tuple):
            return False
        schema = self.subfield_type
        for v in value:
            if v is None:
                continue
            if not isinstance(v, schema[0]):
                return False
        return True

    def __get__(self, instance, owner):
        def notifier(old, new):
            instance.onchange_subfield(self.field_name, self.subfield_name, old, new)

        def asserter():
            instance.assert_changeable(self.field_name)

        if not instance:
            return self
        result = super().__get__(instance, owner)
        assert type(result) is list
        return ListSubfieldHelper(result, notifier, asserter, self.subfield_type)

    def __set__(self, instance, patch):
        instance.assert_changeable(self.field_name)
        assert self.check_schema(patch)
        d = super().__get__(instance, instance.__class__)
        old = d[:]
        # address 가 바뀌면 안되기 때문에 성능을 약간 희생해서라도 이렇게 구현
        d.clear()
        patch = [json_encode(e) for e in patch]
        d.extend(patch)
        if old != d:
            instance.onchange_subfield(self.field_name, self.subfield_name, old, d)
        return old


def list_subfield_setter(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        self._asserter()
        old = self._d[:]
        result = func(*args, **kwargs)
        self._notifier(old, self._d)
        return result

    return wrapper


class ListSubfieldHelper(object):
    def __init__(self, d, notifier, asserter, subfield_type):
        self._d = d
        self._notifier = notifier
        self._asserter = asserter
        self._element_type = subfield_type[0]

    def __getitem__(self, key):
        encoded = self._d[key]
        # TODO : 튜닝
        return json_decode(encoded, self._element_type)

    @list_subfield_setter
    def __setitem__(self, key, value):
        self._d[key] = json_encode(value)

    @list_subfield_setter
    def append(self, value):
        self._d.append(json_encode(value))

    @list_subfield_setter
    def remove(self, value):
        encoded = json_encode(value)
        index = self._d.index(encoded)
        del self._d[index]
        return index

    @list_subfield_setter
    def remove_index(self, index):
        encoded = self._d[index]
        del self._d[index]
        value = json_decode(encoded, self._element_type)
        return value

    @list_subfield_setter
    def extend(self, patch):
        self._d.extend(patch)

    def __eq__(self, other):
        if type(other) in (list, tuple):
            return self._d == other
        elif type(other) is ListSubfieldHelper:
            return self._d == other._d
        else:
            raise NotImplementedError

    def __len__(self):
        return len(self._d)

    def __str__(self):
        return str(self._d)

    def __repr__(self):
        return repr(self._d)

    def __contains__(self, item):
        return item in self._d
