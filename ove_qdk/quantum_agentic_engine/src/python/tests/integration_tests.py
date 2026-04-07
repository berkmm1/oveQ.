#!/usr/bin/env python3
"""
Integration Tests Module
End-to-end integration tests for the quantum agentic engine
Part of the Quantum Agentic Loop Engine
"""

import unittest
import numpy as np
from typing import Dict, Any, List, Tuple
import logging
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestQuantumAgentCore(unittest.TestCase):
    """Test quantum agent core functionality"""

    @classmethod
    def setUpClass(cls):
        logger.info("Setting up Quantum Agent Core tests...")

    def test_agent_initialization(self):
        """Test agent initialization"""
        # Test that agent can be initialized
        from agents.quantum_agent_manager import AgentConfig, AgentRole, QuantumAgent

        config = AgentConfig(
            agent_id="test_agent",
            role=AgentRole.EXPLORER,
            num_qubits=4
        )

        agent = QuantumAgent(config)

        self.assertEqual(agent.config.agent_id, "test_agent")
        self.assertEqual(agent.config.role, AgentRole.EXPLORER)
        self.assertEqual(agent.config.num_qubits, 4)

    def test_agent_perception(self):
        """Test agent perception"""
        from agents.quantum_agent_manager import AgentConfig, QuantumAgent

        config = AgentConfig(agent_id="test_agent", num_qubits=4)
        agent = QuantumAgent(config)

        observation = np.random.randn(8)
        encoded = agent.perceive(observation)

        self.assertEqual(len(encoded), config.num_qubits)

    def test_agent_decision(self):
        """Test agent decision making"""
        from agents.quantum_agent_manager import AgentConfig, QuantumAgent

        config = AgentConfig(agent_id="test_agent", num_qubits=4)
        agent = QuantumAgent(config)

        observation = np.random.randn(8)
        encoded = agent.perceive(observation)
        action = agent.decide(encoded)

        self.assertIsInstance(action, int)
        self.assertGreaterEqual(action, 0)

    def test_experience_storage(self):
        """Test experience storage"""
        from agents.quantum_agent_manager import AgentConfig, QuantumAgent

        config = AgentConfig(agent_id="test_agent", num_qubits=4, memory_size=100)
        agent = QuantumAgent(config)

        # Store experiences
        for i in range(10):
            experience = (
                np.random.randn(4),
                i % 4,
                np.random.randn(),
                np.random.randn(4),
                False
            )
            agent.store_experience(experience)

        self.assertEqual(len(agent.memory), 10)

    def test_agent_learning(self):
        """Test agent learning"""
        from agents.quantum_agent_manager import AgentConfig, QuantumAgent

        config = AgentConfig(
            agent_id="test_agent",
            num_qubits=4,
            memory_size=100,
            batch_size=8
        )
        agent = QuantumAgent(config)

        # Fill memory
        for i in range(20):
            experience = (
                np.random.randn(4),
                i % 4,
                np.random.randn(),
                np.random.randn(4),
                False
            )
            agent.store_experience(experience)

        # Learn
        loss = agent.learn()

        self.assertIsInstance(loss, float)


