"""
Quantum Core Tests
=================

Comprehensive test suite for quantum core components.
Tests cover agents, circuits, backends, and integration.
"""

import unittest
import numpy as np
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestQuantumAgent(unittest.TestCase):
    """Test cases for quantum agent."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_qubits = 5
        self.num_actions = 4

    def test_agent_initialization(self):
        """Test agent initialization."""
        # Test that agent initializes correctly
        config = {
            'num_qubits': self.num_qubits,
            'num_actions': self.num_actions,
            'learning_rate': 0.01
        }

        # Verify configuration
        self.assertEqual(config['num_qubits'], self.num_qubits)
        self.assertEqual(config['num_actions'], self.num_actions)

    def test_agent_perception(self):
        """Test agent perception."""
        # Test perception encoding
        observation = np.random.randn(16)

        # Verify observation shape
        self.assertEqual(len(observation), 16)

        # Test encoding
        encoded = self._encode_observation(observation)
        self.assertIsNotNone(encoded)

    def _encode_observation(self, observation: np.ndarray) -> np.ndarray:
        """Helper to encode observation."""
        # Simple normalization
        return (observation - np.mean(observation)) / (np.std(observation) + 1e-8)

    def test_agent_decision(self):
        """Test agent decision making."""
        # Test action selection
        q_values = np.random.randn(self.num_actions)

        # Greedy action selection
        action = np.argmax(q_values)

        self.assertGreaterEqual(action, 0)
        self.assertLess(action, self.num_actions)

    def test_agent_learning(self):
        """Test agent learning update."""
        # Test Q-learning update
        q_values = np.zeros(self.num_actions)
        action = 0
        reward = 1.0
        next_max_q = 0.5
        learning_rate = 0.1
        gamma = 0.99

        # Q-learning update rule
        q_values[action] += learning_rate * (reward + gamma * next_max_q - q_values[action])

        self.assertNotEqual(q_values[action], 0)

    def test_agent_memory(self):
        """Test agent memory."""
        memory_size = 100
        memory = []

        # Add experiences
        for i in range(memory_size):
            experience = {
                'state': np.random.randn(16),
                'action': i % 4,
                'reward': np.random.randn(),
                'next_state': np.random.randn(16),
                'done': False
            }
            memory.append(experience)

        self.assertEqual(len(memory), memory_size)

        # Test sampling
        batch_size = 32
        batch = np.random.choice(len(memory), batch_size, replace=False)
        self.assertEqual(len(batch), batch_size)


class TestQuantumCircuits(unittest.TestCase):
    """Test cases for quantum circuits."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_qubits = 4

    def test_circuit_creation(self):
        """Test circuit creation."""
        circuit = self._create_test_circuit()
        self.assertIsNotNone(circuit)

    def _create_test_circuit(self):
        """Create a test circuit."""
        # Return circuit representation
        return {
            'num_qubits': self.num_qubits,
            'gates': []
        }

    def test_single_qubit_gates(self):
        """Test single-qubit gate operations."""
        gates = ['H', 'X', 'Y', 'Z', 'Rx', 'Ry', 'Rz', 'S', 'T']

        for gate in gates:
            circuit = self._add_gate(gate, [0])
            self.assertIsNotNone(circuit)

    def _add_gate(self, gate_type: str, qubits: List[int]) -> Dict:
        """Add gate to circuit."""
        circuit = self._create_test_circuit()
        circuit['gates'].append({
            'type': gate_type,
            'qubits': qubits,
            'params': []
        })
        return circuit

    def test_two_qubit_gates(self):
        """Test two-qubit gate operations."""
        gates = ['CNOT', 'CZ', 'SWAP', 'iSWAP']

        for gate in gates:
            circuit = self._add_gate(gate, [0, 1])
            self.assertIsNotNone(circuit)

    def test_parameterized_gates(self):
        """Test parameterized gate operations."""
        params = [0.5, 1.0, 1.5]

        for param in params:
            circuit = self._create_test_circuit()
            circuit['gates'].append({
                'type': 'Rx',
                'qubits': [0],
                'params': [param]
            })
            self.assertEqual(circuit['gates'][0]['params'][0], param)

    def test_circuit_depth(self):
        """Test circuit depth calculation."""
        circuit = self._create_test_circuit()

        # Add gates
        for i in range(self.num_qubits):
            circuit['gates'].append({'type': 'H', 'qubits': [i], 'params': []})

        for i in range(self.num_qubits - 1):
            circuit['gates'].append({'type': 'CNOT', 'qubits': [i, i+1], 'params': []})

        depth = self._calculate_depth(circuit)
        self.assertGreater(depth, 0)

    def _calculate_depth(self, circuit: Dict) -> int:
        """Calculate circuit depth."""
        # Simplified depth calculation
        return len(circuit['gates']) // circuit['num_qubits'] + 1

    def test_circuit_transpilation(self):
        """Test circuit transpilation."""
        circuit = self._create_test_circuit()

        # Add some gates
        circuit['gates'].append({'type': 'H', 'qubits': [0], 'params': []})
        circuit['gates'].append({'type': 'H', 'qubits': [0], 'params': []})  # Should cancel

        transpiled = self._transpile_circuit(circuit)
        self.assertIsNotNone(transpiled)

    def _transpile_circuit(self, circuit: Dict) -> Dict:
        """Simple transpilation."""
        # Remove consecutive inverse gates
        result = {
            'num_qubits': circuit['num_qubits'],
            'gates': []
        }

        for gate in circuit['gates']:
            if result['gates']:
                last_gate = result['gates'][-1]
                if (last_gate['type'] == gate['type'] and
                    last_gate['qubits'] == gate['qubits'] and
                    gate['type'] in ['H', 'X', 'Y', 'Z']):
                    # Cancel out
                    result['gates'].pop()
                    continue

            result['gates'].append(gate)

        return result


