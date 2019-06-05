from django.utils.functional import cached_property

from base.utils import compute_hash_int32, console_log
from base.json import json_freeze


class AUTO(object):
    pass


class TypeMeta(type):
    def __new__(mcs, cls_name, bases, classdict):
        # 자동 할당 속성들은 제거하여 __getattr__() 이 동작하도록 함
        auto_attrs = []
        for k, v in classdict.items():
            if v == AUTO:
                auto_attrs.append(k)
        for k in auto_attrs:
            del classdict[k]
        # 클래스 생성
        type_class = super().__new__(mcs, cls_name, bases, classdict)
        type_class._name_map = {}
        type_class._value_map = {}
        return type_class

    def __getattr__(cls, name):
        if name[0] in "_0123456789":
            raise AttributeError
        name_map = cls._name_map
        try:
            return name_map[name]
        except KeyError:
            value = compute_hash_int32(name)
            value_map = cls._value_map
            assert value not in value_map, "Hash Collision Detected. name 을 바꿔 주세요 ㅠ_ㅜ"
            instance = int.__new__(cls, value)
            instance.name = name
            instance.value = value
            instance._model = None
            name_map[name] = instance
            value_map[value] = instance
            return instance

    def __iter__(cls):
        return (v for v in cls._name_map.values())

    def __len__(cls):
        return len(cls._name_map)


class TypeBase(int, metaclass=TypeMeta):
    def __new__(cls, p):
        if isinstance(p, TypeBase):
            return p
        elif type(p) == str:
            return cls._name_map[p]
        elif type(p) == int:
            return cls._value_map[p]
        else:
            raise AssertionError("초기화 되기 전에 Type instance 가 참조되었습니다.")

    def json_decode(self, value):
        return self.model.json_decode(value)

    def __instancecheck__(self, instance):
        return isinstance(instance, self.model)

    def __str__(self):
        return self.name

    @property
    def model(self):
        assert self._model, console_log("Type.{} 에 매핑되는 model 이 없습니다.".format(self))
        return self._model

    def is_subtype_of(self, super_type):
        super_model = super_type.model
        model = self.model
        result = self in super_model.types
        assert result is issubclass(model, super_model)
        return result

    @cached_property
    def sub_types(self):
        ts = (sub_model.my_type for sub_model in (t.model for t in self.__class__) if self in sub_model.super_types)
        return json_freeze(ts)

    @classmethod
    def issubclass(cls, C1, C2):
        if isinstance(C1, cls):
            C1 = C1.model
        if isinstance(C2, cls):
            C2 = C2.model
        return issubclass(C1, C2)
