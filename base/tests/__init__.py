from unittest.case import skip, _id, _Outcome
from types import MappingProxyType

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import File as DjangoFile
from django.core import mail
from django.test import TestCase as DjangoTestCase

from base.transaction import Transaction, UnitTestTransaction, BulkTestTransaction, TransactionManager
from base.types import Type
from base.descriptors import ValueSubfield
from base.fields import ForceChanger
from base.utils import console_log
from base.exceptions import InvalidInstanceException
from base.managers import ModelManager


def only_full_test():
    if not settings.IS_FULL_TEST:
        return skip("only_full_test")
    return _id


def todo_test():
    return skip("TODO")


def get_uploaded_file(file_path):
    f = open(file_path, "rb")
    file = DjangoFile(f)
    uploaded_file = InMemoryUploadedFile(file, None, file_path, "text/plain", file.size, None, None)
    return uploaded_file


class AbstractTestCase(DjangoTestCase):
    def assertDictContainsSubset(self, subset, dictionary, msg=None):
        copied = {}
        copied.update(dictionary)
        copied.update(subset)
        if dictionary == copied:
            return
        self.fail(self._formatMessage(msg, "dictionary does not contains subset."))


class BaseTestCase(AbstractTestCase):
    def given(self):
        pass

    @property
    def tran(self):
        return TransactionManager.get_transaction()

    @property
    def last_email(self):
        return mail.outbox[-1] if mail.outbox else None

    def get_uploaded_file(self, file_path):
        return get_uploaded_file(file_path)

    def response_500(self, response=None):
        response = self._which_response(response)
        self.assertEqual(response.status_code, 500)

    @classmethod
    def get_tran_cls(cls):
        tran_cls_name = settings.OUTERMOST_TRANSACTION_NAME_FOR_TEST
        if tran_cls_name == "UnitTestTransaction":
            tran_cls = UnitTestTransaction
        else:
            assert tran_cls_name in ("Transaction", None)
            tran_cls = Transaction
        return tran_cls

    # TODO : 좀 더 나이스하게 정리
    # unittest.TestCase.run() 과 거의 동일. testMethod() 호출 부분을 Transaction 으로 감싼 것만 다름
    # TODO : connection already closed 문제 해결
    def run(self, result=None):
        orig_result = result
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, "startTestRun", None)
            if startTestRun is not None:
                startTestRun()

        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)
        if getattr(self.__class__, "__unittest_skip__", False) or getattr(testMethod, "__unittest_skip__", False):
            # If the class or method was skipped.
            try:
                skip_why = getattr(self.__class__, "__unittest_skip_why__", "") or getattr(
                    testMethod, "__unittest_skip_why__", ""
                )
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure_method = getattr(testMethod, "__unittest_expecting_failure__", False)
        expecting_failure_class = getattr(self, "__unittest_expecting_failure__", False)
        expecting_failure = expecting_failure_class or expecting_failure_method
        outcome = _Outcome(result)
        try:
            self._outcome = outcome
            tran = self.get_tran_cls()()
            with outcome.testPartExecutor(self):
                with tran:
                    self.setUp()
            if outcome.success:
                outcome.expecting_failure = expecting_failure
                with outcome.testPartExecutor(self, isTest=True):
                    try:
                        with tran:
                            self.given()
                            testMethod()
                    except InvalidInstanceException:
                        pass
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    self.tearDown()

            self.doCleanups()
            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if orig_result is None:
                stopTestRun = getattr(result, "stopTestRun", None)
                if stopTestRun is not None:
                    stopTestRun()

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None


class BaseNoTransactionTestCase(AbstractTestCase):
    pass


class BaseBulkTestCase(BaseTestCase):
    @classmethod
    def get_tran_cls(cls):
        return BulkTestTransaction


class SpecTestMixin(object):
    def input_from_user(self, v):
        return v

    def render(self, v):
        console_log(v)

    def input(self, *args, example=""):
        if settings.IS_UNIT_TEST:
            return example
        value = input(*args)
        return value

    def print(self, *args):
        console_log(*args)


class BaseSpecTestCase(BaseTestCase, SpecTestMixin):
    @classmethod
    def get_tran_cls(cls):
        return UnitTestTransaction


