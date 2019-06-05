from multiprocessing import Lock
from random import randrange
from datetime import datetime
from types import MappingProxyType

from django.utils.timezone import now, make_aware
from django.db.transaction import Atomic as DjangoAtomic, get_connection
from django.conf import settings

from base.enums import Status
from base.utils import console_log
from base.types import Type
from base.exceptions import InvalidInstanceException

KEY_EPOCH = 1546300800000  # timezone.datetime(2018, 1, 1).timestamp() * 1000 (millisecond)
KEY_LIMIT_TIMESTAMP = 2 ** 41
KEY_LIMIT_SEQ = 2 ** 14
KEY_LIMIT_FOR_UNIQUE = 2 ** 8
KEY_LIMIT = 9223372036854775807
KEY_LIMIT_SEQ_FOR_BULK_TRAN = 2 ** 22


def get_datetime_from_key(key):
    timestamp = (key >> 22) + KEY_EPOCH
    return make_aware(datetime.fromtimestamp(int(timestamp / 1000)))


#  1 bit : not used (sign bit)
# 41 bit : time in milliseconds with custom epoch (약 69.7년)
# 14 bit : sequence number in transaction. 즉, 약 16000 개의 신규 인스턴스 생성을 지원함
#  8 bit : for unique value with two more machines
class KeyGenerator(object):
    last_timestamp = 0
    last_timestamp_lock = Lock()

    def __init__(self):
        timestamp = int(now().timestamp() * 1000) - KEY_EPOCH
        cls = self.__class__
        with cls.last_timestamp_lock:
            if timestamp <= cls.last_timestamp:
                timestamp = cls.last_timestamp + 1
            cls.last_timestamp = timestamp
        assert timestamp < KEY_LIMIT_TIMESTAMP
        self.timestamp = timestamp
        self.seq = 0
        self.for_unique_value = None

    def __call__(self):
        seq, for_unique_value = self.seq, self.for_unique_value
        assert seq < KEY_LIMIT_SEQ
        if for_unique_value is None:
            for_unique_value = randrange(KEY_LIMIT_FOR_UNIQUE)
        result = self.timestamp << 22 | seq << 8 | for_unique_value
        assert 0 < result < KEY_LIMIT
        self.seq = seq + 1
        return result


#  1 bit : not used (sign bit)
# 41 bit : time in milliseconds with custom epoch
# 22 bit : sequence number in transaction (약 4백만)
class BulkTransactionKeyGenerator(KeyGenerator):
    def __init__(self):
        super().__init__()

    def __call__(self):
        seq = self.seq
        assert seq < KEY_LIMIT_SEQ_FOR_BULK_TRAN
        result = self.timestamp << 22 | seq
        assert 0 < result < KEY_LIMIT
        self.seq = seq + 1
        return result


