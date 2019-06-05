from base.tests import BaseTestCase
from base.models import Dummy
from base.utils import snoop


# 장고단에서 order_by() 에서도 None 이 무한소로 취급됨 : django 단이라기 보다는 postgres 단
# None 에 대해 다른 해석이 필요한 경우 application logic 단에서 별도 처리 필요
class OrderingTest(BaseTestCase):
    def setUp(self):
        self.instance3 = Dummy.objects.create(name="3", temp=0)
        self.instance2 = Dummy.objects.create(name="2", temp=-1)
        self.instance1 = Dummy.objects.create(name="1")
        assert self.instance1.temp is None
        self.instance4 = Dummy.objects.create(name="4", temp=1000000000)

    def test_django_asc(self):
        qs = Dummy.objects.order_by("data__temp")

        assert qs[0] == self.instance1
        assert qs[1] == self.instance2
        assert qs[2] == self.instance3
        assert qs[3] == self.instance4

        assert Dummy.objects.order_by("data__temp").first() == self.instance1

    def test_django_desc(self):
        qs = Dummy.objects.order_by("-data__temp")

        assert qs[0] == self.instance4
        assert qs[1] == self.instance3
        assert qs[2] == self.instance2
        assert qs[3] == self.instance1

        assert Dummy.objects.order_by("-data__temp").first() == self.instance4

    def test_subfield_asc(self):
        qs = Dummy.objects.order_by("temp")

        assert qs[0] == self.instance1
        assert qs[1] == self.instance2
        assert qs[2] == self.instance3
        assert qs[3] == self.instance4

        assert Dummy.objects.order_by("temp").first() == self.instance1

    def test_subfield_desc(self):
        qs = Dummy.objects.order_by("-temp")

        assert qs[0] == self.instance4
        assert qs[1] == self.instance3
        assert qs[2] == self.instance2
        assert qs[3] == self.instance1

        assert Dummy.objects.order_by("-temp").first() == self.instance4


class ComplexOrderingTest(BaseTestCase):
    def setUp(self):
        self.instance3 = Dummy.objects.create(name="3", result_labels={"STA_y": "긍정", "STA_prob": 0.0})
        self.instance2 = Dummy.objects.create(name="2", result_labels={"STA_y": "긍정", "STA_prob": -0.99})
        self.instance1 = Dummy.objects.create(name="1")
        assert self.instance1.result_labels["STA_prob"] is None
        self.instance4 = Dummy.objects.create(name="4", result_labels={"STA_y": "긍정", "STA_prob": 0.99})

    # 장고단에서는 dict 안의 dict 에 대해서는 order_by 를 지원하지 않으나
    # deephigh framework 에서는 웹서버 메모리 단에서 소팅하기 때문에 문제 없음
    def test_django_asc(self):
        qs = Dummy.objects.order_by("data__result_labels__STA_prob")

        assert qs[0] == self.instance1
        assert qs[1] == self.instance2
        assert qs[2] == self.instance3
        assert qs[3] == self.instance4

        assert Dummy.objects.order_by("data__result_labels__STA_prob").first() == self.instance1

    def test_django_desc(self):
        qs = Dummy.objects.order_by("-data__result_labels__STA_prob")

        assert qs[0] == self.instance4
        assert qs[1] == self.instance3
        assert qs[2] == self.instance2
        assert qs[3] == self.instance1

        assert Dummy.objects.order_by("-data__result_labels__STA_prob").first() == self.instance4

    def test_subfield_asc(self):
        qs = Dummy.objects.order_by("result_labels__STA_prob")

        assert qs[0] == self.instance1
        assert qs[1] == self.instance2
        assert qs[2] == self.instance3
        assert qs[3] == self.instance4

        assert Dummy.objects.order_by("result_labels__STA_prob").first() == self.instance1

    @snoop()
    def test_subfield_desc(self):
        qs = Dummy.objects.order_by("-result_labels__STA_prob")

        assert qs[0] == self.instance4
        assert qs[1] == self.instance3
        assert qs[2] == self.instance2
        assert qs[3] == self.instance1

        assert Dummy.objects.order_by("-result_labels__STA_prob").first() == self.instance4
