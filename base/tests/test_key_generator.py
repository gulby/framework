from base.tests import BaseTestCase
from base.transaction import KeyGenerator


class KeyGeneratorTest(BaseTestCase):
    def test_one_generator(self):
        gen = KeyGenerator()
        key1 = gen()
        timestamp1 = gen.timestamp

        key2 = gen()
        timestamp2 = gen.timestamp
        assert timestamp2 == timestamp1
        assert key2 > key1

        gen2 = KeyGenerator()
        key3 = gen2()
        timestamp3 = gen2.timestamp
        assert timestamp3 > timestamp2
        assert key3 > key2

    def test_two_generator(self):
        key_gen1 = KeyGenerator()
        key_gen2 = KeyGenerator()

        key1 = key_gen1()
        key2 = key_gen2()
        assert key1
        assert key2
        assert key2 > key1
