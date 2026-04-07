#!/usr/bin/env python3
"""
Unit Tests for Quantum Agentic Engine
Comprehensive test suite for all components
"""

import unittest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "python"))

from core.agent_host import AgentConfig, QuantumAgentHost, ReplayBuffer, Experience
from core.environment_interface import (
    GridWorldEnvironment,
    ContinuousControlEnvironment,
    MultiAgentEnvironment,
    EnvironmentConfig
)
from utils.quantum_utils import (
    QuantumStateEncoder,
    QuantumCircuitBuilder,
    QuantumNoiseSimulator,
    QuantumGradientEstimator,
    QuantumOptimizer,
    QuantumMetrics
)


class TestAgentConfig(unittest.TestCase):
    """Test AgentConfig dataclass"""

    def test_default_config(self):
        config = AgentConfig()
        self.assertEqual(config.num_perception_qubits, 16)
        self.assertEqual(config.num_decision_qubits, 8)
        self.assertEqual(config.learning_rate, 0.01)

    def test_custom_config(self):
        config = AgentConfig(
            num_perception_qubits=32,
            learning_rate=0.001
        )
        self.assertEqual(config.num_perception_qubits, 32)
        self.assertEqual(config.learning_rate, 0.001)

    def test_to_dict(self):
        config = AgentConfig()
        config_dict = config.to_dict()
        self.assertIn("NumPerceptionQubits", config_dict)
        self.assertIn("LearningRate", config_dict)


class TestReplayBuffer(unittest.TestCase):
    """Test ReplayBuffer functionality"""

    def setUp(self):
        self.buffer = ReplayBuffer(capacity=100)

    def test_add_experience(self):
        exp = Experience(
            state=np.array([1.0, 2.0]),
            action=0,
            reward=1.0,
            next_state=np.array([2.0, 3.0]),
            done=False
        )
        self.buffer.add(exp)
        self.assertEqual(len(self.buffer), 1)

    def test_capacity_limit(self):
        # Fill beyond capacity
        for i in range(150):
            exp = Experience(
                state=np.array([float(i)]),
                action=0,
                reward=float(i),
                next_state=np.array([float(i + 1)]),
                done=False
            )
            self.buffer.add(exp)

        self.assertEqual(len(self.buffer), 100)

    def test_sample(self):
        # Add experiences
        for i in range(50):
            exp = Experience(
                state=np.random.randn(4),
                action=i % 4,
                reward=float(i),
                next_state=np.random.randn(4),
                done=False
            )
            self.buffer.add(exp)

        # Sample
        batch, indices, weights = self.buffer.sample(10)
        self.assertEqual(len(batch), 10)
        self.assertEqual(len(indices), 10)
        self.assertEqual(len(weights), 10)

    def test_priorities_update(self):
        # Add experiences
        for i in range(20):
            exp = Experience(
                state=np.random.randn(4),
                action=0,
                reward=float(i),
                next_state=np.random.randn(4),
                done=False
            )
            self.buffer.add(exp)

        # Sample and update
        batch, indices, weights = self.buffer.sample(5)
        new_priorities = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        self.buffer.update_priorities(indices, new_priorities)

        # Verify update
        self.assertTrue(True)  # If no exception, test passes


class TestQuantumAgentHost(unittest.TestCase):
    """Test QuantumAgentHost"""

    def setUp(self):
        config = AgentConfig(
            num_perception_qubits=8,
            num_decision_qubits=4,
            num_action_qubits=4
        )
        self.agent = QuantumAgentHost(config)

    def test_initialization(self):
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.config.num_perception_qubits, 8)

    def test_perceive(self):
        state = np.random.randn(8)
        encoded = self.agent.perceive(state)
        self.assertEqual(encoded.shape, state.shape)

    def test_process(self):
        state = np.random.randn(8)
        processed = self.agent.process(state)
        self.assertIsNotNone(processed)

    def test_decide(self):
        state = np.random.randn(8)
        action, q_values = self.agent.decide(state)
        self.assertIsInstance(action, int)
        self.assertEqual(len(q_values), 4)

    def test_act(self):
        result = self.agent.act(0)
        self.assertIn("action", result)
        self.assertIn("status", result)

    def tearDown(self):
        self.agent.close()


class TestGridWorldEnvironment(unittest.TestCase):
    """Test GridWorldEnvironment"""

    def setUp(self):
        self.env = GridWorldEnvironment(size=5)

    def test_reset(self):
        state = self.env.reset()
        self.assertEqual(len(state), 25)  # 5x5 grid

    def test_step(self):
        self.env.reset()
        state, reward, done, info = self.env.step(0)
        self.assertIsNotNone(state)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)

    def test_dimensions(self):
        self.assertEqual(self.env.get_state_dim(), 25)
        self.assertEqual(self.env.get_action_dim(), 4)

    def test_episode_completion(self):
        state = self.env.reset()
        done = False
        steps = 0

        while not done and steps < 1000:
            action = np.random.randint(0, 4)
            state, reward, done, info = self.env.step(action)
            steps += 1

        self.assertTrue(done or steps >= 1000)


