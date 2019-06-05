from base.tests import BaseTestCase
from docker_init import init_db


class DockerInitTest(BaseTestCase):
    def test(self):
        assert init_db()
