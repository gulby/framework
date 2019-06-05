from base.tests import BaseTestCase
from base.models import Dummy


class ForProfileTest(BaseTestCase):
    def test(self):
        Dummy.objects.create()