class TestContinuousControlEnvironment(unittest.TestCase):
    """Test ContinuousControlEnvironment"""

    def setUp(self):
        self.env = ContinuousControlEnvironment(
            state_dim=12,
            action_dim=4
        )

    def test_reset(self):
        state = self.env.reset()
        self.assertEqual(len(state), 24)  # state + target

    def test_step(self):
        self.env.reset()
        state, reward, done, info = self.env.step(0)
        self.assertIsNotNone(state)
        self.assertLessEqual(reward, 0)  # Negative reward (distance)


class TestMultiAgentEnvironment(unittest.TestCase):
    """Test MultiAgentEnvironment"""

    def setUp(self):
        self.env = MultiAgentEnvironment(
            num_agents=3,
            state_dim_per_agent=4,
            action_dim_per_agent=4
        )

    def test_reset(self):
        state = self.env.reset()
        self.assertEqual(len(state), 14)  # 3*4 + 2 (target)

    def test_step(self):
        self.env.reset()
        state, reward, done, info = self.env.step(0)
        self.assertIsNotNone(state)


class TestQuantumStateEncoder(unittest.TestCase):
    """Test QuantumStateEncoder"""

    def setUp(self):
        self.encoder = QuantumStateEncoder()

    def test_angle_encoding(self):
        data = np.array([0.5, -0.3, 0.8])
        angles = self.encoder.angle_encoding(data)
        self.assertEqual(len(angles), len(data))
        self.assertTrue(np.all(angles >= 0))
        self.assertTrue(np.all(angles <= np.pi))

    def test_amplitude_encoding(self):
        data = np.array([1.0, 2.0, 3.0])
        amplitudes = self.encoder.amplitude_encoding(data)
        norm = np.linalg.norm(amplitudes)
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_basis_encoding(self):
        data = np.array([0.5, -0.3, 0.8])
        binary = self.encoder.basis_encoding(data, n_qubits=8)
        self.assertTrue(np.all(np.isin(binary, [0, 1])))

    def test_dense_angle_encoding(self):
        data = np.array([0.5, -0.3])
        encoded = self.encoder.dense_angle_encoding(data)
        self.assertEqual(len(encoded), len(data) * 2)


class TestQuantumCircuitBuilder(unittest.TestCase):
    """Test QuantumCircuitBuilder"""

    def setUp(self):
        self.builder = QuantumCircuitBuilder(4)

    def test_add_rotation(self):
        self.builder.add_rotation(0, 'x', np.pi / 2)
        self.assertEqual(len(self.builder.gates), 1)

    def test_add_cnot(self):
        self.builder.add_cnot(0, 1)
        self.assertEqual(len(self.builder.gates), 1)

    def test_add_hadamard(self):
        self.builder.add_hadamard(0)
        self.assertEqual(len(self.builder.gates), 1)

    def test_add_entanglement_layer(self):
        self.builder.add_entanglement_layer('linear')
        self.assertEqual(len(self.builder.gates), 3)  # 3 CNOTs for 4 qubits

    def test_build_variational_layer(self):
        params = np.random.randn(12)
        self.builder.build_variational_layer(params)
        self.assertGreater(len(self.builder.gates), 0)

    def test_to_qsharp(self):
        self.builder.add_hadamard(0)
        qsharp_code = self.builder.to_qsharp()
        self.assertIn("operation GeneratedCircuit", qsharp_code)
        self.assertIn("H(qubits[0])", qsharp_code)


class TestQuantumNoiseSimulator(unittest.TestCase):
    """Test QuantumNoiseSimulator"""

    def setUp(self):
        self.simulator = QuantumNoiseSimulator(error_rate=0.1)

    def test_bit_flip(self):
        state = np.array([1.0, -1.0, 1.0, -1.0])
        noisy = self.simulator.apply_bit_flip(state)
        self.assertEqual(len(noisy), len(state))

    def test_phase_flip(self):
        state = np.array([1.0, -1.0, 1.0, -1.0])
        noisy = self.simulator.apply_phase_flip(state)
        self.assertEqual(len(noisy), len(state))

    def test_depolarizing(self):
        state = np.array([1.0, -1.0, 1.0, -1.0])
        noisy = self.simulator.apply_depolarizing(state)
        self.assertEqual(len(noisy), len(state))


