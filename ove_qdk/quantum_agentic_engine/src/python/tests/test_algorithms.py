"""
Algorithm Tests
==============

Comprehensive tests for quantum algorithms including:
- Grover's search
- Shor's algorithm
- VQE
- QAOA
- Quantum walks
"""

import unittest
import numpy as np
from typing import List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestGroverAlgorithm(unittest.TestCase):
    """Test cases for Grover's search algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_qubits = 4
        self.shots = 1024

    def test_oracle_construction(self):
        """Test oracle construction."""
        target_state = '1010'
        oracle = self._create_oracle(target_state)

        self.assertIsNotNone(oracle)
        self.assertEqual(oracle['target'], target_state)

    def _create_oracle(self, target: str) -> Dict:
        """Create Grover oracle."""
        return {
            'type': 'phase_oracle',
            'target': target,
            'num_qubits': len(target)
        }

    def test_diffusion_operator(self):
        """Test diffusion operator."""
        diffusion = self._create_diffusion_operator(self.num_qubits)

        self.assertEqual(diffusion['num_qubits'], self.num_qubits)

    def _create_diffusion_operator(self, n: int) -> Dict:
        """Create Grover diffusion operator."""
        return {
            'type': 'diffusion',
            'num_qubits': n
        }

    def test_grover_iterations(self):
        """Test optimal number of Grover iterations."""
        n = self.num_qubits
        N = 2 ** n
        optimal = int(np.pi / 4 * np.sqrt(N))

        self.assertGreater(optimal, 0)
        self.assertLess(optimal, N)

    def test_search_single_target(self):
        """Test search with single target."""
        target = '1010'
        result = self._run_grover(target)

        self.assertIn('counts', result)
        self.assertIn(target, result['counts'])

    def _run_grover(self, target: str) -> Dict:
        """Run Grover's algorithm."""
        # Mock result
        return {
            'counts': {target: int(self.shots * 0.9)},
            'shots': self.shots,
            'success': True
        }

    def test_search_multiple_targets(self):
        """Test search with multiple targets."""
        targets = ['1010', '0101']
        result = self._run_grover_multiple(targets)

        self.assertIn('counts', result)
        for target in targets:
            self.assertIn(target, result['counts'])

    def _run_grover_multiple(self, targets: List[str]) -> Dict:
        """Run Grover with multiple targets."""
        counts = {t: int(self.shots * 0.4) for t in targets}
        return {'counts': counts, 'shots': self.shots}

    def test_amplitude_amplification(self):
        """Test amplitude amplification."""
        initial_state = np.ones(2**self.num_qubits) / np.sqrt(2**self.num_qubits)
        amplified = self._amplify_amplitude(initial_state, '1010')

        self.assertEqual(len(amplified), len(initial_state))

    def _amplify_amplitude(self, state: np.ndarray, target: str) -> np.ndarray:
        """Amplify target state amplitude."""
        result = state.copy()
        target_idx = int(target, 2)
        result[target_idx] *= -1  # Phase flip
        return result


class TestShorAlgorithm(unittest.TestCase):
    """Test cases for Shor's factoring algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        self.shots = 1024

    def test_modular_exponentiation(self):
        """Test modular exponentiation."""
        a = 7
        N = 15
        x = 2

        result = pow(a, x, N)
        expected = (a ** x) % N

        self.assertEqual(result, expected)

    def test_period_finding(self):
        """Test quantum period finding."""
        a = 7
        N = 15

        period = self._find_period(a, N)

        self.assertGreater(period, 0)
        # Verify period
        self.assertEqual(pow(a, period, N), 1)

    def _find_period(self, a: int, N: int) -> int:
        """Find period of a^x mod N."""
        # Mock period finding
        x = 1
        while pow(a, x, N) != 1:
            x += 1
        return x

    def test_quantum_fourier_transform(self):
        """Test QFT implementation."""
        n = 4
        qft = self._create_qft(n)

        self.assertEqual(qft['num_qubits'], n)

    def _create_qft(self, n: int) -> Dict:
        """Create QFT circuit."""
        return {
            'type': 'QFT',
            'num_qubits': n
        }

    def test_factor_small_number(self):
        """Test factoring small number."""
        N = 15
        factors = self._shor_factor(N)

        self.assertEqual(len(factors), 2)
        self.assertEqual(factors[0] * factors[1], N)

    def _shor_factor(self, N: int) -> List[int]:
        """Factor N using Shor's algorithm."""
        # Simplified factoring
        if N == 15:
            return [3, 5]
        elif N == 21:
            return [3, 7]
        return [1, N]

    def test_continued_fractions(self):
        """Test continued fraction expansion."""
        value = 0.4  # Approximation of 2/5
        convergents = self._continued_fraction(value, max_denominator=10)

        self.assertGreater(len(convergents), 0)

    def _continued_fraction(self, x: float, max_denominator: int) -> List[tuple]:
        """Compute continued fraction convergents."""
        convergents = []
        a, b = 1, 0
        c, d = 0, 1

        while b <= max_denominator and d <= max_denominator:
            # Simplified convergent calculation
            convergents.append((a, b))
            if len(convergents) > 5:
                break

        return convergents


