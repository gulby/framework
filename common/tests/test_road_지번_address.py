from base.tests import BaseTestCase
from common.models import Address


class RoadAddressTest(BaseTestCase):
    def test(self):
        address = Address.objects.create(address="서울특별시 서초구 서초동 삼덕빌딩")
        assert address.road_address == "서울특별시 서초구 반포대로22길 100 (서초동)"

        address2 = Address.objects.create(address="서울특별시 서초구 반포대로22길 100 (서초동)")
        assert address2.road_address == "서울특별시 서초구 반포대로22길 100 (서초동)"

        address3 = Address.objects.create(address="서울특별시 서초구 서초동 1576-1 삼덕빌딩")
        assert address3.road_address == "서울특별시 서초구 반포대로22길 100 (서초동)"


class 지번AddressTest(BaseTestCase):
    def test(self):
        address = Address.objects.create(address="서울특별시 서초구 서초동 삼덕빌딩")
        assert address.지번_address == "서울특별시 서초구 서초동 1576-1 삼덕빌딩"

        address2 = Address.objects.create(address="서울특별시 서초구 서초동 1576-1 삼덕빌딩")
        assert address2.지번_address == "서울특별시 서초구 서초동 1576-1 삼덕빌딩"

        address3 = Address.objects.create(address="서울특별시 서초구 반포대로22길 100 (서초동)")
        assert address3.지번_address == "서울특별시 서초구 서초동 1576-1 삼덕빌딩"


class NoneTest(BaseTestCase):
    def test(self):
        address = Address.objects.create(address="서울특별시 서초구 서초동")
        assert address.지번_address == "서울특별시 서초구 서초동 산141-4 대성사"
        assert address.road_address == "서울특별시 서초구 남부순환로328길 49 (서초동)"


class JusoResJsonTest(BaseTestCase):
    def test(self):
        address = Address.objects.create(address="서울특별시 서초구 서초동 1576-1 삼덕빌딩 6층 지해솔루션")
        assert address.road_address == "서울특별시 서초구 반포대로22길 100 (서초동)"
        assert address.지번_address == "서울특별시 서초구 서초동 1576-1 삼덕빌딩"

        address2 = Address.objects.create(address="서울특별시")
        assert address2.road_address == "서울특별시"
        assert address2.지번_address == "서울특별시"

        address3 = Address.objects.create(address="서울특별시 강남구")
        assert address3.road_address == "서울특별시 강남구"
        assert address3.지번_address == "서울특별시 강남구"

        address5 = Address.objects.create(address="서울특별시 강남구 역삼동 813-10")
        assert address5.road_address == "서울특별시 강남구 봉은사로4길 36 (역삼동)"
        assert address5.지번_address == "서울특별시 강남구 역삼동 813-10 운현빌딩"

        address6 = Address.objects.create(address="서울특별시 강남구 역삼동 813-10 운현빌딩")
        assert address6.road_address == "서울특별시 강남구 봉은사로4길 36 (역삼동)"
        assert address6.지번_address == "서울특별시 강남구 역삼동 813-10 운현빌딩"

        address7 = Address.objects.create(address="서울특별시 서초구 반포대로22길 100")
        assert address7.road_address == "서울특별시 서초구 반포대로22길 100 (서초동)"
        assert address7.지번_address == "서울특별시 서초구 서초동 1576-1 삼덕빌딩"

        address8 = Address.objects.create(address="서울특별시 서초구 반포대로22길")
        assert address8.road_address == "서울특별시 서초구 반포대로22길"
        assert address8.지번_address == "서울특별시 서초구 반포대로22길"

        address9 = Address.objects.create(address="서울특별시 종로구 청와대로 1")
        assert address9.road_address == "서울특별시 종로구 청와대로 1 (세종로)"
        assert address9.지번_address == "서울특별시 종로구 세종로 1"


class ThreeWordsAddressTest(BaseTestCase):
    def test(self):
        address1 = Address.objects.create(address="서울특별시 강남구 역삼동")
        assert address1.road_address == "서울특별시 강남구 봉은사로 108 (역삼동)"
        assert address1.지번_address == "서울특별시 강남구 역삼동 601"

        address2 = Address.objects.create(address="경기도 부천시 오정구")
        assert address2.road_address == "경기도 부천시 오정구"
        assert address2.지번_address == "경기도 부천시 오정구"

        address3 = Address.objects.create(address="인천광역시 백령면 북포리")
        assert address3.road_address == "인천광역시 백령면 북포리"
        assert address3.지번_address == "인천광역시 백령면 북포리"
