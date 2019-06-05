from django.db.models.manager import BaseManager
from django.db.models import QuerySet as DjangoQuerySet

from base.enums import Status
from base.queryset import QuerySet


class ModelManager(BaseManager.from_queryset(QuerySet)):
    def __init__(self):
        super().__init__()
        self.instance = None
        # False 이면 self 가 source, True 이면 self 가 target (is_source 는 self 가 아니라 subfield 의 속성)
        self.reverse = None
        self.rel_type = None
        self.multiplicity = None
        self.target_field_name = None  # for avoid pycharm warning
        self.subfield = None
        self.related_subfield = None

    def process_queryset(self, qs):
        types = self.model.types
        if types:
            qs = qs.filter(type__in=types)
        return qs

    def get_queryset(self):
        qs = super().get_queryset().filter(status__in=(Status.NORMAL, Status.WORKING))
        return self.process_queryset(qs)

    def get_deleted(self, *args, **kwargs):
        kwargs = self.model.resolve_subfield_filters(**kwargs)
        assert kwargs["id"], "get_deleted() 호출 시에는 id 값을 넘겨야 합니다."
        qs = DjangoQuerySet(self.model)
        qs = qs.filter(status=Status.DELETED)
        qs = self.process_queryset(qs)
        instance = qs.get(*args, **kwargs)
        if instance.status != Status.DELETED:
            raise instance.__class__.DoesNotExist
        instance._old_status = Status.DELETED
        return instance

    def create(self, **kwargs):
        model = self.model
        kwargs = model.resolve_subfield_filters(**kwargs)
        obj = model(**kwargs)
        self._for_write = True
        assert obj.status in (Status.CREATING, Status.NEW), "인스턴스 생성이 최종 완료되기 전에 다른 곳에서 save() 가 먼저 호출되었습니다."
        obj.save()
        return obj

    def get_or_create(self, is_update_if_exist=False, **kwargs):
        model = self.model
        kwargs = model.resolve_subfield_filters(**kwargs)
        keys = {}
        for key in model.UNIQUE_KEY_SUBFIELD_NAMES + model.PSEUDO_KEY_SUBFIELD_NAMES:
            if key in kwargs:
                keys[key] = kwargs.pop(key)
        try:
            instance, is_create = self.get(**keys), False
            if is_update_if_exist:
                instance.patch(**kwargs)
                instance.save()
        except model.DoesNotExist:
            # uname 이 DerivedUnameSubfield 인 경우 kwargs 에 의해 계산되기 때문에 keys 보다 kwargs 가 먼저 전달되어야 한다.
            instance, is_create = self.create(**kwargs, **keys), True
        return instance, is_create
