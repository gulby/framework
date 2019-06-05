from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.functional import cached_property

from base.json import json_loads
from base.requests import requests_get
from base.models import Model, Actor
from base.descriptors import (
    ValueSubfield,
    SubfieldWrapper,
    UnameSubfield,
    ForeignKeySubfield,
    ReverseForeignKeySubfield,
)
from base.types import Type
from base.utils import file_log

from common.utils import normalize_address


class TaxOffice(Actor):
    class Meta:
        proxy = True

    # data subfields
    tax_office_name = SubfieldWrapper("uname")
    code = ValueSubfield("data", int)
    account_number = ValueSubfield("data", int)


class LocalTaxGovernment(Actor):
    class Meta:
        proxy = True

    local_tax_government_name = SubfieldWrapper("uname")
    office_address = ValueSubfield("data", str)
    addresses = ReverseForeignKeySubfield("computed", Type.Address, "local_tax_government")

    @property
    def headquarter_position_name(self):
        local_tax_government_name = self.local_tax_government_name
        if local_tax_government_name.endswith("시청"):
            return "{}".format(local_tax_government_name.replace("시청", "시장"))
        elif local_tax_government_name.endswith("군청"):
            return "{}".format(local_tax_government_name.replace("군청", "군수"))
        elif local_tax_government_name.endswith("구청"):
            return "{}".format(local_tax_government_name.replace("구청", "구청장"))
        elif local_tax_government_name.endswith("도청"):
            return "{}".format(local_tax_government_name.replace("도청", "도지사"))
        else:
            raise NotImplementedError(
                "headquarter_position_name() 이 구현되지 않은 지방세관할청 타입입니다. : {}".format(self.local_tax_government_name)
            )

    @classmethod
    def get_by_human_address(cls, human_address):
        splited_human_address = human_address.split()
        for token_count in range(4, 0, -1):
            address = Address.objects.filter(address=cls.join_address(splited_human_address, token_count)).first("-id")
            if address:
                return address.local_tax_government
        return None

    @classmethod
    def join_address(cls, splited_address, count):
        return " ".join(splited_address[:count])