# 안정적인 Repeatable Reads 격리 수준을 제공
# 당연히 여전히 Phantom Read 는 발생할 수 있음
# 따라서 의도적으로 범위검색은 트랜잭션 초반에만 실행하고... 이후에는 하지 않는 형태로 구현하는 습관을 들일 필요가 있음
class Transaction(DjangoAtomic):
    is_readonly = False

    def __init__(self, using=None, savepoint=True, checkin_actor=None, login_user=None):
        assert using is None, "using 지정은 지원하지 않습니다."
        if checkin_actor:
            assert checkin_actor.my_type.is_subtype_of(Type.Actor)
        if login_user:
            assert login_user.my_type.is_subtype_of(Type.User)
        super().__init__(using=None, savepoint=savepoint)
        self.connection = None
        self.is_outermost = None
        self.key_gen = None
        self.id = None
        self._checkin_actor = checkin_actor
        self._login_user = login_user if login_user else checkin_actor.user if checkin_actor else None
        # storage
        self.instances = {}
        self.uri_mapping = {}
        self._query_cache = {}
        self.tasks = {}
        self.status = {"is_dirty": False}

    def has_query_cache(self, sql):
        return sql in self._query_cache

    def get_query_cache(self, sql):
        return self._query_cache.get(sql, None)

    def set_query_cache(self, sql, result):
        assert result is not None
        if isinstance(result, list):
            result = tuple(result)
        if isinstance(result, dict):
            result = MappingProxyType(result)
        self._query_cache[sql] = result

    def clear_query_cache(self):
        self._query_cache.clear()

    @property
    def is_dirty(self):
        result = self.status["is_dirty"]
        # TODO : 버그 해결을 위한 임시 코드임. 반드시 튜닝할 것 (notify_status_changed 같은 걸 받아야 할 듯)
        result = None
        if result is None:
            result = any(
                instance
                for instance in self.instances.values()
                if instance.status not in (Status.NORMAL, Status.WORKING)
            )
            self.is_dirty = result
        return result

    @is_dirty.setter
    def is_dirty(self, v):
        assert isinstance(v, bool) or v is None
        self.status["is_dirty"] = v

    @property
    def checkin_actor(self):
        return self._checkin_actor

    @property
    def login_user(self):
        return self._login_user

    def checkin(self, actor):
        already_login_user, already_checkin_actor = (self._login_user, self._checkin_actor)
        if already_checkin_actor == actor:
            return
        assert already_checkin_actor is None
        assert actor and actor.my_type.is_subtype_of(Type.Actor)
        if not already_login_user and actor.user:
            self.login(actor.user)
        self._checkin_actor = actor
        for instance in [instance for instance in self.instances.values() if instance.status == Status.NEW]:
            assert instance.creator is None
            instance.creator = actor

    def checkout(self):
        self._checkin_actor = None

    def login(self, user):
        already_login_user = self._login_user
        if already_login_user == user:
            return
        assert already_login_user is None
        assert user and user.my_type.is_subtype_of(Type.User)
        self._login_user = user

    def logout(self):
        self._login_user = None
        if self._checkin_actor:
            self.checkout()

    def get(self, id=None, uri=None):
        assert id or uri
        if uri:
            return self.uri_mapping.get(uri, None)
        return self.instances.get(id, None)

    def set(self, instance):
        self.instances[instance.id] = instance
        uri = instance.uri
        if uri:
            self.uri_mapping[uri] = instance
            old_uri = instance._old_uri
            assert old_uri != uri
            if old_uri:
                del self.uri_mapping[old_uri]
        if instance.status not in (Status.NORMAL, Status.WORKING):
            self.is_dirty = True

    def _mark_delete(self, instance):
        assert instance.status == Status.DELETED
        if instance.id in self.instances:
            uri = instance.uri
            if uri:
                assert uri in self.uri_mapping
                del self.uri_mapping[uri]

    def remove(self, instance):
        if instance.id in self.instances:
            del self.instances[instance.id]
            uri = instance.uri
            if uri and uri in self.uri_mapping:
                del self.uri_mapping[uri]

    def connect_storage(self, outermost_transaction):
        self.instances = outermost_transaction.instances
        self.uri_mapping = outermost_transaction.uri_mapping
        self._query_cache = outermost_transaction._query_cache
        self.tasks = outermost_transaction.tasks
        self.status = outermost_transaction.status

    def _clear(self):
        self.clear_query_cache()
        self.instances.clear()
        self.uri_mapping.clear()
        self.tasks.clear()
        self.is_dirty = False

    def gen_key(self):
        return self.key_gen()

    @classmethod
    def create_key_generator(cls):
        return KeyGenerator()

    def prepare_transaction(self):
        # django DB connection 은 thread safe 함
        connection = get_connection(self.using)
        self.connection = connection
        outermost_transaction = getattr(connection, "outermost_transaction", None)
        is_self_outermost_transaction = outermost_transaction is None
        if is_self_outermost_transaction:
            assert getattr(connection, "tran_stack", []) == []
            self.is_outermost = True
            connection.outermost_transaction = self
            connection.tran_stack = [self]
            self.key_gen = self.create_key_generator()
            self.id = self.key_gen()
            checkin_actor, login_user = self.checkin_actor, self.login_user
            if checkin_actor:
                assert checkin_actor.status in (Status.NORMAL, Status.NEW)
                self.set(checkin_actor)
            if login_user:
                assert login_user.status in (Status.NORMAL, Status.NEW)
                self.set(login_user)
        else:
            self.is_outermost = False
            tran_stack = connection.tran_stack
            parent = tran_stack[-1]
            if not self.is_readonly:
                assert not parent.is_readonly, "ReadonlyTransaction 안에는 ReadonlyTransaction 만 들어올 수 있습니다"
            tran_stack.append(self)
            self.key_gen = outermost_transaction.key_gen
            self.id = outermost_transaction.id
            if not self._checkin_actor:
                self._checkin_actor = parent.checkin_actor
            if not self._login_user:
                self._login_user = parent._login_user
            self.connect_storage(outermost_transaction)

    def __enter__(self):
        self.prepare_transaction()
        super().__enter__()
        return self

    # TODO : 리팩토링
    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_outermost:
            new_exception = None
            if exc_value is None:
                try:
                    self._syncdb_instances()
                except Exception as e:
                    exc_type = e.__class__
                    exc_value = e
                    traceback = None
                    new_exception = e
            super().__exit__(exc_type, exc_value, traceback)
            self.finalize_transaction(exc_value)
            if new_exception:
                raise new_exception
        else:
            super().__exit__(exc_type, exc_value, traceback)
            self.finalize_transaction(exc_value)

    # TODO : 리팩토링
    def finalize_transaction(self, exc_value):
        connection = self.connection
        assert connection.tran_stack.pop() == self
        if self.is_outermost:
            assert connection.tran_stack == []
            assert connection.outermost_transaction == self
            connection.outermost_transaction = None
            self.is_outermost = False
            if not exc_value:
                self.execute_tasks()

    def check_dirty_or_new_instances_with_no_save(self):
        # TODO : 관련 구조 정리 후에 NEW 에 대해서도 체크
        problems = [
            instance
            for instance in self.instances.values()
            if not instance._syncdb_required and instance.status == Status.DIRTY
        ]
        assert not problems, console_log("값이 수정되었는데 save() 가 호출되지 않은 인스턴스가 존재합니다 : {}".format(problems))

    def check_invalid_instances(self):
        problems = [instance for instance in self.instances.values() if instance.status == Status.INVALID]
        if problems:
            raise InvalidInstanceException("INVALID 인스턴스가 존재하는데 syncdb 가 호출되었습니다.".format(problems))

    def _syncdb_instances(self, model=None):
        if settings.IS_UNIT_TEST:
            self.check_dirty_or_new_instances_with_no_save()
        self.check_invalid_instances()
        instances = [
            instance
            for instance in self.instances.values()
            if instance._syncdb_required and (not model or isinstance(instance, model))
        ]
        if self.is_readonly:
            assert len(instances) == 0, "ReadonlyTransaction 인데 save() 필요한 instance 가 존재합니다."
            return
        # for avoid dead-lock
        instances.sort(key=lambda instance: instance.id)
        for instance in instances:
            status = instance.status
            if status == Status.NEW:
                instance._syncdb_insert(self)
            elif status == Status.DELETED:
                instance._syncdb_delete(self)
            elif status == Status.DIRTY:
                instance._syncdb_update(self)
            else:
                raise AssertionError("허용되지 않는 status 값입니다.")
        # update is_dirty property
        self.is_dirty = False if model is None else None

    def execute_tasks(self):
        # TODO : 구현
        pass