class BaseNoTransactionSpecTestCase(BaseNoTransactionTestCase, SpecTestMixin):
    pass


class ProxyModelTestMixin(object):
    @classmethod
    def get_proxy_model_class(cls):
        raise NotImplementedError

    def test_types(self):
        cls = self.get_proxy_model_class()
        assert cls.__name__ in [t.name for t in Type], "types.py 에 선언되어 있어야 합니다."
        assert cls.types
        assert type(cls.types) is tuple
        assert all([type(t) is Type for t in cls.types])
        assert cls.my_type.model is cls
        assert all([sub_model_type in cls.types for sub_model_type in cls.my_type.sub_types])
        assert cls.my_type is cls.types[0]
        assert all([cls.my_type in t.model.super_types for t in cls.types[1:]])

    def test_super_types(self):
        cls = self.get_proxy_model_class()
        assert cls.super_types
        assert type(cls.super_types) is tuple
        assert all([type(t) is Type for t in cls.super_types])
        for parent_type in cls.super_types:
            parent = parent_type.model
            assert parent in cls.mro()[1:]
        assert cls.super_types[0].model == cls.__base__
        assert cls.super_types[-1] == Type.Model
        assert all([cls.my_type in t.model.types for t in cls.super_types[:-1]])
        # Type value 가 자동 발번된 hash 로 바뀜에 따라 주석 처리
        # Proxy model 간 상속은 python class 상속으로 처리되고 있기 때문에 python 자체적으로 확인됨. 없어도 되는 테스트임
        # assert all([not cls.my_type or cls.my_type > t for t in cls.super_types])

    def test_no_conflict_subfields_with_parents(self):
        cls = self.get_proxy_model_class()
        for parent_type in cls.super_types:
            parent = parent_type.model
            parent_names = parent.subfield_names
            for k, v in cls.__dict__.items():
                if k in parent_names:
                    if isinstance(v, ValueSubfield):
                        parent_subfield = getattr(parent, k)
                        assert issubclass(type(v), type(parent_subfield))
                        assert v.field_name == parent_subfield.field_name
                        if isinstance(v.subfield_type, tuple):
                            assert isinstance(parent_subfield.subfield_type, tuple)
                            assert Type.issubclass(v.subfield_type[0], parent_subfield.subfield_type[0])
                        elif isinstance(v.subfield_type, MappingProxyType):
                            assert isinstance(parent_subfield.subfield_type, MappingProxyType)
                            for k2, v2 in v.subfield_type.items():
                                if k2 in parent_subfield.subfield_type:
                                    assert Type.issubclass(v2, parent_subfield.subfield_type[k2])
                        else:
                            assert Type.issubclass(v.subfield_type, parent_subfield.subfield_type)
                    else:
                        assert k not in parent_names

    def test_check_validation_subfields(self):
        cls = self.get_proxy_model_class()
        for lf in cls.subfields["_total_reverse"]:
            lf._check_validation()

    def _get_inited_instance(self):
        cls = self.get_proxy_model_class()
        return cls()

    def test_write(self):
        cls = self.get_proxy_model_class()
        if not cls.__dict__.get("ABSTRACT", False):
            assert cls.objects.count() == 0
            instance = self._get_inited_instance()
            assert cls.objects.count() == 0
            instance.save()
            assert cls.objects.count() == 1
            with ForceChanger(instance):
                instance.optimistic_lock_count += 1
            instance.save()
            assert cls.objects.count() == 1
            instance.delete()
            assert cls.objects.count() == 0
            instance._destroy()
            assert cls.objects.count() == 0
            assert instance.id is None
        else:
            with self.assertRaises(AssertionError):
                cls.objects.create()

    def test_check_not_overrided(self):
        cls = self.get_proxy_model_class()
        assert isinstance(cls.objects, ModelManager)
        assert "my_type" not in cls.__dict__
        assert "types" not in cls.__dict__
        assert "super_types" not in cls.__dict__
        assert "subfield_defaults" not in cls.__dict__


class LogicTestMixin(object):
    @classmethod
    def get_logic_class(cls):
        raise NotImplementedError

    def do(self):
        cls = self.get_logic_class()
        assert cls
        logic = cls()
        result = logic.do()
        assert result
        return result

    def test_do(self):
        assert self.do()
