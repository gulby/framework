from base.tests import BaseTestCase
from common.logics import InitializeLocalTaxGovernmentAndAddress
from common.models import LocalTaxGovernment


class HeadQuarterPositionNameTest(BaseTestCase):
    def setUp(self):
        InitializeLocalTaxGovernmentAndAddress().do()

    def test(self):
        local_tax_gov = LocalTaxGovernment.objects.get(uname="오정구청")
        assert local_tax_gov.headquarter_position_name == "오정구청장"

        local_tax_gov2 = LocalTaxGovernment.objects.get(uname="오산시청")
        assert local_tax_gov2.headquarter_position_name == "오산시장"

        local_tax_gov3 = LocalTaxGovernment.objects.get(uname="가평군청")
        assert local_tax_gov3.headquarter_position_name == "가평군수"

        local_tax_gov4 = LocalTaxGovernment.objects.create(uname="경기도청")
        assert local_tax_gov4.headquarter_position_name == "경기도지사"
