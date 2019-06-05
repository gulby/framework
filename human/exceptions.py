from base.exceptions import ApplicationException, AuthenticationException, CheckinException

assert CheckinException


class PasswordNotMatchException(AuthenticationException):
    pass


class PasswordExpiredException(AuthenticationException):
    pass


class RegisterException(ApplicationException):
    pass


class DuplicateIdException(ApplicationException):
    pass


class DuplicateEmailException(ApplicationException):
    pass


class SMTPDataError(ApplicationException):
    pass


class DuplicateNameException(ApplicationException):
    pass