class TestQuantumGradientEstimator(unittest.TestCase):
    """Test QuantumGradientEstimator"""

    def setUp(self):
        self.estimator = QuantumGradientEstimator()

    def test_parameter_shift(self):
        def circuit_fn(params):
            return np.sum(params ** 2)

        params = np.array([1.0, 2.0, 3.0])
        gradient = self.estimator.parameter_shift(circuit_fn, params)

        self.assertEqual(len(gradient), len(params))
        # For f(x) = sum(x^2), gradient should be 2*x
        expected = 2 * params
        np.testing.assert_allclose(gradient, expected, rtol=0.1)

    def test_finite_difference(self):
        def circuit_fn(params):
            return np.sum(params ** 2)

        params = np.array([1.0, 2.0])
        gradient = self.estimator.finite_difference(circuit_fn, params)

        self.assertEqual(len(gradient), len(params))

    def test_spsa_gradient(self):
        def circuit_fn(params):
            return np.sum(params ** 2)

        params = np.array([1.0, 2.0, 3.0])
        gradient = self.estimator.spsa_gradient(circuit_fn, params)

        self.assertEqual(len(gradient), len(params))


class TestQuantumOptimizer(unittest.TestCase):
    """Test QuantumOptimizer"""

    def test_sgd_step(self):
        optimizer = QuantumOptimizer(learning_rate=0.1, optimizer='sgd')
        params = np.array([1.0, 2.0, 3.0])
        gradient = np.array([0.1, 0.2, 0.3])

        new_params = optimizer.step(params, gradient)

        expected = params - 0.1 * gradient
        np.testing.assert_allclose(new_params, expected)

    def test_momentum_step(self):
        optimizer = QuantumOptimizer(learning_rate=0.1, momentum=0.9, optimizer='momentum')
        params = np.array([1.0, 2.0])
        gradient = np.array([0.1, 0.2])

        new_params = optimizer.step(params, gradient)

        # First step should be same as SGD
        expected = params - 0.1 * gradient
        np.testing.assert_allclose(new_params, expected)

    def test_adam_step(self):
        optimizer = QuantumOptimizer(learning_rate=0.1, optimizer='adam')
        params = np.array([1.0, 2.0, 3.0])
        gradient = np.array([0.1, 0.2, 0.3])

        new_params = optimizer.step(params, gradient)

        self.assertEqual(len(new_params), len(params))

    def test_reset(self):
        optimizer = QuantumOptimizer(optimizer='adam')
        optimizer.m = np.array([1.0, 2.0])
        optimizer.v = np.array([0.5, 0.5])
        optimizer.t = 10

        optimizer.reset()

        self.assertIsNone(optimizer.m)
        self.assertIsNone(optimizer.v)
        self.assertEqual(optimizer.t, 0)


class TestQuantumMetrics(unittest.TestCase):
    """Test QuantumMetrics"""

    def test_fidelity(self):
        state1 = np.array([1.0, 0.0]) / np.sqrt(2)
        state2 = np.array([1.0, 0.0]) / np.sqrt(2)

        fidelity = QuantumMetrics.fidelity(state1, state2)
        self.assertAlmostEqual(fidelity, 1.0, places=5)

    def test_fidelity_orthogonal(self):
        state1 = np.array([1.0, 0.0])
        state2 = np.array([0.0, 1.0])

        fidelity = QuantumMetrics.fidelity(state1, state2)
        self.assertAlmostEqual(fidelity, 0.0, places=5)

    def test_trace_distance(self):
        rho1 = np.array([[1.0, 0.0], [0.0, 0.0]])
        rho2 = np.array([[0.0, 0.0], [0.0, 1.0]])

        distance = QuantumMetrics.trace_distance(rho1, rho2)
        self.assertAlmostEqual(distance, 1.0, places=5)

    def test_quantum_volume(self):
        volume = QuantumMetrics.quantum_volume(n_qubits=10, circuit_depth=8)
        self.assertEqual(volume, 256)  # 2^8


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_agent_environment_interaction(self):
        """Test full agent-environment loop"""
        # Create environment
        env = GridWorldEnvironment(size=4)

        # Create agent
        config = AgentConfig(
            num_perception_qubits=16,
            num_decision_qubits=4,
            num_action_qubits=4
        )
        agent = QuantumAgentHost(config)

        # Run episode
        state = env.reset()
        total_reward = 0
        done = False
        steps = 0

        while not done and steps < 100:
            encoded = agent.perceive(state)
            processed = agent.process(encoded)
            action, _ = agent.decide(processed)
            agent.act(action)

            state, reward, done, _ = env.step(action)
            total_reward += reward
            steps += 1

        self.assertGreater(steps, 0)
        agent.close()

    def test_training_pipeline(self):
        """Test training pipeline components"""
        from core.training_pipeline import TrainingConfig

        config = TrainingConfig(
            num_episodes=2,
            max_steps_per_episode=10
        )

        self.assertEqual(config.num_episodes, 2)
        self.assertEqual(config.max_steps_per_episode, 10)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestAgentConfig,
        TestReplayBuffer,
        TestQuantumAgentHost,
        TestGridWorldEnvironment,
        TestContinuousControlEnvironment,
        TestMultiAgentEnvironment,
        TestQuantumStateEncoder,
        TestQuantumCircuitBuilder,
        TestQuantumNoiseSimulator,
        TestQuantumGradientEstimator,
        TestQuantumOptimizer,
        TestQuantumMetrics,
        TestIntegration
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