class TestQuantumEnvironments(unittest.TestCase):
    """Test quantum-enhanced environments"""

    def test_grid_world_creation(self):
        """Test grid world environment creation"""
        from environments.quantum_env import QuantumGridWorld

        env = QuantumGridWorld(size=5, num_goals=2)

        self.assertEqual(env.size, 5)
        self.assertEqual(env.num_goals, 2)

    def test_grid_world_reset(self):
        """Test grid world reset"""
        from environments.quantum_env import QuantumGridWorld

        env = QuantumGridWorld(size=5, num_goobs=2)
        obs = env.reset()

        self.assertIsInstance(obs, np.ndarray)
        self.assertEqual(len(env.goal_positions), 2)

    def test_grid_world_step(self):
        """Test grid world step"""
        from environments.quantum_env import QuantumGridWorld

        env = QuantumGridWorld(size=5, num_goals=2)
        env.reset()

        obs, reward, done, info = env.step(0)

        self.assertIsInstance(obs, np.ndarray)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)

    def test_continuous_environment(self):
        """Test continuous environment"""
        from environments.quantum_env import QuantumContinuousEnvironment

        env = QuantumContinuousEnvironment(state_dim=8, action_dim=4)
        obs = env.reset()

        self.assertEqual(len(obs), env.observation_space.shape[0])

        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)

        self.assertIsInstance(reward, float)

    def test_maze_environment(self):
        """Test maze environment"""
        from environments.quantum_env import QuantumMazeEnvironment

        env = QuantumMazeEnvironment(width=10, height=10)
        obs = env.reset()

        self.assertIsInstance(obs, np.ndarray)

        # Check maze was generated
        self.assertIsNotNone(env.maze)
        self.assertEqual(env.maze.shape, (10, 10))


class TestQuantumML(unittest.TestCase):
    """Test quantum machine learning components"""

    def test_feature_map(self):
        """Test quantum feature map"""
        from ml.quantum_ml import QuantumFeatureMap

        feature_map = QuantumFeatureMap(num_qubits=4, feature_dimension=8)

        X = np.random.randn(10, 8)
        X_mapped = feature_map.fit_transform(X)

        self.assertEqual(X_mapped.shape[0], 10)

    def test_quantum_kernel(self):
        """Test quantum kernel"""
        from ml.quantum_ml import QuantumKernel

        kernel = QuantumKernel(num_qubits=4, kernel_type="zz")

        x1 = np.random.randn(8)
        x2 = np.random.randn(8)

        similarity = kernel.build_circuit(x1, x2)

        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)

    def test_kernel_matrix(self):
        """Test kernel matrix computation"""
        from ml.quantum_ml import QuantumKernel

        kernel = QuantumKernel(num_qubits=4)

        X = np.random.randn(5, 8)
        K = kernel.compute_kernel_matrix(X)

        self.assertEqual(K.shape, (5, 5))
        self.assertTrue(np.allclose(K, K.T))  # Symmetric

    def test_quantum_nn_creation(self):
        """Test quantum neural network creation"""
        from ml.quantum_ml import QuantumNeuralNetwork, QuantumMLConfig

        config = QuantumMLConfig(num_qubits=4, num_layers=2)
        model = QuantumNeuralNetwork(config)

        self.assertEqual(model.config.num_qubits, 4)

    def test_quantum_nn_forward(self):
        """Test quantum neural network forward pass"""
        from ml.quantum_ml import QuantumNeuralNetwork, QuantumMLConfig

        config = QuantumMLConfig(num_qubits=4, num_layers=2)
        model = QuantumNeuralNetwork(config)
        model.build(input_dim=8)

        X = np.random.randn(5, 8)
        output = model.forward(X)

        self.assertEqual(len(output), 5)

    def test_quantum_svm(self):
        """Test quantum SVM"""
        from ml.quantum_ml import QuantumSupportVectorMachine

        svm = QuantumSupportVectorMachine(num_qubits=4)

        # Create simple dataset
        X = np.random.randn(20, 8)
        y = np.random.choice([-1, 1], 20)

        svm.fit(X, y)
        predictions = svm.predict(X)

        self.assertEqual(len(predictions), 20)


