from enum import unique, IntEnum
from types import MappingProxyType


@unique
class Expire(IntEnum):
    ON_CALL = -2  # TODO : 구현
    ON_CHANGE = -1
    NONE = 0


@unique
class Status(IntEnum):
    NO_SYNC = -2  # DB 저장 없이 메모리 상에서만 사용하는 상태. 장고 어드민 등 기존 장고와의 호환성을 위해 도입
    INVALID = -1  # refresh 가 필요함. 롤백된 경우 등
    DELETED = 0  # 삭제됨
    CREATING = 1  # 생성 중
    NEW = 2  # 최초 인스턴스가 생성된 상태
    NORMAL = 10  # DB 와 같음
    WORKING = 11  # 작업중 상태
    DIRTY = 20  # DB 와 달라짐. save() 가 필요한 상태

    def check_route(self, to):
        return to in STATUS_GRAPH[self]


def set_invalid_on_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self = args[0]
            self._set_invalid_and_raise(e)

    return wrapper


STATUS_GRAPH = MappingProxyType(
    {
        Status.CREATING: (Status.NEW,),
        Status.NEW: (Status.NORMAL, Status.DELETED),
        Status.DIRTY: (Status.NORMAL, Status.DELETED, Status.WORKING),
        Status.NORMAL: (Status.DIRTY, Status.DELETED, Status.WORKING),
        Status.WORKING: (Status.DIRTY, Status.DELETED, Status.NORMAL),
        Status.DELETED: (),
        Status.INVALID: (),
        Status.NO_SYNC: (),
    }
)
