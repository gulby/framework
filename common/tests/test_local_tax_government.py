from base.tests import BaseTestCase
from common.logics import InitializeLocalTaxGovernmentAndAddress
from common.models import Address, LocalTaxGovernment


class LocalTaxGovernmentTest(BaseTestCase):
    def setUp(self):
        logic = InitializeLocalTaxGovernmentAndAddress()
        logic.do()

    def test(self):
        address = Address.objects.get(address="경기도 가평군")
        local_tax_government = LocalTaxGovernment.objects.get(local_tax_government_name="가평군청")
        assert address.local_tax_government.uname == "가평군청"
        assert address.local_tax_government == local_tax_government

        local_tax_government2 = LocalTaxGovernment.objects.get(local_tax_government_name="오정구청")
        human_address1 = Address(address="경기도 부천시 오정구 여월동 316 여월휴먼시아5단지아파트").지번_address
        assert LocalTaxGovernment.get_by_human_address(human_address=human_address1) == local_tax_government2

        human_address2 = Address(address="서울특별시 서초구 반포대로22길 100 삼덕빌딩").지번_address
        local_tax_government3 = LocalTaxGovernment.get_by_human_address(human_address=human_address2)
        assert local_tax_government3.local_tax_government_name == "서초구청"

        human_address3 = Address(address="서울특별시 강남구 테헤란로 142").지번_address
        local_tax_government4 = LocalTaxGovernment.get_by_human_address(human_address=human_address3)
        assert local_tax_government4 is None

        human_address4 = Address(address="서울특별시 강남구 강남대로 382 메리츠타워").지번_address
        local_tax_government5 = LocalTaxGovernment.get_by_human_address(human_address=human_address4)
        assert local_tax_government5 is None

        local_tax_government6 = LocalTaxGovernment.objects.get(local_tax_government_name="오정구청")
        human_address5 = Address(address="경기도 부천시 여월동 316 여월휴먼시아5단지아파트").지번_address
        assert LocalTaxGovernment.get_by_human_address(human_address=human_address5) == local_tax_government6
