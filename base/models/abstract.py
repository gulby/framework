from copy import deepcopy
from inspect import isdatadescriptor

from django.db.models import Model as DjangoModel
from django.db.models import BigIntegerField, SmallIntegerField, IntegerField

from base.transaction import TransactionManager
from base.enums import Status, Expire
from base.exceptions import OptimisticLockException
from base.utils import get_referenced_members_of_self_from_source, getsource
from base.descriptors import Subfield, ValueSubfield, SubfieldWrapper, ReverseForeignKeySubfield
from base.fields import CachedClassProperty
from base.json import json_encode
from base.constant import COMPUTE_FUNC_NAME, LOOKUP_SEP


class AbstractModel(DjangoModel):
    class Meta:
        abstract = True

    # class part
    required_filters = ({"id"},)
    subfields = CachedClassProperty("_get_subfields")
    subfield_names = CachedClassProperty("_get_subfield_names")
    field_names = CachedClassProperty("_get_field_names")
    column_names = CachedClassProperty("_get_column_names")  # ForeignKey 의 경우만 field_name 과 다름 (끝에 _id)
    only_column_names = CachedClassProperty("_get_only_column_names")
    model_level_field_names = CachedClassProperty("_get_model_level_field_names")
    uri = None
    super_types = ()

    # field
    id = BigIntegerField(primary_key=True)
    version = IntegerField(null=False)
    last_transaction = BigIntegerField(null=False)
    status = SmallIntegerField(null=False)

    def __init__(self, *args, **kwargs):
        subfield_kwargs = kwargs.pop("subfield_kwargs", {})
        super().__init__(*args, **kwargs)
        is_create = not self.id
        if is_create:
            self._pre_create()
        self.init_variables()
        if is_create:
            self.register_on_transaction()
            self._init_subfields(**subfield_kwargs)
            self.__dict__["status"] = Status.NEW
            self.on_create()

    def init_variables(self):
        self._syncdb_required = False
        self._status_before_delete = None
        self._old_syncdb_required = None

    def _init_subfields(self, **kwargs):
        pass

    def __str__(self):
        return "({}, {}, {}, {})".format(self.__class__.__name__, self.id, self.status.name, id(self))

    def json_encode(self):
        return self.id

    @classmethod
    def json_decode(cls, value):
        if value is None:
            return None
        elif isinstance(value, AbstractModel):
            return value
        else:
            return cls.objects.get(id=value)

    @property
    def mjson(self):
        mjson = {}
        for field_name in self.field_names:
            mjson[field_name] = json_encode(getattr(self, field_name))
        return mjson

    @classmethod
    def _get_field_names(cls):
        return [field.name for field in cls._meta.fields]

    @classmethod
    def _get_column_names(cls):
        return ["{}_id".format(field.name) if field.is_relation else field.name for field in cls._meta.fields]

    @classmethod
    def _get_only_column_names(cls):
        return ["{}_id".format(field.name) for field in cls._meta.fields if field.is_relation]

    @classmethod
    def _get_subfields(cls):
        # TODO : 추후 Model 이외의 다른 subclass 가 만들어지는 경우 해당 subclass 에서 가져오도록 리팩토링
        d = {
            "data": {},
            "computed": {},
            "sources": {},
            "targets": {},
            "_wrapper": {},
            "_wrapper_reverse": {},
            "_total": {},
            "_total_reverse": {},
            "_dependents": {},
        }
        # bases
        for base in cls.__bases__[::-1]:  # cls.mro() 순서와 동일하게 처리되도록 reverse 함
            if issubclass(base, AbstractModel):
                for subfield_name, subfield in base._get_subfields().items():
                    d[subfield_name].update(subfield)
        # self
        for subfield_name, subfield in cls.__dict__.items():
            if subfield_name[0] != "_" and isinstance(subfield, Subfield):
                subfield.set_owner(cls)
                field_name = subfield.field_name
                # 필수 사항 상속
                if subfield_name in d[field_name] and isinstance(subfield, ValueSubfield):
                    base_subfield = d[field_name][subfield_name]
                    if base_subfield.check:
                        if not subfield.check:
                            subfield.check = lambda v: base_subfield.check(v)
                        if "lambda v: base_subfield.check(v)" not in getsource(subfield.check):
                            # 그냥 subfield.check 를 lambda 식에 넘기면 버그 발생함
                            func = deepcopy(subfield.check)
                            subfield.check = lambda v: base_subfield.check(v) and func(v)
                    if base_subfield.null is False:
                        subfield.null = False
                d[field_name][subfield_name] = subfield
                d["_total"][subfield_name] = subfield
                d["_total_reverse"][subfield] = subfield_name
                if isinstance(subfield, SubfieldWrapper):
                    assert field_name == "_wrapper"
                    original_subfield_name = subfield.original_subfield_name
                    if original_subfield_name in d["_wrapper_reverse"]:
                        if subfield not in d["_wrapper_reverse"][original_subfield_name]:
                            d["_wrapper_reverse"][original_subfield_name].append(subfield)
                    else:
                        d["_wrapper_reverse"][original_subfield_name] = [subfield]
        # dependency
        for subfield_name, subfield in cls.__dict__.items():
            if subfield_name[0] != "_" and isinstance(subfield, ValueSubfield):
                referenced_members = []
                if subfield.expire != Expire.NONE:
                    assert callable(subfield.default) and subfield.field_name == "data"
                    referenced_members.extend(get_referenced_members_of_self_from_source(getsource(subfield.default)))
                if subfield.field_name == "computed" and not isinstance(subfield, ReverseForeignKeySubfield):
                    compute_func = getattr(cls, COMPUTE_FUNC_NAME.format(subfield_name))
                    assert callable(compute_func)
                    # TODO : compute_func 에서 다른 함수를 호출하는 경우 해당 함수들도 체크
                    referenced_members.extend(get_referenced_members_of_self_from_source(getsource(compute_func)))
                referenced_members = [
                    d["_wrapper"][m].original_subfield_name if m in d["_wrapper"] else m for m in referenced_members
                ]
                referenced_members = list(set(referenced_members))
                for m in referenced_members:
                    if m in d["_dependents"]:
                        if subfield not in d["_dependents"][m]:
                            d["_dependents"][m].append(subfield)
                    else:
                        d["_dependents"][m] = [subfield]
        return d

    @classmethod
    def _get_subfield_names(cls):
        return list(cls._get_subfields()["_total"])

    @classmethod
    def _get_model_level_field_names(cls):
        result = []
        for c in [c for c in cls.mro()]:
            result.extend(
                [k for (k, v) in c.__dict__.items() if k[0] != "_" and (isinstance(v, property) or isdatadescriptor(v))]
            )
        return result

    @classmethod
    def get_subfield(cls, subfield_name):
        subfields = cls.subfields
        try:
            return subfields["_wrapper"][subfield_name]
        except KeyError:
            return subfields["_total"][subfield_name]

    def _pre_create(self):
        tran = TransactionManager.get_transaction()
        assert tran and tran.key_gen, "트랜잭션 안에서만 인스턴스 생성이 가능합니다."
        self.status = Status.CREATING
        self.id = tran.gen_key()
        self.version = 0
        self.last_transaction = tran.id

    def register_on_transaction(self):
        # TODO : Transaction 매번 조회하는 부분 튜닝
        tran = TransactionManager.get_transaction()
        assert self.id not in tran.instances, "해당 id 값으로 이미 생성된 instance 가 존재합니다."
        assert self.uri not in tran.uri_mapping, "해당 uri 값으로 이미 생성된 instance 가 존재합니다."
        self.creator = tran.checkin_actor
        tran.set(self)

    def on_create(self):
        pass

    def assert_changeable(self, field_name=None):
        assert self.status, "DELETED 상태여서 수정할 수 없습니다."
        tran = TransactionManager.get_transaction()
        assert tran, "Transaction 내부가 아니어서 수정할 수 없습니다."
        assert tran.is_readonly is False, "ReadonlyTransaction 에서는 수정할 수 없습니다."

    @classmethod
    def from_db_impl(cls, db, field_names, values):
        new = super().from_db(db, field_names, values)
        new.status = Status(new.status)
        return new

    @classmethod
    def from_db(cls, db, field_names, values):
        new_id = values[0]
        tran = TransactionManager.get_transaction()
        already = tran and tran.get(new_id)
        if already:
            return already
        new = cls.from_db_impl(db, field_names, values)
        assert new.id == new_id
        tran and tran.set(new)
        return new

    # TODO: 풀구현
    def _do_update(self, base_qs, using, pk_val, values, update_fields, forced_update):
        # For optimistic lock
        base_qs = base_qs.filter(version=self.version - 1)
        result = super()._do_update(base_qs, using, pk_val, values, update_fields, forced_update)
        if not result:
            raise OptimisticLockException("Optimistic Lock Failed. 이미 수정된 instance 입니다.")
        return result

    def is_in_writable_transaction(self):
        tran = TransactionManager.get_transaction()
        return tran and not tran.is_readonly and self.id in tran.instances

    def on_nosave(self):
        pass

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # check
        assert not using or using == "default", "using 은 지원하지 않습니다."
        assert update_fields is None, "update_fields 는 지원하지 않습니다."
        assert self.is_in_writable_transaction(), "해당 instance 가 수정 가능한 Transaction 내에 없습니다."
        old_status = self.status
        if old_status in (Status.NORMAL, Status.WORKING):
            self.on_nosave()
            return
        assert old_status in (Status.NEW, Status.DIRTY, Status.DELETED), "save() 호출이 가능한 상태가 아닙니다: {}".format(
            old_status
        )
        assert not force_insert or old_status == Status.NEW
        assert not force_update or old_status == Status.DIRTY
        # impl
        self._syncdb_required = True
        tran = TransactionManager.get_transaction()
        tran.clear_query_cache()

    def _set_invalid_and_raise(self, e=Exception()):
        tran = TransactionManager.get_transaction()
        self.__dict__["status"] = Status.INVALID
        tran.remove(self)
        raise e

    def _pre_syncdb_insert(self, tran):
        self.__dict__["version"] = 1
        self.__dict__["last_transaction"] = tran.id
        self.__dict__["status"] = Status.NORMAL

    def on_syncdb_insert(self):
        pass

    def _syncdb_insert(self, tran):
        assert self.status == Status.NEW, "NEW 상태에서만 syncdb_insert() 호출이 가능합니다."
        assert self._syncdb_required is True, "_syncdb_required 가 True 일때만 syncdb_insert() 호출이 가능합니다."
        assert self.version == 0, "insert 시점인데 version 값이 0 이 아닙니다."
        self._syncdb_required = False
        self._pre_syncdb_insert(tran)
        # TODO : syncdb 함수들의 super().save() 예외 처리 개선
        try:
            super().save(force_insert=True, force_update=False, using=None, update_fields=None)
        except Exception as e:
            self._set_invalid_and_raise(e)
        self.init_variables()
        self.on_syncdb_insert()

    def _pre_syncdb_update(self, tran, update_fields):
        if "version" not in update_fields:
            self.__dict__["version"] += 1
        if "last_transaction" not in update_fields:
            self.__dict__["last_transaction"] = tran.id
        self.__dict__["status"] = Status.NORMAL

    def _syncdb_update(self, tran, update_fields=None):
        assert self.status == Status.DIRTY, "DIRTY 상태에서만 syncdb_update() 호출이 가능합니다."
        assert self._syncdb_required is True, "_syncdb_required 가 True 일때만 syncdb_update() 호출이 가능합니다."
        assert update_fields is None or len(update_fields) >= 2, "update_fields 파라메터가 잘못되었습니다."
        self._syncdb_required = False
        self._pre_syncdb_update(tran, update_fields)
        try:
            super().save(force_insert=False, force_update=True, using=None, update_fields=update_fields)
        except Exception as e:
            self._set_invalid_and_raise(e)
        self.init_variables()

    def _mark_delete(self):
        if self._status_before_delete is None:
            self._status_before_delete = self.status
        self._old_syncdb_required = self._syncdb_required
        self.__dict__["status"] = Status.DELETED
        tran = TransactionManager.get_transaction()
        tran._mark_delete(self)

    def delete(self, using=None, keep_parents=True):
        assert keep_parents is True, "keep_parents 는 지원하지 않습니다."
        assert using is None, "using 은 지원하지 않습니다."
        assert self.is_in_writable_transaction(), "해당 instance 가 수정 가능한 Transaction 내에 없습니다."
        self._mark_delete()
        self.save()
        if not self._old_syncdb_required:
            self.on_delete()

    def on_delete(self):
        pass

    def _pre_syncdb_delete(self, tran):
        self.__dict__["version"] += 1
        self.__dict__["last_transaction"] = tran.id

    def _syncdb_delete(self, tran):
        assert self.status == Status.DELETED, "DELETED 상태에서만 syncdb_delete() 호출이 가능합니다."
        assert self._syncdb_required is True, "_syncdb_required 가 True 일때만 syncdb_delete() 호출이 가능합니다."
        assert self._status_before_delete is not None, "_status_before_delete 이 세팅되지 않은 상태에서 호출되었습니다."
        self._syncdb_required = False
        self._pre_syncdb_delete(tran)
        if self._status_before_delete != Status.NEW:
            try:
                # TODO : 구조 리팩토링
                update_fields = ("version", "last_transaction", "status", "computed_uri_hash")
                super().save(force_insert=False, force_update=True, using=None, update_fields=update_fields)
            except Exception as e:
                self._set_invalid_and_raise(e)
        tran.remove(self)
        self.init_variables()

    def _destroy(self, using=None, keep_parents=True):
        assert using is None, "using 은 지원하지 않습니다."
        assert keep_parents is True, "keep_parents 는 지원하지 않습니다."
        assert self.status == Status.DELETED, "DELETED 상태에서만 _destroy() 호출이 가능합니다."
        assert self._syncdb_required is False, "_syncdb_required 가 False 일때만 _destroy() 호출이 가능합니다."
        if self._status_before_delete != Status.NEW:
            super().delete(using=None, keep_parents=True)
        self.init_variables()
        tran = TransactionManager.get_transaction()
        tran.clear_query_cache()
        tran.remove(self)
        self.__dict__["id"] = None

    def refresh_from_db(self, using=None, fields=None):
        raise AssertionError("refresh_from_db() 는 사용 금지입니다. get(id=id) 로 구현을 대체해야 합니다.")

    @classmethod
    def resolve_subfield_name(cls, subfield_name):
        subfields = cls.subfields
        try:
            return subfields["_wrapper"][subfield_name].subfield_name
        except KeyError:
            return subfield_name

    @classmethod
    def resolve_subfield_filters(cls, **kwargs):
        result = {}
        for subfield_filter_name, value in kwargs.items():
            resolved_subfield_filter_name, value = cls.resolve_subfield_filter_value(subfield_filter_name, value)
            result[resolved_subfield_filter_name] = value
        return result

    @classmethod
    def resolve_subfield_filter_names(cls, *subfield_filter_names):
        resolved_subfield_filter_names = [
            cls.resolve_subfield_filter_value(subfield_filter_name)[0] for subfield_filter_name in subfield_filter_names
        ]
        return resolved_subfield_filter_names

    @classmethod
    def resolve_subfield_filter_value(cls, subfield_filter_name, value=None):
        splited = subfield_filter_name.split(LOOKUP_SEP)
        if len(splited) >= 2:
            order_by, subfield_name = "", LOOKUP_SEP.join(splited[:-1])
            if subfield_name[0] == "-":
                order_by, subfield_name = subfield_name[0], subfield_name[1:]
            subfield_name = cls.resolve_subfield_name(subfield_name)
            lookup = splited[-1]
            resolved_subfield_filter_name = "{}{}{}{}".format(order_by, subfield_name, LOOKUP_SEP, lookup)
        else:
            subfield_name = subfield_filter_name
            resolved_subfield_filter_name = cls.resolve_subfield_name(subfield_filter_name)
        if value is not None and subfield_name in cls.subfields["_total"]:
            subfield = cls.get_subfield(subfield_name)
            if isinstance(subfield, ValueSubfield) and subfield.normalize:
                value = subfield.normalize(value)
        return resolved_subfield_filter_name, value