class TestQuantumTraining(unittest.TestCase):
    """Test quantum training components"""

    def test_training_config(self):
        """Test training configuration"""
        from training.quantum_trainer import TrainingConfig, TrainingMode, OptimizerType

        config = TrainingConfig(
            mode=TrainingMode.EPISODIC,
            optimizer=OptimizerType.ADAM,
            learning_rate=0.001
        )

        self.assertEqual(config.mode, TrainingMode.EPISODIC)
        self.assertEqual(config.optimizer, OptimizerType.ADAM)

    def test_experience_buffer(self):
        """Test experience buffer"""
        from training.quantum_trainer import ExperienceBuffer

        buffer = ExperienceBuffer(capacity=100)

        # Add experiences
        for i in range(50):
            buffer.push((np.random.randn(4), i % 4, 0.0, np.random.randn(4), False))

        self.assertEqual(len(buffer), 50)

        # Sample
        batch = buffer.sample(10)
        self.assertEqual(len(batch), 10)

    def test_quantum_optimizer(self):
        """Test quantum optimizer"""
        from training.quantum_trainer import QuantumOptimizer, OptimizerType

        optimizer = QuantumOptimizer(OptimizerType.ADAM, learning_rate=0.01)

        params = np.array([1.0, 2.0, 3.0])
        gradients = np.array([0.1, 0.2, 0.3])

        new_params = optimizer.step(params, gradients)

        self.assertEqual(len(new_params), 3)

    def test_gae_computation(self):
        """Test GAE computation"""
        from training.quantum_trainer import QuantumTrainer, TrainingConfig

        # Mock agent and environment
        class MockAgent:
            pass

        class MockEnv:
            pass

        config = TrainingConfig()
        trainer = QuantumTrainer(MockAgent(), MockEnv(), config)

        rewards = [1.0, 0.5, 0.0, 1.0]
        values = [0.5, 0.4, 0.3, 0.2]
        dones = [False, False, False, True]

        advantages, returns = trainer.compute_gae(rewards, values, dones)

        self.assertEqual(len(advantages), 4)
        self.assertEqual(len(returns), 4)


class TestQuantumVisualization(unittest.TestCase):
    """Test quantum visualization components"""

    def test_bloch_vector(self):
        """Test Bloch vector"""
        from utils.quantum_visualization import BlochVector

        bv = BlochVector(1.0, 0.0, 0.0)
        x, y, z = bv.to_cartesian()

        self.assertEqual(x, 1.0)
        self.assertEqual(y, 0.0)
        self.assertEqual(z, 0.0)

    def test_state_visualizer(self):
        """Test state visualizer"""
        from utils.quantum_visualization import QuantumStateVisualizer

        visualizer = QuantumStateVisualizer(num_qubits=2)

        # Bell state
        state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])

        probs = visualizer.compute_probabilities(state)

        self.assertIn('00', probs)
        self.assertIn('11', probs)

    def test_entropy_computation(self):
        """Test entropy computation"""
        from utils.quantum_visualization import QuantumStateVisualizer

        visualizer = QuantumStateVisualizer(num_qubits=2)

        # Bell state
        state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])

        entropy = visualizer.compute_entropy(state)

        self.assertGreaterEqual(entropy, 0)

    def test_circuit_visualizer(self):
        """Test circuit visualizer"""
        from utils.quantum_visualization import CircuitVisualizer

        visualizer = CircuitVisualizer(num_qubits=3)

        visualizer.add_gate('H', [0])
        visualizer.add_gate('CNOT', [0, 1])
        visualizer.add_gate('X', [2])

        diagram = visualizer.to_ascii()

        self.assertIn('H', diagram)
        self.assertIn('CNOT', diagram)

    def test_training_visualizer(self):
        """Test training visualizer"""
        from utils.quantum_visualization import TrainingVisualizer

        visualizer = TrainingVisualizer()

        # Add metrics
        for i in range(10):
            visualizer.update({'rewards': float(i)})

        stats = visualizer.get_statistics('rewards')

        self.assertIn('mean', stats)


