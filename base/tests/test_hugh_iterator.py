from base.tests import BaseTestCase
from base.models import Dummy


class IteratorTest(BaseTestCase):
    def test(self):
        Dummy.objects.create(temp=1)
        Dummy.objects.create(temp=2)
        Dummy.objects.create(temp=3)
        sum_temp = 0
        for dummy in Dummy.objects.hugh_iterator():
            sum_temp += dummy.temp
        assert sum_temp == 6
        sum_temp = 0
        for dummy in Dummy.objects.hugh_iterator(chunk_size=1):
            sum_temp += dummy.temp
        assert sum_temp == 6
        sum_temp = 0
        for dummy in Dummy.objects.hugh_iterator(chunk_size=2):
            sum_temp += dummy.temp
        assert sum_temp == 6
        sum_temp = 0
        for dummy in Dummy.objects.hugh_iterator(chunk_size=3):
            sum_temp += dummy.temp
        assert sum_temp == 6
        sum_temp = 0
        for dummy in Dummy.objects.hugh_iterator(chunk_size=4):
            sum_temp += dummy.temp
        assert sum_temp == 6
