from base.tests import BaseTestCase, ProxyModelTestMixin
from common.models import Address, TaxOffice, LocalTaxGovernment, Board, Post, Country
from common.logics import InitializeTaxOffice


class CountryTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Country


class AddressTest(ProxyModelTestMixin, BaseTestCase):
    def given(self):
        InitializeTaxOffice().do()

    @classmethod
    def get_proxy_model_class(cls):
        return Address

    def _get_inited_instance(self):
        cls = self.get_proxy_model_class()
        return cls(address="경기도 화성시 영통로50번길 27")


class TaxOfficeTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return TaxOffice


class LocalTaxGovernmentTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return LocalTaxGovernment


class BoardTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Board


class PostTest(ProxyModelTestMixin, BaseTestCase):
    @classmethod
    def get_proxy_model_class(cls):
        return Post

    def _get_inited_instance(self):
        board = Board.objects.create()
        cls = self.get_proxy_model_class()
        return cls(title="게시글~", board=board)
