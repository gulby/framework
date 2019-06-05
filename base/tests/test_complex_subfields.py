from django.db.models import Q

from base.tests import BaseTestCase, todo_test
from base.models.samples import Dummy
from base.fields import SQ


class DictSubfieldTest(BaseTestCase):
    def test_filter(self):
        instance1 = Dummy.objects.create(result_labels={"STA_y": "긍정", "STA_prob": 0.99})
        assert instance1.result_labels == {
            "STA_y": "긍정",
            "STA_prob": 0.99,
            "STA2_y": None,
            "STA2_prob": None,
            "TTS_y": None,
            "TTS_prob": None,
        }

        instance2 = Dummy.objects.create()
        assert instance2.result_labels.STA_prob is None
        assert Dummy.objects.count() == 2

        # 장고단 에서는 filter() 에서도 None 을 무한소 취급함 : django 단이라기 보다는 postgres 단
        assert Dummy.objects.filter(data__result_labels__STA_prob__gt=-1000000).count() == 1
        assert Dummy.objects.filter(data__result_labels__STA_prob__lt=-1000000).count() == 1

        # subfield 를 써서 deephigh framework 단 filter() 에서는 None 을 제거함
        # 당연히 이게 맞음. None >= 0 is False and None <= 0 is False 이기 때문 (파이썬에선 에러, DB 에선 False)
        # gt, gte 에서는 원래 제거되고, lt, lte 에서는 별도 처리를 하여 framework 단에서 제거
        assert Dummy.objects.filter(result_labels__STA_prob__gt=-1000000).count() == 1
        assert Dummy.objects.filter(result_labels__STA_prob__lt=-1000000).count() == 0

    @todo_test()
    def test_Q(self):
        instance1 = Dummy.objects.create(result_labels={"STA_y": "긍정", "STA_prob": 0.99})
        assert instance1.result_labels.STA_prob == 0.99
        instance2 = Dummy.objects.create()
        assert instance2.result_labels.STA_prob is None
        instance3 = Dummy.objects.create(result_labels={"STA_y": "긍정", "STA_prob": 0.01})
        assert instance3.result_labels.STA_prob == 0.01

        qs = Dummy.objects.filter(Q(data__result_labels__STA_prob=None))
        assert len(qs) == 1 and qs[0] == instance2
        qs = Dummy.objects.filter(Q(data__result_labels__STA_prob__gt=0.5))
        assert len(qs) == 1 and qs[0] == instance1
        qs = Dummy.objects.filter(Q(data__result_labels__STA_prob=None) | Q(data__result_labels__STA_prob__gt=0.5))
        assert len(qs) == 2
        qs = Dummy.objects.filter(
            Q(data__result_labels__STA_prob=None)
            | (Q(data__result_labels__STA_prob__gt=0.5) & Q(data__result_labels__STA_y="부정"))
        )
        assert len(qs) == 1

        qs = Dummy.objects.filter(SQ(result_labels__STA_prob=None))
        assert len(qs) == 1 and qs[0] == instance2
        qs = Dummy.objects.filter(SQ(result_labels__STA_prob__gt=0.5))
        assert len(qs) == 1 and qs[0] == instance1
        qs = Dummy.objects.filter(SQ(result_labels__STA_prob=None) | SQ(result_labels__STA_prob__gt=0.5))
        assert len(qs) == 2
        qs = Dummy.objects.filter(
            SQ(result_labels__STA_prob=None) | (SQ(result_labels__STA_prob__gt=0.5) & SQ(result_labels__STA_y="부정"))
        )
        assert len(qs) == 1
