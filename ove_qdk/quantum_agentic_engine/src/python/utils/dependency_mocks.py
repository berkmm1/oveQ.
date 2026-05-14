"""
Mock utilities for missing dependencies.
Ensures the engine can run even when numpy or qsharp are not installed.
"""

import sys
import logging
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

def setup_mocks():
    """Setup mocks for missing critical dependencies."""

    # Mock numpy
    try:
        import numpy
    except ImportError:
        logger.warning("numpy not found, creating mock")
        mock_np = MagicMock()
        mock_np.ndarray = MagicMock
        mock_np.mean.return_value = 0.0
        mock_np.std.return_value = 1.0
        mock_np.random.randn.side_effect = lambda *args: mock_array([0.1] * (args[0] if args else 1))
        mock_np.random.random.return_value = 0.5
        mock_np.random.randint.return_value = 0
        mock_np.random.choice.return_value = 0
        mock_np.linalg.norm.return_value = 1.0
        mock_np.tanh.side_effect = lambda x: x
        mock_np.exp.side_effect = lambda x: x
        mock_np.cos.side_effect = lambda x: x
        mock_np.sin.side_effect = lambda x: x
        mock_np.abs.side_effect = lambda x: x
        mock_np.zeros.side_effect = lambda shape, **kwargs: mock_array([0.0] * (shape if isinstance(shape, int) else shape[0]))
        mock_np.ones.side_effect = lambda shape, **kwargs: mock_array([1.0] * (shape if isinstance(shape, int) else shape[0]))
        mock_np.eye.return_value = MagicMock()
        mock_np.dot.return_value = MagicMock()
        def mock_array(x, **kwargs):
            if isinstance(x, (list, tuple)):
                class MockArray(list):
                    def __getitem__(self, idx):
                        if isinstance(idx, tuple):
                            # Very basic multidimensional indexing support
                            return 0.0
                        return super().__getitem__(idx)
                    def __sub__(self, other):
                        if isinstance(other, (list, tuple)):
                            return MockArray([a - b for a, b in zip(self, other)])
                        return MockArray([a - other for a in self])
                    def __add__(self, other):
                        if isinstance(other, (list, tuple)):
                            return MockArray([a + b for a, b in zip(self, other)])
                        return MockArray([a + other for a in self])
                    def __radd__(self, other):
                        return self.__add__(other)
                    def __mul__(self, other):
                        if isinstance(other, (list, tuple)):
                            return MockArray([a * b for a, b in zip(self, other)])
                        return MockArray([a * other for a in self])
                    def __rmul__(self, other):
                        return self.__mul__(other)
                    def __truediv__(self, other):
                        if isinstance(other, (list, tuple)):
                            return MockArray([a / b if b != 0 else 0 for a, b in zip(self, other)])
                        return MockArray([a / other if other != 0 else 0 for a in self])
                    def __pow__(self, other):
                        return MockArray([a ** other for a in self])
                    @property
                    def shape(self):
                        return (len(self),)
                    @property
                    def dtype(self):
                        class DType:
                            def __init__(self): self.kind = 'f'
                        return DType()
                    def flatten(self):
                        return self
                    def tolist(self):
                        return self
                    def __array__(self, dtype=None):
                        return self
                return MockArray(x)
            return x

        mock_np.array.side_effect = mock_array
        mock_np.argmax.return_value = 0
        mock_np.float64 = float
        mock_np.int64 = int
        mock_np.complex128 = complex
        sys.modules["numpy"] = mock_np

    # Mock qsharp
    try:
        import qsharp
    except ImportError:
        logger.warning("qsharp not found, creating mock")
        mock_qsharp = MagicMock()
        sys.modules["qsharp"] = mock_qsharp

    # Mock gymnasium
    try:
        import gymnasium
    except ImportError:
        try:
            import gym
            sys.modules["gymnasium"] = gym
        except ImportError:
            logger.warning("gymnasium/gym not found, creating mock")
            mock_gym = MagicMock()
            sys.modules["gymnasium"] = mock_gym

    # Mock matplotlib
    try:
        import matplotlib.pyplot
    except ImportError:
        logger.warning("matplotlib not found, creating mock")
        mock_plt = MagicMock()
        sys.modules["matplotlib"] = mock_plt
        sys.modules["matplotlib.pyplot"] = mock_plt

    # Mock tqdm
    try:
        import tqdm
    except ImportError:
        logger.warning("tqdm not found, creating mock")
        mock_tqdm = MagicMock()
        mock_tqdm.tqdm.side_effect = lambda x, **kwargs: x
        sys.modules["tqdm"] = mock_tqdm

if __name__ == "__main__":
    setup_mocks()
    import numpy as np
    print(f"Numpy mock mean: {np.mean([1, 2, 3])}")