class Address(Model):
    class Meta:
        proxy = True

    # data subfields
    uname = UnameSubfield(normalize=normalize_address, alias="address")
    tax_office_name = ValueSubfield("data", str, default=lambda self: self.get_tax_office_name())
    road_address = ValueSubfield("data", str, default=lambda self: self.get_road_address())
    지번_address = ValueSubfield("data", str, default=lambda self: self.get_지번_address())
    road_name = ValueSubfield("data", str, default=lambda self: self.get_road_name())
    # TODO: expire, onchange 기능확장 후 수정
    zip_code = ValueSubfield("data", str, default=lambda self: self.get_zip_code())

    local_tax_government = ForeignKeySubfield("data", Type.LocalTaxGovernment)

    @property
    def tax_office(self):
        tax_office, _ = TaxOffice.objects.get_or_create(uname=self.tax_office_name)
        return tax_office

    @cached_property
    def _juso_res_json(self):
        # TODO: api 콜은 여기가 아니라 따로 caller 로 빼기
        url = "http://www.juso.go.kr/addrlink/addrLinkApi.do?"
        splited_address = self.address.split()
        # 미리 세팅한 이유는 4개 미만인경우 dict 를 만들어서 넘겨줘야 하기때문
        # 도로명주소, 지번주소, 우편번호, 도로명(도로이름)
        result = {
            "results": {"juso": [{"roadAddr": self.address, "jibunAddr": self.address, "zipNo": None, "rn": None}]}
        }
        params = {"resultType": "json", "confmKey": settings.ADDERSS_SEARCH_API_KEY}
        if len(splited_address) < 4:
            if (not splited_address[-1].endswith("동")) or (1 <= len(splited_address) < 3):
                return result
            # TODO: 리팩토링
            params["keyword"] = self.address
            res = requests_get(url, params=params)
            result = json_loads(res.text)
        else:
            for token_count in range(4, len(splited_address) + 1):
                # TODO: 리팩토링
                params["keyword"] = " ".join(splited_address[:token_count])
                res = requests_get(url, params=params)
                json_res = json_loads(res.text)
                if json_res["results"]["juso"]:
                    result = json_res
                else:
                    break
        # TODO: 3어절로 검색하면 주렁주렁 붙는데 이에대한처리 추가
        return result

    # 도로이름
    # TODO: 리팩토링 -> get_road_name 이랑 구현이 완전 동일, 단지 zipNo 인지 rn 인지의 차이뿐
    def get_road_name(self):
        juso_res_json = self._juso_res_json
        rn_list = [data["rn"] for data in juso_res_json["results"]["juso"]]
        if len(set(rn_list)) > 1:
            file_log("2개 이상의 도로가 검색되었습니다. 검색 결과 중 첫번째 도로가 임의로 선택되었습니다. : {}".format(self.address))
        return juso_res_json["results"]["juso"][0]["rn"]

    def select_one_tax_office_name(self, soup):
        # TODO: 제대로 구현 -> 검색결과가 여러개인경우 normalize_address 의 값이랑 매칭해서 1개의 값을 리턴
        # 여러개의 결과 중 하나 선택 : 운서로 라고 검색했는데 인천에 운서로와 대구에 운서로 이렇게 2개의 결과가 존재하여 이중에 하나를 선택하는 함수
        return soup.select_one("body > div:nth-of-type(2) > table > tr:nth-of-type(1) > td:nth-of-type(2) > a").text

    # 세무서 (국세)
    def get_tax_office_name(self):
        road_name = self.road_name
        url = "https://www.nts.go.kr/wtsuser/about_semuFind.asp"
        params = {"search_type": "R", "keyword": road_name.encode("euc-kr"), "target": "search_semu"}
        res = requests_get(url, params=params)
        soup = BeautifulSoup(res.content.decode("euc-kr"), features="lxml")
        tax_office_name = self.select_one_tax_office_name(soup)
        return tax_office_name

    # 우편번호
    # TODO: 리팩토링 -> get_road_name 이랑 구현이 완전 동일, 단지 zipNo 인지 rn 인지의 차이뿐
    # TODO: 우편번호 조회방식 개선
    def get_zip_code(self):
        juso_res_json = self._juso_res_json
        rn_list = [data["rn"] for data in juso_res_json["results"]["juso"]]
        if len(set(rn_list)) == 1:
            return juso_res_json["results"]["juso"][0]["zipNo"]
        elif len(set(rn_list)) == 0:
            return "검색실패"
        elif len(set(rn_list)) >= 2:
            return "2개이상"
        else:
            assert AssertionError

    def get_road_address(self):
        juso_res_json = self._juso_res_json
        if len(juso_res_json["results"]["juso"]) > 1:
            file_log("2개 이상의 도로명 주소가 검색되었습니다. 검색 결과 중 첫번째 도로명 주소가 임의로 선택되었습니다. : {}".format(self.address))
        return juso_res_json["results"]["juso"][0]["roadAddr"]

    def get_지번_address(self):
        juso_res_json = self._juso_res_json
        if len(juso_res_json["results"]["juso"]) > 1:
            file_log("2개 이상의 지번 주소가 검색되었습니다. 검색 결과 중 첫번째 지번 주소가 임의로 선택되었습니다. : {}".format(self.address))
        return juso_res_json["results"]["juso"][0]["jibunAddr"]


class Board(Model):
    class Meta:
        proxy = True

    title = SubfieldWrapper("uname")
    posts = ReverseForeignKeySubfield("computed", Type.Post, "board")


class Post(Model):
    class Meta:
        proxy = True

    author = SubfieldWrapper("owner")
    title = ValueSubfield("data", str)
    content = ValueSubfield("data", str)

    container = ForeignKeySubfield("data", Type.Board, null=False, create_only=True, alias="board")

    @property
    def published_date(self):
        return self.created_date
