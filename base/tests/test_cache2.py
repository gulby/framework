from base.tests import BaseTestCase
from base.utils import cache_get, cache_set, cache_delete


class CacheTest2(BaseTestCase):
    def test(self):
        key1 = "test_key"
        value = "test_value"
        cache_set(key1, value)
        cache_value = cache_get(key1)

        assert cache_value == value

        cache_delete(key1)

        assert cache_get(key1) is None