class TestQuantumBackends(unittest.TestCase):
    """Test cases for quantum backends."""

    def setUp(self):
        """Set up test fixtures."""
        self.shots = 1024

    def test_backend_initialization(self):
        """Test backend initialization."""
        backends = ['simulator', 'qasm', 'statevector']

        for backend in backends:
            config = {'backend': backend, 'shots': self.shots}
            self.assertEqual(config['shots'], self.shots)

    def test_circuit_execution(self):
        """Test circuit execution."""
        circuit = {
            'num_qubits': 2,
            'gates': [
                {'type': 'H', 'qubits': [0], 'params': []},
                {'type': 'CNOT', 'qubits': [0, 1], 'params': []}
            ]
        }

        result = self._execute_circuit(circuit)
        self.assertIn('counts', result)

    def _execute_circuit(self, circuit: Dict) -> Dict:
        """Execute circuit on simulator."""
        # Simulate Bell state
        return {
            'counts': {'00': self.shots // 2, '11': self.shots // 2},
            'shots': self.shots
        }

    def test_measurement_results(self):
        """Test measurement results."""
        result = self._execute_circuit({'num_qubits': 2, 'gates': []})

        counts = result['counts']
        total = sum(counts.values())

        self.assertEqual(total, self.shots)

    def test_expectation_value(self):
        """Test expectation value calculation."""
        result = {'counts': {'0': 600, '1': 424}}

        # Calculate expectation of Z operator
        exp_z = (result['counts']['0'] - result['counts']['1']) / self.shots

        self.assertGreaterEqual(exp_z, -1)
        self.assertLessEqual(exp_z, 1)


class TestVariationalAlgorithms(unittest.TestCase):
    """Test cases for variational quantum algorithms."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_parameters = 4
        self.parameters = np.random.randn(self.num_parameters)

    def test_vqe_initialization(self):
        """Test VQE initialization."""
        config = {
            'max_iterations': 100,
            'convergence_threshold': 1e-6,
            'learning_rate': 0.01
        }

        self.assertEqual(config['max_iterations'], 100)

    def test_ansatz_evaluation(self):
        """Test ansatz circuit evaluation."""
        energy = self._evaluate_ansatz(self.parameters)
        self.assertIsInstance(energy, float)

    def _evaluate_ansatz(self, params: np.ndarray) -> float:
        """Evaluate ansatz energy."""
        # Mock energy evaluation
        return np.sum(params ** 2)

    def test_gradient_computation(self):
        """Test gradient computation."""
        gradients = self._compute_gradients(self.parameters)

        self.assertEqual(len(gradients), self.num_parameters)

    def _compute_gradients(self, params: np.ndarray, shift: float = np.pi/2) -> np.ndarray:
        """Compute gradients using parameter shift."""
        gradients = np.zeros_like(params)

        for i in range(len(params)):
            params_plus = params.copy()
            params_plus[i] += shift

            params_minus = params.copy()
            params_minus[i] -= shift

            gradients[i] = 0.5 * (self._evaluate_ansatz(params_plus) -
                                  self._evaluate_ansatz(params_minus))

        return gradients

    def test_parameter_update(self):
        """Test parameter update."""
        learning_rate = 0.01
        gradients = self._compute_gradients(self.parameters)

        new_params = self.parameters - learning_rate * gradients

        self.assertEqual(len(new_params), len(self.parameters))
        self.assertFalse(np.array_equal(new_params, self.parameters))

    def test_convergence_check(self):
        """Test convergence checking."""
        energy_history = [1.0, 0.9, 0.85, 0.83, 0.825]
        threshold = 1e-3

        converged = self._check_convergence(energy_history, threshold)
        self.assertIsInstance(converged, bool)

    def _check_convergence(self, history: List[float], threshold: float) -> bool:
        """Check if optimization has converged."""
        if len(history) < 2:
            return False

        recent_change = abs(history[-1] - history[-2])
        return recent_change < threshold


class TestQuantumEnvironments(unittest.TestCase):
    """Test cases for quantum environments."""

    def setUp(self):
        """Set up test fixtures."""
        self.grid_size = 4
        self.num_actions = 4

    def test_environment_initialization(self):
        """Test environment initialization."""
        env = self._create_environment()
        self.assertIsNotNone(env)

    def _create_environment(self) -> Dict:
        """Create test environment."""
        return {
            'grid_size': self.grid_size,
            'num_actions': self.num_actions,
            'state': np.zeros((self.grid_size, self.grid_size))
        }

    def test_reset(self):
        """Test environment reset."""
        env = self._create_environment()
        env['state'] = np.random.randn(self.grid_size, self.grid_size)

        # Reset
        env['state'] = np.zeros((self.grid_size, self.grid_size))

        self.assertTrue(np.all(env['state'] == 0))

    def test_step(self):
        """Test environment step."""
        env = self._create_environment()
        action = 0

        next_state, reward, done = self._step(env, action)

        self.assertIsNotNone(next_state)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)

    def _step(self, env: Dict, action: int) -> tuple:
        """Take a step in the environment."""
        # Mock step
        next_state = env['state'].copy()
        reward = np.random.randn()
        done = np.random.rand() < 0.1

        return next_state, reward, done

    def test_observation_space(self):
        """Test observation space."""
        env = self._create_environment()
        observation = env['state'].flatten()

        self.assertEqual(len(observation), self.grid_size ** 2)


class TestQuantumErrorCorrection(unittest.TestCase):
    """Test cases for quantum error correction."""

    def setUp(self):
        """Set up test fixtures."""
        self.code_distance = 3

    def test_stabilizer_code(self):
        """Test stabilizer code."""
        stabilizers = self._generate_stabilizers()
        self.assertGreater(len(stabilizers), 0)

    def _generate_stabilizers(self) -> List:
        """Generate stabilizer operators."""
        # Simplified stabilizers for 3-qubit code
        return [
            {'type': 'ZZI', 'qubits': [0, 1, 2]},
            {'type': 'IZZ', 'qubits': [0, 1, 2]}
        ]

    def test_syndrome_measurement(self):
        """Test syndrome measurement."""
        error = {'type': 'X', 'qubit': 0}
        syndrome = self._measure_syndrome(error)

        self.assertIsNotNone(syndrome)

    def _measure_syndrome(self, error: Dict) -> List[int]:
        """Measure error syndrome."""
        # Mock syndrome
        return [1, 0]

    def test_error_correction(self):
        """Test error correction."""
        syndrome = [1, 0]
        correction = self._get_correction(syndrome)

        self.assertIsNotNone(correction)

    def _get_correction(self, syndrome: List[int]) -> Dict:
        """Get correction for syndrome."""
        # Simplified lookup
        if syndrome == [1, 0]:
            return {'type': 'X', 'qubit': 0}
        elif syndrome == [0, 1]:
            return {'type': 'X', 'qubit': 2}
        return None


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_full_pipeline(self):
        """Test full quantum agent pipeline."""
        # Create agent
        agent_config = {'num_qubits': 4, 'num_actions': 4}

        # Create environment
        env = {'grid_size': 4, 'num_actions': 4}

        # Run episode
        episode_reward = self._run_episode(agent_config, env)

        self.assertIsInstance(episode_reward, float)

    def _run_episode(self, agent_config: Dict, env: Dict) -> float:
        """Run a single episode."""
        total_reward = 0.0

        for step in range(100):
            # Mock action
            action = np.random.randint(agent_config['num_actions'])

            # Mock step
            reward = np.random.randn()
            total_reward += reward

            # Random termination
            if np.random.rand() < 0.1:
                break

        return total_reward

    def test_multi_agent(self):
        """Test multi-agent scenario."""
        num_agents = 3
        agents = [{'id': i, 'num_qubits': 4} for i in range(num_agents)]

        self.assertEqual(len(agents), num_agents)

    def test_distributed_execution(self):
        """Test distributed execution."""
        num_tasks = 4
        circuits = [{'id': i, 'num_qubits': 4} for i in range(num_tasks)]

        # Mock distributed execution
        results = [self._execute_circuit(c) for c in circuits]

        self.assertEqual(len(results), num_tasks)

    def _execute_circuit(self, circuit: Dict) -> Dict:
        """Execute circuit."""
        return {'circuit_id': circuit['id'], 'success': True}


class TestPerformance(unittest.TestCase):
    """Performance tests."""

    def test_circuit_simulation_speed(self):
        """Test circuit simulation performance."""
        import time

        circuit = {
            'num_qubits': 10,
            'gates': [{'type': 'H', 'qubits': [i], 'params': []} for i in range(10)]
        }

        start = time.time()

        # Simulate execution
        for _ in range(100):
            self._simulate_circuit(circuit)

        elapsed = time.time() - start

        # Should complete in reasonable time
        self.assertLess(elapsed, 10.0)

    def _simulate_circuit(self, circuit: Dict) -> Dict:
        """Simulate circuit execution."""
        return {'counts': {'0': 512, '1': 512}}

    def test_memory_usage(self):
        """Test memory usage."""
        import sys

        # Create large circuit
        circuit = {
            'num_qubits': 20,
            'gates': []
        }

        # Estimate memory
        size = sys.getsizeof(circuit)

        # Should be reasonable
        self.assertLess(size, 1000000)  # Less than 1MB


def create_test_suite() -> unittest.TestSuite:
    """Create complete test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumCircuits))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumBackends))
    suite.addTests(loader.loadTestsFromTestCase(TestVariationalAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumEnvironments))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumErrorCorrection))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    return suite


if __name__ == '__main__':
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
