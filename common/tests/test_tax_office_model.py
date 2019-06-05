from base.tests import BaseTestCase
from common.models import TaxOffice
from common.logics import InitializeTaxOffice


class TaxOfficeTest(BaseTestCase):
    def setUp(self):
        logic = InitializeTaxOffice().do()

    def test(self):
        instance = TaxOffice.objects.get(uname="구미세무서")

        assert instance.code == 513
        assert instance.account_number == 905244
        assert TaxOffice.objects.all().count() == 126

        instance2 = TaxOffice.objects.get(uname="서울지방국세청")

        assert instance2.code == 100
        assert instance2.account_number == 11895

        instance3 = TaxOffice.objects.get(uname="강남세무서")

        assert instance3.code == 211
        assert instance3.account_number == 180616
