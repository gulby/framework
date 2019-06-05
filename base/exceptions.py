from django.db import DatabaseError, IntegrityError


class ApplicationException(Exception):
    pass


class OptimisticLockException(DatabaseError, ApplicationException):
    pass


class DuplicateUriException(IntegrityError, ApplicationException):
    pass


class InvalidRawDataException(ApplicationException):
    pass


class NoContentRawDataException(InvalidRawDataException):
    pass


class DamagedRawDataException(InvalidRawDataException):
    pass


class InvalidInstanceException(DatabaseError, ApplicationException):
    pass


class AuthenticationException(ApplicationException):
    pass


class CheckinException(AuthenticationException):
    pass


class NoErrorException(ApplicationException):
    pass
