from base.agents import DummyAgent, Agent
from base.tests import BaseTestCase


class AgentModelTest(BaseTestCase):
    def test(self):
        dummy_agent = DummyAgent()

        assert dummy_agent == DummyAgent()

        agent = Agent()

        with self.assertRaises(NotImplementedError):
            agent.get_master("None")