class TestBenchmarks(unittest.TestCase):
    """Test benchmark components"""

    def test_latency_benchmark(self):
        """Test latency benchmark"""
        from benchmarks.performance_suite import LatencyBenchmark

        benchmark = LatencyBenchmark("test")

        def test_func():
            return sum(range(100))

        result = benchmark.run(test_func, iterations=100)

        self.assertEqual(result.name, "test")
        self.assertEqual(result.iterations, 100)

    def test_throughput_benchmark(self):
        """Test throughput benchmark"""
        from benchmarks.performance_suite import ThroughputBenchmark

        benchmark = ThroughputBenchmark("test")

        def test_func():
            return sum(range(10))

        result = benchmark.run(test_func, duration=0.1)

        self.assertGreater(result.value, 0)

    def test_accuracy_benchmark(self):
        """Test accuracy benchmark"""
        from benchmarks.performance_suite import AccuracyBenchmark

        benchmark = AccuracyBenchmark("test")

        def test_func():
            return 42.0

        result = benchmark.run(test_func, expected=42.0, iterations=10)

        self.assertGreaterEqual(result.value, 0)

    def test_circuit_benchmark(self):
        """Test circuit benchmark"""
        from benchmarks.performance_suite import QuantumCircuitBenchmark

        benchmark = QuantumCircuitBenchmark(num_qubits=4)
        results = benchmark.run_all()

        self.assertIn('state_preparation', results)
        self.assertIn('gate_application', results)


class TestIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""

    def test_full_agent_training_pipeline(self):
        """Test complete agent training pipeline"""
        from agents.quantum_agent_manager import AgentConfig, QuantumAgent
        from environments.quantum_env import QuantumGridWorld
        from training.quantum_trainer import TrainingConfig, QuantumTrainer

        # Create components
        config = AgentConfig(agent_id="e2e_agent", num_qubits=4)
        agent = QuantumAgent(config)

        env = QuantumGridWorld(size=4, num_goals=1)

        train_config = TrainingConfig(num_epochs=2, log_frequency=1)
        trainer = QuantumTrainer(agent, env, train_config)

        # Run a few episodes
        for _ in range(3):
            reward = trainer.train_episode()

        self.assertGreater(len(agent.memory), 0)

    def test_multi_agent_system(self):
        """Test multi-agent system"""
        from agents.quantum_agent_manager import QuantumAgentManager, create_explorer_agent, create_exploiter_agent

        manager = QuantumAgentManager()

        # Create agents
        explorer = create_explorer_agent("explorer_1", num_qubits=4)
        exploiter = create_exploiter_agent("exploiter_1", num_qubits=4)

        manager.create_agent(explorer.config)
        manager.create_agent(exploiter.config)

        # Establish entanglement
        manager.establish_entanglement("explorer_1", "exploiter_1")

        # Check entanglement
        agent1 = manager.get_agent("explorer_1")
        self.assertIn("exploiter_1", agent1.state.entangled_partners)

    def test_quantum_ml_pipeline(self):
        """Test quantum ML pipeline"""
        from ml.quantum_ml import QuantumNeuralNetwork, QuantumMLConfig

        # Create model
        config = QuantumMLConfig(num_qubits=4, num_layers=2, epochs=5)
        model = QuantumNeuralNetwork(config)

        # Create data
        np.random.seed(42)
        X = np.random.randn(50, 8)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)

        # Build and train
        model.build(X.shape[1])
        model.fit(X, y, verbose=False)

        # Evaluate
        metrics = model.evaluate(X, y)

        self.assertIn('loss', metrics)

    def test_save_load_agent(self):
        """Test agent save and load"""
        import tempfile
        import os

        from agents.quantum_agent_manager import AgentConfig, QuantumAgent

        config = AgentConfig(agent_id="save_test", num_qubits=4)
        agent = QuantumAgent(config)

        # Add some experiences
        for i in range(10):
            experience = (
                np.random.randn(4),
                i % 4,
                float(i),
                np.random.randn(4),
                False
            )
            agent.store_experience(experience)

        # Save
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "agent.json")
            agent.save(filepath)

            # Load
            loaded_agent = QuantumAgent.load(filepath)

            self.assertEqual(loaded_agent.config.agent_id, "save_test")


def run_integration_tests():
    """Run all integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumAgentCore))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumEnvironments))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumML))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumTraining))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumVisualization))
    suite.addTests(loader.loadTestsFromTestCase(TestBenchmarks))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationEndToEnd))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("Integration Tests")
    print("=" * 60)

    success = run_integration_tests()

    sys.exit(0 if success else 1)