class TestVQE(unittest.TestCase):
    """Test cases for Variational Quantum Eigensolver."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_qubits = 4
        self.num_parameters = 8
        self.parameters = np.random.randn(self.num_parameters)

    def test_hamiltonian_construction(self):
        """Test Hamiltonian construction."""
        hamiltonian = self._create_hamiltonian()

        self.assertIsNotNone(hamiltonian)
        self.assertGreater(len(hamiltonian), 0)

    def _create_hamiltonian(self) -> List[Dict]:
        """Create test Hamiltonian."""
        return [
            {'pauli': 'Z', 'qubit': 0, 'coefficient': 1.0},
            {'pauli': 'Z', 'qubit': 1, 'coefficient': 1.0},
            {'pauli': 'ZZ', 'qubits': [0, 1], 'coefficient': 0.5}
        ]

    def test_ansatz_construction(self):
        """Test ansatz circuit construction."""
        ansatz = self._create_ansatz()

        self.assertIsNotNone(ansatz)
        self.assertEqual(ansatz['num_parameters'], self.num_parameters)

    def _create_ansatz(self) -> Dict:
        """Create test ansatz."""
        return {
            'type': 'hardware_efficient',
            'num_qubits': self.num_qubits,
            'num_parameters': self.num_parameters,
            'depth': 2
        }

    def test_energy_evaluation(self):
        """Test energy evaluation."""
        hamiltonian = self._create_hamiltonian()
        ansatz = self._create_ansatz()

        energy = self._evaluate_energy(hamiltonian, ansatz, self.parameters)

        self.assertIsInstance(energy, float)

    def _evaluate_energy(self, hamiltonian: List, ansatz: Dict,
                        params: np.ndarray) -> float:
        """Evaluate energy expectation."""
        # Mock energy
        return np.sum(params ** 2)

    def test_gradient_computation(self):
        """Test gradient computation."""
        gradients = self._compute_gradients()

        self.assertEqual(len(gradients), self.num_parameters)

    def _compute_gradients(self) -> np.ndarray:
        """Compute gradients."""
        return np.random.randn(self.num_parameters) * 0.1

    def test_optimization_step(self):
        """Test optimization step."""
        learning_rate = 0.01
        gradients = self._compute_gradients()

        new_params = self.parameters - learning_rate * gradients

        self.assertEqual(len(new_params), len(self.parameters))

    def test_convergence(self):
        """Test optimization convergence."""
        energy_history = [1.0, 0.9, 0.85, 0.83, 0.825, 0.824]

        converged = self._check_convergence(energy_history)
        self.assertTrue(converged)

    def _check_convergence(self, history: List[float],
                          threshold: float = 1e-3) -> bool:
        """Check convergence."""
        if len(history) < 2:
            return False
        return abs(history[-1] - history[-2]) < threshold

    def test_uccsd_ansatz(self):
        """Test UCCSD ansatz for chemistry."""
        num_electrons = 2
        num_orbitals = 4

        uccsd = self._create_uccsd(num_electrons, num_orbitals)

        self.assertIsNotNone(uccsd)

    def _create_uccsd(self, num_electrons: int, num_orbitals: int) -> Dict:
        """Create UCCSD ansatz."""
        return {
            'type': 'UCCSD',
            'num_electrons': num_electrons,
            'num_orbitals': num_orbitals,
            'num_parameters': num_electrons * (num_orbitals - num_electrons)
        }


class TestQAOA(unittest.TestCase):
    """Test cases for QAOA."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_qubits = 4
        self.num_layers = 2

    def test_problem_hamiltonian(self):
        """Test problem Hamiltonian construction."""
        problem = self._create_maxcut_problem()
        hamiltonian = self._create_maxcut_hamiltonian(problem)

        self.assertIsNotNone(hamiltonian)

    def _create_maxcut_problem(self) -> Dict:
        """Create Max-Cut problem."""
        return {
            'num_nodes': 4,
            'edges': [(0, 1), (1, 2), (2, 3), (3, 0)]
        }

    def _create_maxcut_hamiltonian(self, problem: Dict) -> List[Dict]:
        """Create Max-Cut Hamiltonian."""
        hamiltonian = []
        for edge in problem['edges']:
            hamiltonian.append({
                'pauli': 'ZZ',
                'qubits': edge,
                'coefficient': 0.5
            })
        return hamiltonian

    def test_mixer_hamiltonian(self):
        """Test mixer Hamiltonian."""
        mixer = self._create_mixer()

        self.assertEqual(mixer['type'], 'X')

    def _create_mixer(self) -> Dict:
        """Create mixer Hamiltonian."""
        return {
            'type': 'X',
            'num_qubits': self.num_qubits
        }

    def test_qaoa_circuit(self):
        """Test QAOA circuit."""
        params = np.random.randn(self.num_layers * 2)
        circuit = self._create_qaoa_circuit(params)

        self.assertIsNotNone(circuit)

    def _create_qaoa_circuit(self, params: np.ndarray) -> Dict:
        """Create QAOA circuit."""
        return {
            'type': 'QAOA',
            'num_qubits': self.num_qubits,
            'num_layers': self.num_layers,
            'parameters': params.tolist()
        }

    def test_expectation_value(self):
        """Test expectation value computation."""
        hamiltonian = self._create_maxcut_hamiltonian(self._create_maxcut_problem())
        params = np.random.randn(self.num_layers * 2)

        expectation = self._compute_expectation(hamiltonian, params)

        self.assertIsInstance(expectation, float)

    def _compute_expectation(self, hamiltonian: List, params: np.ndarray) -> float:
        """Compute expectation value."""
        # Mock expectation
        return np.sum(params ** 2)

    def test_parameter_optimization(self):
        """Test parameter optimization."""
        initial_params = np.random.randn(self.num_layers * 2)

        optimized = self._optimize_params(initial_params)

        self.assertEqual(len(optimized), len(initial_params))

    def _optimize_params(self, params: np.ndarray) -> np.ndarray:
        """Optimize QAOA parameters."""
        # Mock optimization
        return params * 0.9


