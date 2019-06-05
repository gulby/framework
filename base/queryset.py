from types import MappingProxyType

from django.db.models import QuerySet as DjangoQuerySet, BigIntegerField, Sum, FloatField, Q
from django.db.models.expressions import Func
from django.db.models.functions import Cast
from django.db.models.lookups import Exact, In
from django.db.models.fields.related_lookups import RelatedExact
from django.core.exceptions import FieldError, EmptyResultSet
from django.db import DEFAULT_DB_ALIAS
from django.utils.functional import cached_property
from django.conf import settings
from django.db.models.query import ModelIterable

from base.transaction import TransactionManager
from base.fields import KeyTextTransform, SF, SQ
from base.utils import console_log, file_log, isnull
from base.constant import LOOKUP_SEP, CHUNK_SIZE, MAX_QUERYSET_SIZE
from base.types import Type
from base.enums import Status
from base.models import AbstractModel
from base.descriptors.value_subfields import ListSubfieldHelper

# 원래 django.db.models.sql.constants 에 있었으나 장고 버전 2.1 이 되면서 사라져서 여기에 넣음
QUERY_TERMS = {
    "exact",
    "iexact",
    "contains",
    "icontains",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "range",
    "year",
    "month",
    "day",
    "week_day",
    "hour",
    "minute",
    "second",
    "isnull",
    "search",
    "regex",
    "iregex",
}


def _contains(a, b):
    if type(b) in (list, tuple, ListSubfieldHelper):
        return all(item in a for item in b)
    return b in a


def _in(a, b):
    if type(a) in (list, tuple, ListSubfieldHelper):
        return all(item in b for item in a)
    return a in b


def eq(a, b):
    a = a.id if isinstance(a, AbstractModel) else a
    b = b.id if isinstance(b, AbstractModel) else b
    return a == b


def lt(a, b):
    if a is None or b is None:
        return False
    return a < b


def lte(a, b):
    if a is None or b is None:
        return False
    return a <= b


def gt(a, b):
    if a is None or b is None:
        return False
    return a > b


def gte(a, b):
    if a is None or b is None:
        return False
    return a >= b


RESOLVER = {
    "exact": eq,
    "iexact": lambda a, b: a.lower() == b.lower(),
    "gt": gt,
    "gte": gte,
    "lt": lt,
    "lte": lte,
    "contains": _contains,
    "icontains": lambda a, b: b.lower() in a.lower(),
    "in": _in,
    "startswith": lambda a, b: a.startswith(b),
    "istartswith": lambda a, b: a.lower().startswith(b.lower()),
    "endswith": lambda a, b: a.endswith(b),
    "iendswith": lambda a, b: a.lower().endswith(b.lower()),
    "range": lambda a, b: b[0] <= a <= b[1],
    "year": lambda a, b: a.year == b,
    "month": lambda a, b: a.month == b,
    "day": lambda a, b: a.day == b,
    "isnull": lambda a, b: (not a and b) or (a and not b),
}


