from base.tests import BaseTestCase
from common.logics import InitializeTaxOffice
from common.models import Address


class GetTaxOfficeTest(BaseTestCase):
    def given(self):
        InitializeTaxOffice().do()

    def test(self):
        address1 = Address(address="인천광역시 중구 운서2로 31")
        tax_office = address1.tax_office

        assert tax_office.code == 121
        assert tax_office.account_number == 110259
        assert address1.road_name == "운서2로"
        assert tax_office.uname == "인천세무서"

    def test2(self):
        address1 = Address(address="인천광역시 중구 운서동 2886-13")
        tax_office = address1.tax_office

        assert tax_office.code == 121
        assert tax_office.account_number == 110259
        assert address1.road_name == "운서2로"

    def test_get_tax_office_name(self):
        address1 = Address(address="인천광역시 중구 운서동 2886-13")
        tax_office = address1.tax_office
        assert tax_office.uname == "인천세무서"

        address2 = Address(address="인천광역시 중구 운서2로 31")
        tax_office2 = address2.tax_office
        assert tax_office2.uname == "인천세무서"

        address3 = Address(address="서울특별시 서초구 반포대로 22길 100")
        tax_office3 = address3.tax_office
        assert tax_office3.uname == "서초세무서"

        address4 = Address(address="경기도 화성시 영통로50번길 3")
        tax_office4 = address4.tax_office
        assert tax_office4.uname == "동수원세무서"

        address5 = Address(address="경기도 부천시 오정구 여월동 316")
        tax_office5 = address5.tax_office
        assert tax_office5.uname == "부천세무서"

        address6 = Address(address="경기도 부천시 원미로 144번길 45")
        tax_office6 = address6.tax_office
        assert tax_office6.uname == "부천세무서"