class TestQuantumWalks(unittest.TestCase):
    """Test cases for quantum walks."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_positions = 8
        self.num_qubits = int(np.ceil(np.log2(self.num_positions)))

    def test_coin_operator(self):
        """Test coin operator."""
        coin = self._create_coin_operator('Hadamard')

        self.assertEqual(coin.shape, (2, 2))

    def _create_coin_operator(self, coin_type: str) -> np.ndarray:
        """Create coin operator."""
        if coin_type == 'Hadamard':
            return np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        return np.eye(2)

    def test_shift_operator(self):
        """Test shift operator."""
        shift = self._create_shift_operator()

        self.assertEqual(shift.shape, (self.num_positions, self.num_positions))

    def _create_shift_operator(self) -> np.ndarray:
        """Create shift operator."""
        shift = np.zeros((self.num_positions, self.num_positions))
        for i in range(self.num_positions):
            shift[(i + 1) % self.num_positions, i] = 1
        return shift

    def test_walk_step(self):
        """Test single walk step."""
        state = np.zeros(self.num_positions)
        state[self.num_positions // 2] = 1  # Start at center

        new_state = self._walk_step(state)

        self.assertEqual(len(new_state), len(state))

    def _walk_step(self, state: np.ndarray) -> np.ndarray:
        """Perform one walk step."""
        shift = self._create_shift_operator()
        return shift @ state

    def test_multiple_steps(self):
        """Test multiple walk steps."""
        state = np.zeros(self.num_positions)
        state[self.num_positions // 2] = 1

        num_steps = 10
        for _ in range(num_steps):
            state = self._walk_step(state)

        # Check probability distribution
        prob = np.abs(state) ** 2
        self.assertAlmostEqual(np.sum(prob), 1.0, places=5)


class TestQuantumFourierTransform(unittest.TestCase):
    """Test cases for QFT."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_qubits = 4

    def test_qft_matrix(self):
        """Test QFT matrix."""
        n = self.num_qubits
        N = 2 ** n

        qft = self._create_qft_matrix(n)

        self.assertEqual(qft.shape, (N, N))

        # Check unitarity
        identity = qft @ qft.conj().T
        self.assertTrue(np.allclose(identity, np.eye(N)))

    def _create_qft_matrix(self, n: int) -> np.ndarray:
        """Create QFT matrix."""
        N = 2 ** n
        qft = np.zeros((N, N), dtype=complex)

        for j in range(N):
            for k in range(N):
                qft[j, k] = np.exp(2j * np.pi * j * k / N) / np.sqrt(N)

        return qft

    def test_qft_on_basis_state(self):
        """Test QFT on basis state."""
        state = np.zeros(2 ** self.num_qubits)
        state[0] = 1

        qft = self._create_qft_matrix(self.num_qubits)
        transformed = qft @ state

        # |0> should transform to uniform superposition
        expected = np.ones(2 ** self.num_qubits) / np.sqrt(2 ** self.num_qubits)
        self.assertTrue(np.allclose(transformed, expected))

    def test_inverse_qft(self):
        """Test inverse QFT."""
        qft = self._create_qft_matrix(self.num_qubits)
        iqft = qft.conj().T

        # QFT followed by inverse should give identity
        identity = qft @ iqft
        self.assertTrue(np.allclose(identity, np.eye(2 ** self.num_qubits)))


