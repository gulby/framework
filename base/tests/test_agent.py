from base.models.samples import Dummy
from base.agents import DummyAgent
from base.tests import BaseTestCase


class AgentModelTest(BaseTestCase):
    def test(self):
        dummy1 = Dummy.objects.create()
        dummy2 = Dummy.objects.create()
        dummy3 = Dummy.objects.create()
        agent = DummyAgent()
        assert agent.get_master(dummy1) == dummy1
        assert agent.get_master(dummy2) == dummy2
        assert agent.get_master(dummy3) == dummy3
        dummy1.group = agent
        dummy1.save()
        assert Dummy.objects.get(group=dummy1) == dummy1
        dummy2.group = agent
        dummy2.save()
        assert Dummy.objects.get(group=dummy2) == dummy2
