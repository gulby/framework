import pandas as pd

from base.logics import Logic
from common.models import TaxOffice, Address, LocalTaxGovernment


# TODO: 프로포티로 까서 보여줄때만 서울지방 국세청으로
TAX_OFFICE_NAME_MAPPING = {
    "서울청": "서울지방국세청",
    "중부청": "중부지방국세청",
    "대전청": "대전지방국세청",
    "광주청": "광주지방국세청",
    "대구청": "대구지방국세청",
    "부산청": "부산지방국세청",
}


class InitializeTaxOffice(Logic):
    def __init__(self, path="common/data/tax_office_data.csv"):
        self.path = path

    def _do(self):
        table_frame = pd.read_csv(self.path, sep="\t")
        # TODO: 데이터에 세무서명에 강남, 강동 으로 만 되어있어서 뒤에 세무서를 붙이는 코드인데 프로포티로 까서 보여줄때만 ~ 세무서로 보이게끔 수정
        table_frame["세무서명"] = table_frame["세무서명"].apply(
            lambda x: TAX_OFFICE_NAME_MAPPING[x] if x in TAX_OFFICE_NAME_MAPPING.keys() else "{}세무서".format(x)
        )
        table_json = table_frame.to_dict(orient="record")
        for stat in table_json:
            instance = TaxOffice.objects.create(uname=stat["세무서명"], code=stat["세무서코드"], account_number=stat["세무서계좌번호"])


class InitializeLocalTaxGovernmentAndAddress(Logic):
    # TODO: 현재 파일은 임시로 만든 파일
    def __init__(self, path="common/tests/data/local_tax_government.csv"):
        self.path = path

    def _do(self):
        table_frame = pd.read_csv(self.path, sep="\t")
        stats = table_frame.to_dict(orient="record")
        for stat in stats:
            address = Address.objects.create(address=stat["주소"])
            local_tax_government, _ = LocalTaxGovernment.objects.get_or_create(uname=stat["관할청"])
            address.local_tax_government = local_tax_government
            address.save()