# TODO : get 말고도 instance 를 얻어내는 다른 방법들에 TransactionStorage 에서 선조회
class QuerySet(DjangoQuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None, cache=None):
        super().__init__(model, query, using, hints)
        self._result_cache = cache
        self.tran = TransactionManager.get_transaction()
        self._filters = []

    @cached_property
    def json(self):
        return [v.mjson for v in self]

    def _clone(self):
        c = super()._clone()
        c.tran = self.tran
        c._filters = list(self._filters)
        return c

    def assert_transaction(self):
        tran = TransactionManager.get_transaction()
        self_tran = self.tran
        if tran:
            assert TransactionManager.is_same_outermost_transaction(
                self_tran, tran
            ), "outermost transaction 이 일치하지 않습니다."

    def get(self, *args, **kwargs):
        kwargs = self.model.resolve_subfield_filters(**kwargs)
        tran = self.tran
        if tran:
            instance_id = self.find_id(*args, **kwargs)
            if instance_id:
                instance = tran.get(id=instance_id)
                if instance:
                    return instance
            uri = self.find_uri(*args, **kwargs)
            if uri:
                instance = tran.get(uri=uri)
                if instance:
                    return instance
        instance = self._super_get(*args, **kwargs)
        tran and tran.set(instance)
        return instance

    # 장고 내부 구현은 불필요한 부분 및 잘못된 호출에 대한 안전 장치가 없어 수정함
    def _super_get(self, *args, **kwargs):
        results = self.filter(*args, **kwargs)[:2]
        num = len(results)
        if num == 1:
            return results[0]
        if not num:
            raise self.model.DoesNotExist("%s matching query does not exist." % self.model._meta.object_name)
        raise self.model.MultipleObjectsReturned(
            "get() returned more than one %s -- it returned %s!" % (self.model._meta.object_name, num)
        )

    def find_id(self, *args, **kwargs):
        if "id" in kwargs:
            return kwargs["id"]
        elif "pk" in kwargs:
            return kwargs["pk"]
        for a in args:
            # TODO: cover 하는 테스트 작성
            for c in a.children:
                if c[0] in ("id", "pk"):
                    return c[1]
        for w in self.query.where.children:
            if type(w) is Exact and w.lhs.alias == "base_model" and w.lhs.field.attname in ("id", "pk"):
                return w.rhs
        return None

    def find_uri(self, *args, **kwargs):
        if "uri" in kwargs:
            return kwargs["uri"]
        elif "uname" in kwargs:
            return self.model.convert_uri(kwargs["uname"])
        # TODO : DB query case 에서도 uri 를 찾아 처리
        return None

    def using(self, alias):
        qs = super().using(alias)
        if self._result_cache is not None and (alias or DEFAULT_DB_ALIAS) == (self._db or DEFAULT_DB_ALIAS):
            qs._result_cache = self._result_cache
        return qs

    def allow_db_sorting(self, *ordering_names):
        # aggregation query 인 경우 db sorting 허용
        if not issubclass(self._iterable_class, ModelIterable):
            return True
        # parameter 가 넘어오지 않은 경우 현재까지 세팅된 order_by 에 대한 체크 진행
        if not ordering_names:
            ordering_names = self.query.order_by
        # sorting 을 하지 않는 경우는 db sorting 허용 (그냥 disk 상에 저장된 순서 sorting 사용)
        if not ordering_names:
            return True
        # id 정렬인 경우 db sorting 허용
        if len(ordering_names) == 1 and ordering_names[0] in ("id", "-id", "pk", "-pk"):
            return True
        # 그 이외의 경우는 db sorting 허용하지 않음. 정렬 없이 MAX_QUERYSET_SIZE 만큼만 가져와서 웹서버단에서 소팅 진행
        return False

    def order_by(self, *ordering_names):
        tran = self.tran
        if not tran and self._result_cache is None:
            return self._super_order_by(*ordering_names)

        ordering_names = self.model.resolve_subfield_filter_names(*ordering_names)
        reverse = ordering_names[0][0] == "-" if ordering_names else None

        # pre-condition check
        if reverse:
            assert all([ordering_name[0] == "-" for ordering_name in ordering_names]), "모두 ASC 이거나 모두 DESC 여야 합니다."
        else:
            assert all([ordering_name[0] != "-" for ordering_name in ordering_names]), "모두 ASC 이거나 모두 DESC 여야 합니다."
        if isinstance(self.model, Type.Model.model):
            assert any(
                [
                    unique_key[1:] if unique_key[0] == "-" else unique_key in ordering_names
                    for unique_key in self.model.UNIQUE_KEY_SUBFIELD_NAMES
                ]
            ), "order_by() 호출은 반드시 deterministic 해야 합니다."

        # subfield --> field
        for i, ordering_name in enumerate(ordering_names):
            order_by = "-" if ordering_name[0] == "-" else ""
            ordering_name = ordering_name[1:] if ordering_name[0] == "-" else ordering_name
            subfield_name = ordering_name.split(LOOKUP_SEP)[0]
            if subfield_name in self.model.subfield_names:
                subfield = getattr(self.model, subfield_name)
                ordering_names[i] = "{}{}__{}".format(order_by, subfield.field_name, ordering_name)

        # super
        qs = self._super_order_by(*ordering_names)

        # cache
        if self._result_cache is not None:
            self.assert_transaction()
            qs._result_cache = list(self._result_cache)
            if ordering_names:
                qs._result_cache.sort(
                    key=lambda instance: [
                        isnull(getattr(instance, field if not reverse else field[1:])) for field in ordering_names
                    ],
                    reverse=reverse,
                )

        return qs

    def _super_order_by(self, *ordering_names):
        return super().order_by(*ordering_names)

    def last(self, *args):
        raise NotImplementedError("last() 대신 order_by() 와 first() 를 사용하세요.")

    def reverse(self):
        raise NotImplementedError("reverse() 대신 명시적으로 order_by() 를 사용하세요.")

    def first(self, *args):
        qs = self
        if args:
            qs = qs.order_by(*qs.model.resolve_subfield_filter_names(*args))
        assert qs.is_ordered_explicitly(), "order_by 기준을 파라메터로 넘겨 주세요."

        if qs._result_cache is not None:
            return qs._result_cache[0] if qs._result_cache else None
        else:
            return qs._super_first()

    def _super_first(self):
        return super().first()

    def values(self, *fields, **expressions):
        qs = self
        for f in fields:
            if f in self.model.subfield_names:
                subfield_name, _ = self.model.resolve_subfield_filter_value(f)
                if subfield_name not in self.query.annotations:
                    qs = qs.annotate(**{subfield_name: SF(subfield_name)})
        return qs._super_values(*fields, **expressions)

    def _super_values(self, *fields, **expressions):
        self._syncdb_instances()
        return super().values(*fields, **expressions)

    def resolve_SF(self, sf):
        model, subfield_name = self.model, sf.name
        subfield = getattr(model, subfield_name)
        result = KeyTextTransform(subfield_name, subfield.field_name)
        try:
            subfield_type = subfield.subfield_type
            if issubclass(subfield_type, int):
                result = Cast(result, BigIntegerField())
            elif issubclass(subfield_type, float):
                result = Cast(result, FloatField())
        except TypeError:
            pass
        return result

    def update_SQ(self, args):
        def helper(children):
            for i, child in enumerate(children):
                if isinstance(child, tuple):
                    filter_name, value = child[0], child[1]
                    subfield_name = filter_name.split("__")[0]
                    if subfield_name in model.subfield_names:
                        subfield = getattr(model, subfield_name)
                        q.children[i] = ("{}__{}".format(subfield.field_name, filter_name), value)
                elif isinstance(child, SQ):
                    helper(child.children)
                else:
                    assert isinstance(child, Q)

        model = self.model
        for q in args:
            if isinstance(q, SQ):
                helper(q.children)

    def annotate(self, *args, **kwargs):
        kwargs, model = self.model.resolve_subfield_filters(**kwargs), self.model
        for k, p in kwargs.items():
            if isinstance(p, SF):
                if k in model.subfield_names:
                    assert k == p.name, "subfield annotation() 시에는 name 이 일치해야 합니다."
                kwargs[k] = self.resolve_SF(p)
            elif isinstance(p, Func):
                exprs = p.get_source_expressions()
                for i, expr in enumerate(exprs):
                    if isinstance(expr, SF):
                        expr = self.resolve_SF(expr)
                        exprs[i] = expr
                p.set_source_expressions(exprs)
        return super().annotate(*args, **kwargs)

    def _clean_lookups_for_subfield(self, filters):
        lookups = []
        for raw, value in filters.items():
            parts = raw.split(LOOKUP_SEP)
            if not parts:
                raise FieldError("Cannot parse keyword query %r" % raw)
            if len(parts) == 1 or parts[-1] not in QUERY_TERMS:
                lookup_type = "exact"
            else:
                lookup_type = parts.pop()
            assert lookup_type in RESOLVER, "미구현된 RESOLVER 가 있습니다. gulby 한테 연락해 주세요."
            lookups.append((parts, value, lookup_type, raw))
        return lookups

    def _clean_lookups_for_cached_queryset(self, filters):
        lookups = []
        for raw, value in filters.items():
            parts = raw.split(LOOKUP_SEP)
            if not parts:
                raise FieldError("Cannot parse keyword query %r" % raw)
            if len(parts) == 1 or parts[-1] not in QUERY_TERMS:
                lookup_type = "exact"
            else:
                lookup_type = parts.pop()
            assert lookup_type in RESOLVER, "미구현된 RESOLVER 가 있습니다. gulby 한테 연락해 주세요."
            # json field 및 Relation 처리
            attr = LOOKUP_SEP.join(parts)
            if parts[0] in ("data", "computed", "raw"):
                parts = [attr]
            # TODO : 추후 table join 에 대해서도 cachedqueryset 이 동작하도록 하기?
            elif parts[0] not in self.model.field_names:
                return None
            # TODO : 이 케이스를 줄여 최대한 튜닝하기
            if len(parts) >= 2:
                return None
            lookups.append((parts, value, lookup_type, raw))
        return lookups

    def _super_filter_or_exclude(self, negate, *args, **kwargs):
        return super()._filter_or_exclude(negate, *args, **kwargs)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        model = self.model

        # update SQ : SQ 를 resolve 하면서 in-place 로 수정함
        if args:
            self.update_SQ(args)

        # resolve kwargs
        kwargs = model.resolve_subfield_filters(**kwargs)

        # lookups for subfield
        lookups = self._clean_lookups_for_subfield(kwargs)

        # qs
        qs = self

        # Subfield
        for parts, value, lookup_type, raw in lookups or ():
            if parts[0] in model.subfield_names:
                subfield = getattr(model, parts[0])
                converted_filter = subfield.convert_filter(model, parts, value, lookup_type, raw)
                if lookup_type in ("lt", "lte"):
                    exclude_filter = {"{}__{}".format(subfield.field_name, LOOKUP_SEP.join(parts)): None}
                    qs = qs.exclude(**exclude_filter)
                del kwargs[raw]
                kwargs.update(converted_filter)

        # super
        qs = qs._super_filter_or_exclude(negate, *args, **kwargs)

        # lookups for cached queryset
        lookups = self._clean_lookups_for_cached_queryset(kwargs)

        # cache
        if issubclass(self._iterable_class, ModelIterable) and self._result_cache is not None:
            self.assert_transaction()
            new_cache = self._result_cache
            for parts, value, lookup_type, raw in lookups:
                attr = LOOKUP_SEP.join(parts)
                new_cache = [obj for obj in new_cache if RESOLVER[lookup_type](getattr(obj, attr), value) is not negate]
            qs._result_cache = new_cache

        # return
        assert isinstance(args, tuple)
        qs._filters.append((negate, args, MappingProxyType(kwargs)))
        return qs

    def check_required_filters(self):
        if not settings.IS_CHECK_PERFORMANCE_PROBLEM:
            return True
        filters = set()
        for w in self.query.where.children:
            type_w = type(w)
            if type_w in (Exact, In, RelatedExact):
                field_name = w.lhs.field.name
                if field_name in ("id", "pk"):
                    return True
                else:
                    filters.add(field_name)
        if self.model == Type.Model.model:
            # Model 에 대해서는 차라리 type 에 대해 filter 를 걸지 않는 것이 더 좋음
            filters.add("type")
        result = any(required.issubset(filters) for required in self.model.required_filters)
        return result

    @cached_property
    def sql(self):
        return str(self.query)

    def _fetch_all(self):
        # 트랜잭션 밖인 경우 혹은 ModelIterate 가 아닌 경우 : DjangoQuerySet 과 동일하게
        tran = self.tran
        if not tran or not issubclass(self._iterable_class, ModelIterable):
            self._super_fetch_all()
            return

        self.assert_transaction()
        assert self.check_required_filters()

        # fetch_all() 이 이미 실행된 경우
        if self._result_cache is not None:
            self._super_fetch_all()
            return

        # key == sql
        try:
            qs = self._chain()
            if self.is_ordered_explicitly() and not self.allow_db_sorting():
                qs.query.clear_ordering(force_empty=True)
            sql = qs.sql
        except EmptyResultSet:
            self._result_cache = []
            self._super_fetch_all()
            return

        # read from cache
        assert sql
        if tran.has_query_cache(sql):
            cached = tran.get_query_cache(sql)
            self._result_cache = cached
            assert self._result_cache is not None

        # truncated queryset 처리
        if self._result_cache is None and self.is_ordered_explicitly() and not self.allow_db_sorting():
            qs = self._chain()
            qs.query.clear_ordering(force_empty=True)
            truncated = qs[:MAX_QUERYSET_SIZE]
            truncated._fetch_all()
            assert truncated._result_cache is not None
            self._result_cache = truncated._result_cache
            if len(self) >= MAX_QUERYSET_SIZE:
                if settings.IS_UNIT_TEST:
                    assert False
                else:
                    file_log("id 정렬이 아닌 case 에서 MAX_QUERYSET_SIZE 를 넘는 쿼리 결과가 존재합니다.")
            truncated = None
            qs = None

        # default
        self._super_fetch_all()
        assert self._result_cache is not None

        # 아직 db 로 sync 되지 않고 Transaction Storage 에만 있는 instances 처리
        if tran.is_dirty:
            instances = [
                ins for ins in tran.instances.values() if isinstance(ins, self.model) and ins.status != Status.DELETED
            ]
            tqs = QuerySet(self.model)
            tqs._result_cache = list(instances)
            for _negate, _args, _kwargs in self._filters:
                if _args:
                    # 장고 내부적으로 활용되는 id 로의 조회만 예외 처리
                    # TODO : Q 에 대한 제대로 된 구현
                    if (
                        len(_args) == 1
                        and _args[0].connector == "AND"
                        and len(_args[0].children) == 1
                        and _args[0].children[0][0] == "id"
                    ):
                        _kwargs = dict(_kwargs)
                        _kwargs["id"] = _args[0].children[0][1]
                    else:
                        raise NotImplementedError("Q 에 대한 Transaction Storage 에서의 query 는 아직 미구현 상태입니다.")
                if "status__in" in _kwargs:
                    statuses = _kwargs["status__in"]
                    if Status.NORMAL in statuses:
                        statuses = tuple(set(list(statuses) + [Status.DIRTY, Status.NEW]))
                        _kwargs = dict(_kwargs)
                        _kwargs["status__in"] = statuses
                tqs = tqs._filter_or_exclude(_negate, *_args, **_kwargs)
            assert tqs._result_cache is not None
            self._result_cache = tqs._result_cache
            tqs = None

        # ordering
        ordering_names = self.query.order_by
        if ordering_names:
            qs = QuerySet(self.model)
            qs._result_cache = self._result_cache
            qs = qs.order_by(*ordering_names)
            assert qs._result_cache is not None
            self._result_cache = qs._result_cache
            qs = None

        # limit
        low_mark, high_mark = self.query.low_mark, self.query.high_mark or MAX_QUERYSET_SIZE
        assert high_mark <= MAX_QUERYSET_SIZE
        if low_mark == 0 and high_mark == MAX_QUERYSET_SIZE:
            pass
        else:
            assert self._result_cache is not None
            self._result_cache = self._result_cache[low_mark:high_mark]

        # insert to cache
        tran.set_query_cache(sql, self._result_cache)

    def __getitem__(self, k):
        if isinstance(k, slice) and k.step:
            raise NotImplementedError("step 기능은 구현하지 않았으며, 허용하지 않습니다.")
        if self.is_ordered_explicitly() and not self.allow_db_sorting():
            self._fetch_all()
        return super().__getitem__(k)

    def is_ordered_explicitly(self):
        if self.query.extra_order_by:
            raise NotImplementedError
        return bool(self.query.order_by)

    def _super_fetch_all(self):
        super()._fetch_all()

    def _syncdb_instances(self):
        tran = self.tran
        if tran:
            tran._syncdb_instances(model=self.model)

    def count(self):
        self.assert_transaction()
        if self._result_cache is not None:
            return len(self._result_cache)
        tran = self.tran
        if not tran:
            return self._super_count()

        # sql
        try:
            qs = self._chain()
            qs.query.clear_ordering(force_empty=True)
            sql = qs.sql
            qs = None
        except EmptyResultSet:
            self._result_cache = []
            return 0

        # cache
        cached = tran.get_query_cache(sql)
        if cached:
            return cached

        # DB
        result = self._super_count()
        tran.set_query_cache(sql, result)
        return result

    def _super_count(self):
        self._syncdb_instances()
        return super().count()

    def aggregate(self, *args, **kwargs):
        self._syncdb_instances()
        return super().aggregate(*args, **kwargs)

    def sum(self, subfield_name):
        subfield_name, _ = self.model.resolve_subfield_filter_value(subfield_name)
        annotated = self.annotate(**{subfield_name: SF(subfield_name)})
        result = annotated.aggregate(Sum(subfield_name))["{}__sum".format(subfield_name)] or 0
        return result

    # check_required_filters() 를 회피하고 Transaction Cache 를 무시하고 무조건 DB call 을 하여 결과를 가져온다.
    # 오직 개발 디버깅용으로만 활용할 것
    def _all(self):
        assert settings.DEPLOYMENT_LEVEL not in ("staging", "production")
        qs = self._chain()
        qs._super_fetch_all()
        return qs

    # Django 의 iterator 도 chunk 처리를 하지만 Queryset 이 너무 크면 chunk 처리를 해도 문제임
    def hugh_iterator(self, chunk_size=CHUNK_SIZE):
        assert issubclass(self._iterable_class, ModelIterable)
        assert self.query.order_by in ((), ("id",)), console_log(
            "hugh_iterator() 가 허용되지 않는 order_by 가 적용되었습니다.", self.query.order_by
        )
        assert self.query.extra_order_by == (), console_log(
            "hugh_iterator() 가 허용되지 않는 extra_order_by 가 적용되었습니다.", self.query.extra_order_by
        )
        last_id = 0
        last_index_in_chunk = chunk_size - 1
        qs = None
        qs_last_index = None
        total_count = self.count()
        for i in range(total_count):
            last_index_in_chunk += 1
            if last_index_in_chunk >= chunk_size:
                last_index_in_chunk = 0
                qs = self.filter(id__gt=last_id).order_by("id")[:chunk_size]
                qs_last_index = len(qs) - 1
            if last_index_in_chunk <= qs_last_index:
                instance = qs[last_index_in_chunk]
                last_id = instance.id
                yield instance
