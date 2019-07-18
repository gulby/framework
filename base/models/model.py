from copy import deepcopy
from types import MappingProxyType
from uuid import UUID
from datetime import datetime
from django.db.models import DEFERRED, PROTECT
from django.db.models import UUIDField, IntegerField, ForeignKey, BigIntegerField
from django.conf import settings
from django.utils.timezone import now
from django.db.models.base import ModelBase as DjangoModelBase
from django.contrib.postgres.indexes import GinIndex
from django.utils.functional import cached_property

from base.enums import Status, set_invalid_on_exception, Expire
from base.types import Type
from base.managers import ModelManager
from base.utils import compute_hash_uuid, run_sql, console_log, safe_call
from base.transaction import TransactionManager, get_datetime_from_key
from base.json import patch_mjson, json_deepcopy_with_callable, json_encode, json_decode
from base.fields import ForceChanger, CachedClassProperty
from base.descriptors import (
    ValueSubfield,
    ForeignKeySubfield,
    SubfieldWrapper,
    ReverseForeignKeySubfield,
    UnameSubfield,
)
from base.models.abstract import AbstractModel
from base.fields import JSONField, ArrayField
from base.exceptions import DuplicateUriException, OptimisticLockException
from base.constant import ONCHANGE_FUNC_NAME, COMPUTE_FUNC_NAME, COMPUTED_FIELD_NAME


class ModelBase(DjangoModelBase):
    def __new__(mcs, cls_name, bases, classdict):
        has_alias_fields = {k: v.alias for k, v in classdict.items() if isinstance(v, ValueSubfield) and v.alias}
        for k, alias in has_alias_fields.items():
            # 중복되는 alias 가 있는경우
            assert alias not in classdict, console_log("중복되는 alias 가 존재합니다. {}".format(alias))
            # 상위클래스에 alias 의 이름이 존재하는 경우 SubfieldWrapper 인지 확인하고 pass
            if alias in bases[0].__dict__.keys():
                base_alias = bases[0].__dict__[alias]
                assert isinstance(base_alias, SubfieldWrapper), console_log(
                    "상위클래스에 SubfieldWrapper 가 아닌 {} 가 존재합니다.".format(alias)
                )
                assert base_alias.original_subfield_name == k
            else:
                classdict[alias] = SubfieldWrapper(k)
        cls = super().__new__(mcs, cls_name, bases, classdict)
        t = getattr(Type, cls_name)
        t._model = cls
        assert cls.subfields
        return cls


