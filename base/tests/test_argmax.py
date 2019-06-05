import random
from base.tests import BaseTestCase
from base.utils import argmax


class ArgMaxTest(BaseTestCase):
    def test(self):
        arr = [x for x in range(100)]
        random.shuffle(arr)
        assert arr.index(99) == argmax(arr)
