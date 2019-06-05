from django.db.models import Model as DjangoModel
from django.db.models import BigIntegerField, SmallIntegerField, IntegerField, UUIDField, BigAutoField

from base.fields import JSONField, ArrayField


class ModelHistory(DjangoModel):
    class Meta:
        unique_together = (("id", "history_id"),)

    # History fields
    history_id = BigAutoField(primary_key=True)
    history_transaction = BigIntegerField(null=False)

    # AbstractModel fields
    id = BigIntegerField(null=False)
    status = SmallIntegerField(null=False)
    version = IntegerField(null=False)
    last_transaction = BigIntegerField(null=False)

    # Model fields
    type = IntegerField(null=False)
    optimistic_lock_count = IntegerField(null=False)
    data = JSONField(null=False)

    # Model fields : not required
    # 디버깅 목적으로 켜서 저장을 해야 할 수도 있기 때문에 null=True 로 컬럼을 만들어 둔다
    computed = JSONField(null=True)
    raw = JSONField(null=True)
    computed_uri_hash = UUIDField(null=True)
    computed_owner_id = BigIntegerField(null=True)
    computed_container_id = BigIntegerField(null=True)
    computed_proprietor_id = BigIntegerField(null=True)
    computed_search_array = ArrayField(BigIntegerField(), null=True)
