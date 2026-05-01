
import sys
import unittest
from unittest.mock import MagicMock

# Mock modules before anything else
mock_qsharp = MagicMock()
sys.modules["qsharp"] = mock_qsharp

mock_np = MagicMock()
# Mock basic numpy functions used in the code
mock_np.ndarray = MagicMock
mock_np.array = MagicMock(side_effect=lambda x, **kwargs: x)
mock_np.tanh = MagicMock(side_effect=lambda x: x)
mock_np.arccos = MagicMock(side_effect=lambda x: x)
mock_np.zeros = MagicMock(side_effect=lambda x: [0]*x if isinstance(x, int) else [0])
mock_np.random.random = MagicMock(return_value=0.5)
mock_np.random.randn = MagicMock(return_value=0.1)
mock_np.random.randint = MagicMock(return_value=0)
mock_np.linalg.norm = MagicMock(return_value=1.0)

sys.modules["numpy"] = mock_np

# Mock other potential missing dependencies
sys.modules["gymnasium"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["tqdm"] = MagicMock()

# Now add our project to the path
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "python"))
sys.path.insert(0, project_root)

class TestQuantumAgentSmoke(unittest.TestCase):
    def test_agent_instantiation(self):
        from core.agent_host import QuantumAgentHost, AgentConfig

        config = AgentConfig(num_perception_qubits=8)
        agent = QuantumAgentHost(config)

        self.assertIsNotNone(agent)
        print("Agent instantiated successfully.")

    def test_initialize_agent(self):
        from core.agent_host import QuantumAgentHost
        agent = QuantumAgentHost()
        result = agent.initialize_agent()
        self.assertEqual(result["status"], "success")
        print("Agent initialized successfully.")

    def test_perceive(self):
        from core.agent_host import QuantumAgentHost
        agent = QuantumAgentHost()
        # With our mock, np.array just returns what we pass
        state = [0.5, -0.5, 0.1]
        encoded = agent.perceive(state)
        self.assertIsNotNone(encoded)
        print("Perception successful.")

if __name__ == "__main__":
    unittest.main()
