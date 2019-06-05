from base.tests import BaseTestCase
from common.models import Address, LocalTaxGovernment
from common.logics import InitializeTaxOffice, InitializeLocalTaxGovernmentAndAddress


class AddressTest(BaseTestCase):
    def setUp(self):
        InitializeTaxOffice().do()
        InitializeLocalTaxGovernmentAndAddress().do()

    def test(self):
        address1 = Address(address="서울특별시 서초구 반포대로 22길 100")
        tax_office = address1.tax_office

        assert tax_office.code == 214
        assert tax_office.account_number == 180658
        assert address1.road_name == "반포대로22길"
        assert address1.zip_code == "06650"

        assert LocalTaxGovernment.get_by_human_address(address1.지번_address) == LocalTaxGovernment.objects.get(
            uname="서초구청"
        )
