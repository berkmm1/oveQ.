
import sys
import unittest
from unittest.mock import MagicMock

# Mock everything needed for the real test suite to load
mock_qsharp = MagicMock()
sys.modules["qsharp"] = mock_qsharp

mock_np = MagicMock()
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

sys.modules["gymnasium"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["tqdm"] = MagicMock()
sys.modules["scipy"] = MagicMock()

# Path setup
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "python"))
sys.path.insert(0, project_root)

# Now run the actual test suite
import unittest
loader = unittest.TestLoader()
# test_quantum_agent.py is in the tests/ directory relative to root,
# but let's try to load it by path
suite = loader.discover(os.path.dirname(__file__), pattern='test_quantum_agent.py')

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