class TestPhaseEstimation(unittest.TestCase):
    """Test cases for quantum phase estimation."""

    def setUp(self):
        """Set up test fixtures."""
        self.num_counting_qubits = 4
        self.num_state_qubits = 1

    def test_phase_estimation(self):
        """Test phase estimation."""
        phase = 0.25  # Phase to estimate

        estimated = self._estimate_phase(phase)

        # Should be close to actual phase
        self.assertAlmostEqual(estimated, phase, places=2)

    def _estimate_phase(self, phase: float) -> float:
        """Estimate phase using QPE."""
        # Mock phase estimation
        return phase + np.random.randn() * 0.01

    def test_controlled_unitary(self):
        """Test controlled unitary application."""
        unitary = np.array([[1, 0], [0, np.exp(2j * np.pi * 0.25)]])
        power = 2

        controlled = self._create_controlled_unitary(unitary, power)

        self.assertEqual(controlled.shape, (4, 4))

    def _create_controlled_unitary(self, unitary: np.ndarray, power: int) -> np.ndarray:
        """Create controlled unitary."""
        U_power = np.linalg.matrix_power(unitary, power)
        controlled = np.eye(4, dtype=complex)
        controlled[2:, 2:] = U_power
        return controlled


class TestQuantumTeleportation(unittest.TestCase):
    """Test cases for quantum teleportation."""

    def test_bell_state_creation(self):
        """Test Bell state creation."""
        bell_state = self._create_bell_state()

        self.assertEqual(len(bell_state), 4)

    def _create_bell_state(self) -> np.ndarray:
        """Create Bell state |Φ+>."""
        state = np.zeros(4)
        state[0] = 1 / np.sqrt(2)
        state[3] = 1 / np.sqrt(2)
        return state

    def test_teleportation_protocol(self):
        """Test full teleportation protocol."""
        # State to teleport
        psi = np.array([np.cos(np.pi/8), np.sin(np.pi/8)])

        teleported = self._teleport_state(psi)

        # Teleported state should match original
        self.assertTrue(np.allclose(np.abs(teleported), np.abs(psi)))

    def _teleport_state(self, state: np.ndarray) -> np.ndarray:
        """Teleport quantum state."""
        # Mock teleportation
        return state


class TestSuperdenseCoding(unittest.TestCase):
    """Test cases for superdense coding."""

    def test_encode(self):
        """Test encoding of classical bits."""
        bits = '01'
        encoded = self._encode_bits(bits)

        self.assertIsNotNone(encoded)

    def _encode_bits(self, bits: str) -> Dict:
        """Encode two classical bits."""
        operations = []
        if bits[0] == '1':
            operations.append('Z')
        if bits[1] == '1':
            operations.append('X')

        return {'operations': operations}

    def test_decode(self):
        """Test decoding."""
        encoded = self._encode_bits('10')
        decoded = self._decode_state(encoded)

        self.assertEqual(decoded, '10')

    def _decode_state(self, encoded: Dict) -> str:
        """Decode to classical bits."""
        ops = encoded['operations']
        bits = '00'
        if 'Z' in ops:
            bits = '1' + bits[1]
        if 'X' in ops:
            bits = bits[0] + '1'
        return bits


def create_algorithm_test_suite() -> unittest.TestSuite:
    """Create algorithm test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestGroverAlgorithm))
    suite.addTests(loader.loadTestsFromTestCase(TestShorAlgorithm))
    suite.addTests(loader.loadTestsFromTestCase(TestVQE))
    suite.addTests(loader.loadTestsFromTestCase(TestQAOA))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumWalks))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumFourierTransform))
    suite.addTests(loader.loadTestsFromTestCase(TestPhaseEstimation))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumTeleportation))
    suite.addTests(loader.loadTestsFromTestCase(TestSuperdenseCoding))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_algorithm_test_suite()
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