class BulkTransaction(Transaction):
    MAX_INSTANCES_SIZE = 100000

    @classmethod
    def create_key_generator(cls):
        return BulkTransactionKeyGenerator()

    def set(self, instance):
        size = len(self.instances)
        if size >= self.MAX_INSTANCES_SIZE:
            assert not self.check_dirty_or_new_instances_with_no_save(), "값이 수정되었는데 save() 가 호출되지 않은 인스턴스가 존재합니다."
            self._syncdb_instances()
            self._clear()
        super().set(instance)


class ReadonlyTransaction(Transaction):
    is_readonly = True

    def __enter__(self):
        self.prepare_transaction()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        is_transaction_complete = exc_value is None and self.is_outermost
        self.finalize_transaction(is_transaction_complete)
        if is_transaction_complete:
            assert all(not instance._syncdb_required for instance in self.instances.values())


class _TryException(Exception):
    pass


class TryTransaction(Transaction):
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value is None:
            exc_type = _TryException
            exc_value = _TryException()
            if not settings.IS_UNIT_TEST:
                console_log("No error and transaction rollback successfully")
        super().__exit__(exc_type, exc_value, traceback)


class UnitTestTransaction(TryTransaction):
    pass


class BulkTestTransaction(BulkTransaction, UnitTestTransaction):
    pass


class TransactionManager(object):
    @staticmethod
    def get_transaction(using=None):
        connection = get_connection(using)
        try:
            tran_stack = connection.tran_stack
        except:
            tran_stack = []
            connection.tran_stack = tran_stack
        return tran_stack[-1] if tran_stack else None

    @staticmethod
    def get_checkin_actor():
        tran = TransactionManager.get_transaction()
        return tran.checkin_actor

    @staticmethod
    def get(id):
        tran = TransactionManager.get_transaction()
        return tran.get(id, None) if tran else None

    @staticmethod
    def set(instance):
        tran = TransactionManager.get_transaction()
        if tran:
            tran.set(instance)

    @staticmethod
    def remove(instance):
        tran = TransactionManager.get_transaction()
        if tran:
            tran.remove(instance)

    @staticmethod
    def _clear():
        tran = TransactionManager.get_transaction()
        tran._clear()

    @staticmethod
    def is_same_outermost_transaction(tran1, tran2):
        return (tran1 and tran1.id) == (tran2 and tran2.id)
