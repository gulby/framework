from datetime import timedelta

from base.tests import BaseTestCase
from base.transaction import KeyGenerator, get_datetime_from_key
from base.utils import now


class KeyGeneratorTest(BaseTestCase):
    def test(self):
        keygen = KeyGenerator()
        id1 = keygen()
        self.assertAlmostEqual(get_datetime_from_key(id1), now(), delta=timedelta(10))
