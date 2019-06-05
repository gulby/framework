from base.tests import BaseTestCase
from common.models import Address


class GetRoadNameTest(BaseTestCase):
    def test(self):
        addr1 = "운서"
        address1 = Address()
        address1.address = addr1
        road_name = address1.road_name
        assert road_name is None

        address2 = Address(address="인천광역시 중구 운서동 2886-13 노벨빌라돔")
        assert address2.road_name == "운서2로"

        address3 = Address(address="인천광역시 중구 운서2로 31")
        assert address3.road_name == "운서2로"

        address4 = Address(address="인천광역시 중구 운서동 2886-13")
        assert address4.road_name == "운서2로"

        address5 = Address(address="경기도 부천시 원미구 원미1동 두산아파트 101동 1205호")
        assert address5.road_name == "원미로144번길"

        address6 = Address(address="경기도 화성시 영통로50번길 27, 106동 103호")
        assert address6.road_name == "영통로50번길"