class Model(AbstractModel, metaclass=ModelBase):
    UNIQUE_KEY_SUBFIELD_NAMES = ("id", "uname", "uri", "uri_hash", "computed_uri_hash")
    PSEUDO_KEY_SUBFIELD_NAMES = ("name",)

    class Meta:
        base_manager_name = "objects"
        unique_together = (
            ("status", "type", "id"),
            ("computed_owner", "status", "type", "id"),
            ("computed_container", "status", "type", "id"),
            ("computed_proprietor", "status", "type", "id"),
        )
        indexes = (GinIndex(fields=("computed_search_array",)),)

    # class part
    objects = ModelManager()
    my_type = CachedClassProperty("_get_my_type", is_freeze=False)
    types = CachedClassProperty("_get_types")
    super_types = CachedClassProperty("_get_super_types")
    subfield_defaults = CachedClassProperty("_get_subfield_defaults")
    required_filters = ({"status", "type"},)
    uri_format = CachedClassProperty("_get_uri_format", is_freeze=False)
    field_names_needs_object_setter = CachedClassProperty("_get_field_names_needs_object_setter")
    is_agent = False

    # system field
    type = IntegerField(null=False)
    optimistic_lock_count = IntegerField(null=False)

    # json field
    data = JSONField(null=False, blank=True)
    computed = JSONField(null=False, blank=True)
    raw = JSONField(null=True, blank=True)

    # data subfields
    created_date = ValueSubfield("data", datetime)
    uname = UnameSubfield()  # intrinsic key (mutable)
    name = ValueSubfield("data", str)  # loose key (mutable)

    # computed subfields
    uri = ValueSubfield(
        "computed",
        str,
        check=lambda v: v[:5] == "/uri/" and v[-1] == "/",
        filter=lambda cls, v: {"computed_uri_hash": compute_hash_uuid(v)},
    )
    uri_hash = ValueSubfield("computed", UUID, filter=lambda cls, v: {"computed_uri_hash": v})

    # relational subfields
    creator = ForeignKeySubfield("data", Type.Actor, create_only=True)
    owner = ForeignKeySubfield("data", Type.Actor)
    container = ForeignKeySubfield("data", Type.Model)
    elements = ReverseForeignKeySubfield("computed", Type.Model, "container")
    proprietor = ForeignKeySubfield("data", Type.Model)
    properties = ReverseForeignKeySubfield("computed", Type.Model, "proprietor")

    # computed field
    computed_uri_hash = UUIDField(unique=True, null=True)  # derived from uname (intrinsic key)
    computed_owner = ForeignKey(
        "Model", related_name="computed_possessions", null=True, on_delete=PROTECT, db_index=False
    )
    computed_container = ForeignKey(
        "Model", related_name="computed_elements", null=True, on_delete=PROTECT, db_index=False
    )
    computed_proprietor = ForeignKey(
        "Model", related_name="computed_properties", null=True, on_delete=PROTECT, db_index=False
    )
    computed_search_array = ArrayField(BigIntegerField(), null=True)

    # class member variable
    _is_initialized = False  # instance member variable 이나 __init__() 전에 setattr 이 호출될 수 있어 세팅함

    @cached_property
    def intrinsic_content_subfield_names(self):
        return tuple(
            k
            for k, v in self.subfields["_total"].items()
            if not isinstance(v, ForeignKeySubfield)
            and not isinstance(v, ReverseForeignKeySubfield)
            and not isinstance(v, SubfieldWrapper)
            and k not in ("created_date", "uname", "uri", "uri_hash")
        )

    def is_same_content(self, other):
        if self.my_type != other.my_type:
            return False
        for subfield_name in self.intrinsic_content_subfield_names:
            if getattr(self, subfield_name) != getattr(other, subfield_name):
                return False
        return True

    def __init__(self, *args, **kwargs):
        assert not self.__class__.__dict__.get("ABSTRACT", False), "인스턴스화가 불가능한 모델입니다."
        self._is_initialized = False
        self._force_changer_count = 0
        super().__init__(*args, subfield_kwargs=kwargs)

    def init_variables(self):
        super().init_variables()
        self._is_initialized = True
        self._mjson_revert_patch = {"data": {}, "computed": {}}
        self._old_uri = None
        if settings.IS_UNIT_TEST:
            self._mjson_on_init = deepcopy(self.mjson)

    @property
    def last_transaction_date(self):
        return get_datetime_from_key(self.last_transaction)

    @classmethod
    def _get_my_type(cls):
        return getattr(Type, cls.__name__)

    @classmethod
    def _get_types(cls):
        my_type = cls.my_type
        if my_type == Type.Model:
            return []
        sub_model_types = list(my_type.sub_types)
        return [my_type] + sub_model_types

    @classmethod
    def _get_super_types(cls):
        return [parent.my_type for parent in cls.mro()[1:] if issubclass(parent, Model)]

    @classmethod
    def _get_subfield_defaults(cls):
        total = {"data": {}, "computed": {"_mjson_revert_patch": None}}
        for k, v in cls.subfields["data"].items():
            total["data"][k] = json_encode(v.default)
        for k, v in cls.subfields["computed"].items():
            total["computed"][k] = json_encode(v.default)
        return total

    @classmethod
    def _get_uri_format(cls):
        app_name = cls.__module__.split(".")[0]
        cls_name = cls.__name__
        header = "/uri/{}/{}/".format(app_name.lower(), cls_name.lower())
        return header + "{}/"

    @classmethod
    def _get_field_names_needs_object_setter(cls):
        return cls.subfield_names + cls.model_level_field_names + cls.only_column_names

    def __str__(self):
        return "({}, {}, {}, {}, {})".format(
            self.type, self.id, self.uri or self.uname or self.name, self.status.name, id(self)
        )

    def _pre_create(self):
        super()._pre_create()
        my_type = self.my_type
        assert my_type is not None, "Type 이 정의되어 있어야 합니다."
        self.type = my_type
        default = json_deepcopy_with_callable(self.subfield_defaults)
        self.data = default["data"]
        self.computed = default["computed"]
        self.optimistic_lock_count = 0
        self.data["created_date"] = str(now())

    def _init_subfields(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def on_create(self):
        super().on_create()
        for subfield_name, subfield in self.subfields["data"].items():
            encoded = self.data[subfield_name]
            if encoded and not callable(encoded):
                self.onchange_subfield("data", subfield_name, None, json_decode(encoded, subfield.subfield_type))

    def _init_no_inited_subfields(self):
        for k, v in self.data.items():
            if v is None and k[0] != "_":
                subfield = self.get_subfield(k)
                assert subfield.null, console_log("{} 는 null 이 허용되지 않습니다.".format(subfield.subfield_name))
            elif callable(v):
                self.data[k] = json_encode(safe_call(v, self))
        for k, v in self.computed.items():
            if v is None and k[0] != "_":
                subfield = self.get_subfield(k)
                assert subfield.null
            elif callable(v):
                self.computed[k] = json_encode(safe_call(v, self))

    def _pre_syncdb_insert(self, tran):
        super()._pre_syncdb_insert(tran)
        self._init_no_inited_subfields()

    def take_optimistic_lock(self):
        if self.status in (Status.CREATING, Status.NEW):
            return
        with ForceChanger(self):
            self.optimistic_lock_count += 1
        self.save()

    # 절대 함부로 사용하지 말 것. 정말 특수한 경우가 아니라면 활용할 일이 없음
    def _set_fields(self, **kwargs):
        # version
        assert "version" not in kwargs
        old_version = self.version
        self.__dict__["version"] = old_version + 1
        kwargs["version"] = old_version + 1
        # set fields
        for k, v in kwargs.items():
            self.__dict__[k] = v
            if settings.IS_UNIT_TEST:
                self._mjson_on_init[k] = v
        # DB
        result = self.__class__.objects.filter(id=self.id, version=old_version).update(**kwargs)
        if result == 0:
            raise OptimisticLockException
        assert result == 1

    def set_working(self):
        assert self.is_in_writable_transaction(), "해당 instance 가 수정 가능한 Transaction 내에 없습니다."
        if self.status == Status.NEW:
            tran = TransactionManager.get_transaction()
            self._syncdb_insert(tran)
        assert self.status in (Status.NORMAL, Status.DIRTY)
        self._set_fields(status=Status.WORKING)

    def rollback_working(self):
        assert self.status is Status.WORKING, console_log("Status 가 WORKING 일때만 호출이 가능합니다.")
        self._set_fields(status=Status.NORMAL)

    def take_exclusive_lock(self, nowait=False):
        if self.status in (Status.CREATING, Status.NEW):
            return
        manager = self.__class__.objects
        queryset = manager.select_for_update(nowait=nowait).filter(id=self.id)
        assert queryset._result_cache is None or len(queryset._result_cache) == 0
        queryset._fetch_all()
        assert len(queryset._result_cache) == 1

    @classmethod
    def from_db_impl(cls, db, field_names, values):
        t = Type(values[field_names.index("type")])
        # override cls
        cls_t = t.model
        # almost same with DjangoModel.from_db()
        if len(values) != len(cls_t._meta.concrete_fields):
            values_iter = iter(values)
            values = [next(values_iter) if f.attname in field_names else DEFERRED for f in cls_t._meta.concrete_fields]
        new = cls_t(*values)
        new._is_initialized = False
        new._state.adding = False
        new._state.db = db
        # for only Model
        assert new.type == cls_t.my_type
        new.type = Type(new.type)
        new.status = Status(new.status)
        new.init_variables()
        new.patch_json_field()
        return new

    # TODO : schema 만 바뀐 경우에 save() 가 가능하도록 하는 구현 부분 리팩토링
    def patch_json_field(self):
        if self.status == Status.DELETED:
            return
        assert self.status in (Status.NORMAL, Status.WORKING), self.status
        total_default = self.subfield_defaults
        _schema_changed = False
        old_status = self.__dict__["status"]
        for json_field_name in total_default:
            json_field = self.__dict__[json_field_name]
            field_default = total_default[json_field_name]
            for key, value in field_default.items():
                if key not in json_field:
                    if callable(value):
                        value = safe_call(value, self)
                    json_field[key] = json_deepcopy_with_callable(value)
                    _schema_changed = True
                    self.__dict__["status"] = Status.DIRTY
                    self._mjson_revert_patch.update(
                        {"status": json_encode(old_status), json_field_name: {"_schema_changed": _schema_changed}}
                    )
            for k in [k for k in json_field.keys() if k not in field_default]:
                del json_field[k]
                _schema_changed = True
                self.__dict__["status"] = Status.DIRTY
                self._mjson_revert_patch.update(
                    {"status": json_encode(old_status), json_field_name: {"_schema_changed": _schema_changed}}
                )
        if _schema_changed and settings.IS_UNIT_TEST:
            self._mjson_on_init = deepcopy(self.mjson)
            self._mjson_on_init["status"] = json_encode(old_status)

    def patch(self, **kwargs):
        for subfield_name, value in kwargs.items():
            setattr(self, subfield_name, value)

    def assert_changeable(self, field_name=None):
        super().assert_changeable(field_name)
        if field_name:
            assert field_name not in ("id", "type"), "id, type field 는 절대 수정할 수 없습니다."
            if field_name == "raw":
                assert self.status in (Status.CREATING, Status.NEW), "raw 컬럼은 최초 생성시에만 세팅 가능합니다."
            elif settings.IS_UNIT_TEST:
                assert field_name == "data" or self._force_changer_count >= 1, console_log(
                    "data field 를 제외하면 기본적으로 수정 금지입니다 : {}".format(field_name)
                )
            else:
                # for django admin
                assert (
                    field_name in ("data", "computed") or self._force_changer_count >= 1
                ), "data field 를 제외하면 기본적으로 수정 금지입니다. computed field 는 수정되지 않고 무시됩니다."

    def __setattr__(self, field_name, value):
        # __dict__ setter
        if field_name[0] == "_" or not self._is_initialized:
            self.__dict__[field_name] = value
            return
        # object setter
        # TODO : 모두 확정된 후 로컬상수변수로 대체하여 튜닝
        if field_name in self.field_names_needs_object_setter:
            return object.__setattr__(self, field_name, value)
        # for overrides super().delete()
        if field_name == "id" and value is None:
            return
        # set field
        old = getattr(self, field_name)
        if old != value:
            # for django admin
            if value is None and field_name in ("data", "computed"):
                return
            # check pre condition
            self.assert_changeable(field_name)
            # change value
            if field_name == "data":
                for subfield, subvalue in value.items():
                    setattr(self, subfield, subvalue)
            elif field_name == "status":
                assert old.check_route(value), "해당 status 변경은 허용되지 않습니다: {} --> {}".format(old, value)
                self.__dict__["status"] = value
            elif field_name == "computed":
                assert not settings.IS_UNIT_TEST, "computed field 직접 세팅은 허용되지 않습니다."
                # for django admin
                console_log("try change of computed field is ignored")
            else:
                if self.status in (Status.NORMAL, Status.WORKING):
                    self.__setattr__("status", Status.DIRTY)
                self.__dict__[field_name] = value
            # make revert patch
            if field_name not in self._mjson_revert_patch and field_name in self.field_names:
                self._mjson_revert_patch[field_name] = json_encode(old)
            # raw
            if field_name == "raw":
                assert self.status in (Status.CREATING, Status.NEW)
                self.init_data_by_raw()

    # for cached queryset filter
    def __getattr__(self, key):
        # dot operator 처리 순서 상 이미 __dict__ 는 check 가 된 상태임
        if key[0] == "_":
            raise AttributeError(key)

        parts = key.split("__")
        field_name = parts[0]

        # TODO : ComplexSubfield 에 대해 2-depth 까지만 허용되고 있는데, 이를 확장
        # json field
        if field_name in ("data", "computed", "raw"):
            assert len(parts) in (2, 3)
            subfield_name = parts[1]
            assert getattr(self.__class__, subfield_name).field_name == field_name
            result = getattr(self, subfield_name)
            if len(parts) == 3:
                result = result[parts[2]]
            return result
        # subfield
        elif field_name in self.subfield_names:
            assert len(parts) in (2,)
            subfield_name = parts[0]
            result = getattr(self, subfield_name)[parts[1]]
            return result
        else:
            raise AttributeError("{}.{}".format(self.__class__.__name__, key))

    def get_modified_field_names(self):
        return [field_name for field_name, value in self._mjson_revert_patch.items() if value != {}]

    def create_history(self):
        column_names = [f for f in self.column_names if not f.startswith("computed") and not f.startswith("raw")]
        field_names_str = ",".join(column_names)
        tran = TransactionManager.get_transaction()
        query = "insert into base_modelhistory ({},{}) select {},{} from base_model where id=%s".format(
            "history_transaction", field_names_str, tran.id, field_names_str
        )
        instance_id = self.id
        run_sql(query, params=(instance_id,))

    def on_nosave(self):
        if settings.IS_UNIT_TEST:
            assert self.mjson == self._mjson_on_init, "subfield 를 통하지 않는 등 잘못된 방식으로 필드가 수정되었습니다."
        super().on_nosave()

    def _syncdb_update(self, tran, update_fields=None):
        assert update_fields is None
        update_fields = self.get_modified_field_names()
        assert len(update_fields) >= 2, "수정된 필드가 없는데 syncdb_update() 가 호출되었습니다."
        assert "status" in update_fields and "status" in self._mjson_revert_patch, "status 필드가 적절한 방식으로 수정되지 않았습니다."
        assert (
            "version" not in update_fields and "last_transaction" not in update_fields
        ), "system 필드가 적절한 방식으로 수정되지 않았습니다."
        with ForceChanger(self):
            self.version += 1
            self.last_transaction = tran.id
        if settings.IS_UNIT_TEST:
            mjson_reverted = patch_mjson(deepcopy(self.mjson), MappingProxyType(self._mjson_revert_patch))
            # TODO : schema 만 바뀐 경우에 save() 가 가능하도록 하는 구현 부분 리팩토링
            if "_schema_changed" in mjson_reverted["data"]:
                del mjson_reverted["data"]["_schema_changed"]
            if "_schema_changed" in mjson_reverted["computed"]:
                del mjson_reverted["computed"]["_schema_changed"]
            assert mjson_reverted == self._mjson_on_init, "subfield 를 통하지 않는 등 잘못된 방식으로 필드가 수정되었습니다."
        self.create_history()
        self.computed["_mjson_revert_patch"] = self._mjson_revert_patch
        update_fields.extend(["version", "last_transaction", "computed"])
        super()._syncdb_update(tran, update_fields=update_fields)

    def _mark_delete(self):
        with ForceChanger(self):
            self.computed_uri_hash = None
        super()._mark_delete()

    def on_delete(self):
        subfields = self.subfields
        for rf in subfields["sources"]:
            setattr(self, rf, None)
        for rf in subfields["targets"]:
            setattr(self, rf, None)

    def _syncdb_delete(self, tran):
        self.create_history()
        super()._syncdb_delete(tran)

    def _destroy(self, using=None, keep_parents=True):
        self.create_history()
        super()._destroy(using=None, keep_parents=True)

    def _process_expire_onchange(self, subfield_name=None):
        if subfield_name is None:
            for k, v in self.subfields["data"].items():
                if v.expire == Expire.ON_CHANGE:
                    v.__set__(self, v.default(self))
        else:
            subfields = self.subfields
            if subfield_name in subfields["_dependents"]:
                depended = subfields["_dependents"][subfield_name]
                for v in depended:
                    if v.expire == Expire.ON_CHANGE:
                        v.__set__(self, safe_call(v.default, self))

    def _process_dependent_computed(self, subfield_name):
        subfields = self.subfields
        if subfield_name in subfields["_dependents"]:
            for v in subfields["_dependents"][subfield_name]:
                if v.field_name == "computed":
                    self.compute(v.subfield_name)

    @set_invalid_on_exception
    def onchange_subfield(self, field_name, subfield_name, old, new):
        assert old != new, "old 와 new 값이 같은 경우는 원천적으로 발생되지 않도록 해야 합니다."
        old_status, _mjson_revert_patch, subfields = (self.status, self._mjson_revert_patch, self.subfields)
        subfield = subfields[field_name][subfield_name]
        assert not isinstance(subfield, SubfieldWrapper)
        if old_status == Status.CREATING:
            # TODO : save() 호출 자체를 없애고 나면 이것도 없애기
            # 이때는 on_create 이후 별도로 onchange 이벤트를 일괄 발생시킴
            return
        if subfield_name not in _mjson_revert_patch[field_name]:
            _mjson_revert_patch[field_name][subfield_name] = json_encode(old)
        with ForceChanger(self):
            if old_status not in (Status.NEW, Status.NO_SYNC):
                self.status = Status.DIRTY
            self._process_dependent_computed(subfield_name)
            # original
            onchange_func_name = ONCHANGE_FUNC_NAME.format(subfield_name)
            func = getattr(self, onchange_func_name, None)
            func and func(old, new)
            # wrappers
            for wrapper in subfields["_wrapper_reverse"].get(subfield_name, []):
                onchange_func_name = ONCHANGE_FUNC_NAME.format(wrapper.wrapper_subfield_name)
                func = getattr(self, onchange_func_name, None)
                func and func(old, new)
        self._process_expire_onchange(subfield_name)

    def compute(self, subfield_name):
        # set to computed json
        old_status = self.status
        compute_func = getattr(self, COMPUTE_FUNC_NAME.format(subfield_name))
        value = safe_call(compute_func)
        setattr(self, subfield_name, value)
        # set to computed_field
        computed_field_name = COMPUTED_FIELD_NAME.format(subfield_name)
        if computed_field_name in self.field_names:
            setattr(self, computed_field_name, value)
        if old_status in (Status.NORMAL, Status.WORKING) and self.status == Status.DIRTY:
            self.save()

    def _compute_total(self):
        for subfield_name in self.computed:
            if subfield_name[0] != "_":
                self.compute(subfield_name)

    def compute_uri(self):
        return self.convert_uri(self.uname)

    def compute_all(self):
        for subfield_name in self.subfields["computed"]:
            self.compute(subfield_name)

    @classmethod
    def convert_uri(cls, uname):
        if not uname:
            return None
        uri = cls.uri_format.format(uname if uname[0] != "/" else uname[1:])
        return uri if uri[-2] != "/" else uri[:-1]

    def onchange_uri(self, old, new):
        tran = TransactionManager.get_transaction()
        assert not old or old in tran.uri_mapping, "Transaction.uri_mapping 에 기존 uri 값이 존재하지 않습니다."
        if new in tran.uri_mapping:
            if self.status == Status.NEW:
                tran.remove(self)
            raise DuplicateUriException
        self._old_uri = old
        tran.set(self)

    def compute_uri_hash(self):
        return compute_hash_uuid(self.uri)

    def init_data_by_raw(self):
        pass
