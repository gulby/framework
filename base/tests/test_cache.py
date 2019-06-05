from base.tests import BaseTestCase
from base.utils import cache_get, cache_set
from base.transaction import KeyGenerator


class CacheTest(BaseTestCase):
    def test(self):
        key = KeyGenerator()()
        assert cache_get(key) is None
        cache_set(key, 1)
        assert cache_get(key) == 1
        cache_set(key, "1")
        assert cache_get(key) == "1"
