#!/usr/bin/env python3
"""
Quantum Utilities for Agentic Engine
Helper functions for quantum state manipulation and visualization
"""

import numpy as np
from typing import List, Tuple, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class QuantumStateEncoder:
    """Encode classical data into quantum states"""

    @staticmethod
    def angle_encoding(data: np.ndarray, normalize: bool = True) -> np.ndarray:
        """
        Encode data using angle encoding
        Maps data to rotation angles: θ = arccos(x)
        """
        if normalize:
            data = np.clip(data, -1, 1)

        angles = np.arccos(data)
        return angles

    @staticmethod
    def amplitude_encoding(data: np.ndarray) -> np.ndarray:
        """
        Encode data using amplitude encoding
        Normalizes data to represent quantum amplitudes
        """
        norm = np.linalg.norm(data)
        if norm > 0:
            return data / norm
        return data

    @staticmethod
    def basis_encoding(data: np.ndarray, n_qubits: int) -> np.ndarray:
        """
        Encode data using basis encoding
        Converts integers to binary representation
        """
        if np.issubdtype(data.dtype, np.integer):
            max_val = 2 ** n_qubits
            binary = np.unpackbits(
                data.astype(np.uint8).reshape(-1, 1),
                axis=1
            )[:, -n_qubits:]
            return binary.flatten()

        # For continuous data, threshold
        return (data > 0).astype(int)

    @staticmethod
    def dense_angle_encoding(data: np.ndarray) -> np.ndarray:
        """
        Dense angle encoding using both Rx and Ry rotations
        """
        angles_x = np.arccos(np.clip(data, -1, 1))
        angles_y = np.arcsin(np.clip(data, -1, 1))
        return np.concatenate([angles_x, angles_y])


class QuantumCircuitBuilder:
    """Build quantum circuits programmatically"""

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.gates = []

    def add_rotation(self, qubit: int, axis: str, angle: float):
        """Add rotation gate"""
        self.gates.append({
            'type': 'rotation',
            'qubit': qubit,
            'axis': axis,
            'angle': angle
        })

    def add_cnot(self, control: int, target: int):
        """Add CNOT gate"""
        self.gates.append({
            'type': 'cnot',
            'control': control,
            'target': target
        })

    def add_hadamard(self, qubit: int):
        """Add Hadamard gate"""
        self.gates.append({
            'type': 'hadamard',
            'qubit': qubit
        })

    def add_entanglement_layer(self, pattern: str = 'linear'):
        """Add entanglement layer"""
        if pattern == 'linear':
            for i in range(self.n_qubits - 1):
                self.add_cnot(i, i + 1)
        elif pattern == 'circular':
            for i in range(self.n_qubits):
                self.add_cnot(i, (i + 1) % self.n_qubits)
        elif pattern == 'full':
            for i in range(self.n_qubits):
                for j in range(i + 1, self.n_qubits):
                    self.add_cnot(i, j)

    def build_variational_layer(
        self,
        params: np.ndarray,
        entanglement: str = 'linear'
    ):
        """Build a variational layer with rotations and entanglement"""
        # Single-qubit rotations
        for i in range(self.n_qubits):
            self.add_rotation(i, 'x', params[i * 3])
            self.add_rotation(i, 'y', params[i * 3 + 1])
            self.add_rotation(i, 'z', params[i * 3 + 2])

        # Entanglement
        self.add_entanglement_layer(entanglement)

    def to_qsharp(self) -> str:
        """Convert to Q# code"""
        lines = ["operation GeneratedCircuit(qubits : Qubit[]) : Unit {"]

        for gate in self.gates:
            if gate['type'] == 'rotation':
                if gate['axis'] == 'x':
                    lines.append(f"    Rx({gate['angle']}, qubits[{gate['qubit']}]);")
                elif gate['axis'] == 'y':
                    lines.append(f"    Ry({gate['angle']}, qubits[{gate['qubit']}]);")
                elif gate['axis'] == 'z':
                    lines.append(f"    Rz({gate['angle']}, qubits[{gate['qubit']}]);")
            elif gate['type'] == 'cnot':
                lines.append(f"    CNOT(qubits[{gate['control']}], qubits[{gate['target']}]);")
            elif gate['type'] == 'hadamard':
                lines.append(f"    H(qubits[{gate['qubit']}]);")

        lines.append("}")
        return '\n'.join(lines)


class QuantumNoiseSimulator:
    """Simulate quantum noise effects"""

    def __init__(self, error_rate: float = 0.001):
        self.error_rate = error_rate

    def apply_bit_flip(self, state: np.ndarray) -> np.ndarray:
        """Apply bit flip noise"""
        mask = np.random.random(state.shape) < self.error_rate
        noisy_state = state.copy()
        noisy_state[mask] *= -1
        return noisy_state

    def apply_phase_flip(self, state: np.ndarray) -> np.ndarray:
        """Apply phase flip noise"""
        mask = np.random.random(state.shape) < self.error_rate
        noisy_state = state.copy()
        noisy_state[mask] = -noisy_state[mask]
        return noisy_state

    def apply_depolarizing(self, state: np.ndarray) -> np.ndarray:
        """Apply depolarizing noise"""
        mask = np.random.random(state.shape) < self.error_rate
        noisy_state = state.copy()
        noisy_state[mask] = np.random.choice([-1, 1], size=mask.sum())
        return noisy_state

    def apply_amplitude_damping(self, state: np.ndarray, gamma: float = 0.01) -> np.ndarray:
        """Apply amplitude damping"""
        damping = np.random.random(state.shape) < gamma
        damped_state = state.copy()
        damped_state[damping] = 0
        return damped_state


class QuantumStateVisualizer:
    """Visualize quantum states"""

    @staticmethod
    def bloch_coordinates(amplitude: complex) -> Tuple[float, float, float]:
        """
        Convert qubit amplitude to Bloch sphere coordinates
        Returns (x, y, z)
        """
        # |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩
        prob_0 = np.abs(amplitude) ** 2
        theta = 2 * np.arccos(np.sqrt(prob_0))
        phi = np.angle(amplitude)

        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        return x, y, z

    @staticmethod
    def density_matrix(state_vector: np.ndarray) -> np.ndarray:
        """Compute density matrix from state vector"""
        return np.outer(state_vector, state_vector.conj())

    @staticmethod
    def von_neumann_entropy(density_matrix: np.ndarray) -> float:
        """Compute von Neumann entropy"""
        eigenvalues = np.linalg.eigvalsh(density_matrix)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]  # Remove zeros
        return -np.sum(eigenvalues * np.log2(eigenvalues))

    @staticmethod
    def entanglement_entropy(bipartition: Tuple[np.ndarray, np.ndarray]) -> float:
        """Compute entanglement entropy for bipartition"""
        # Compute reduced density matrix
        full_state = np.kron(bipartition[0], bipartition[1])
        density = QuantumStateVisualizer.density_matrix(full_state)

        # Partial trace over second subsystem
        dim_a = len(bipartition[0])
        dim_b = len(bipartition[1])

        reduced = np.zeros((dim_a, dim_a), dtype=complex)
        for i in range(dim_a):
            for j in range(dim_a):
                for k in range(dim_b):
                    idx_ik = i * dim_b + k
                    idx_jk = j * dim_b + k
                    reduced[i, j] += density[idx_ik, idx_jk]

        return QuantumStateVisualizer.von_neumann_entropy(reduced)


class QuantumGradientEstimator:
    """Estimate gradients for quantum circuits"""

    @staticmethod
    def parameter_shift(
        circuit_fn: Callable[[np.ndarray], float],
        params: np.ndarray,
        shift: float = np.pi / 2
    ) -> np.ndarray:
        """
        Compute gradient using parameter shift rule
        ∂f/∂θ = (f(θ + s) - f(θ - s)) / (2 sin(s))
        """
        gradients = np.zeros_like(params)

        for i in range(len(params)):
            params_plus = params.copy()
            params_plus[i] += shift

            params_minus = params.copy()
            params_minus[i] -= shift

            f_plus = circuit_fn(params_plus)
            f_minus = circuit_fn(params_minus)

            gradients[i] = (f_plus - f_minus) / (2 * np.sin(shift))

        return gradients

    @staticmethod
    def finite_difference(
        circuit_fn: Callable[[np.ndarray], float],
        params: np.ndarray,
        epsilon: float = 1e-5
    ) -> np.ndarray:
        """Compute gradient using finite differences"""
        gradients = np.zeros_like(params)
        f_original = circuit_fn(params)

        for i in range(len(params)):
            params_eps = params.copy()
            params_eps[i] += epsilon

            f_eps = circuit_fn(params_eps)
            gradients[i] = (f_eps - f_original) / epsilon

        return gradients

    @staticmethod
    def spsa_gradient(
        circuit_fn: Callable[[np.ndarray], float],
        params: np.ndarray,
        perturbation: float = 0.1
    ) -> np.ndarray:
        """
        Simultaneous Perturbation Stochastic Approximation
        More efficient for high-dimensional parameter spaces
        """
        # Random perturbation direction
        delta = np.random.choice([-1, 1], size=len(params)) * perturbation

        # Evaluate at perturbed points
        params_plus = params + delta
        params_minus = params - delta

        f_plus = circuit_fn(params_plus)
        f_minus = circuit_fn(params_minus)

        # Gradient estimate
        gradient = (f_plus - f_minus) / (2 * delta)

        return gradient


class QuantumOptimizer:
    """Optimization algorithms for quantum circuits"""

    def __init__(
        self,
        learning_rate: float = 0.01,
        momentum: float = 0.9,
        optimizer: str = 'adam'
    ):
        self.lr = learning_rate
        self.momentum = momentum
        self.optimizer = optimizer

        # Adam state
        self.m = None
        self.v = None
        self.t = 0
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.epsilon = 1e-8

    def step(self, params: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        """Single optimization step"""
        if self.optimizer == 'sgd':
            return params - self.lr * gradient

        elif self.optimizer == 'momentum':
            if self.m is None:
                self.m = np.zeros_like(params)
            self.m = self.momentum * self.m + gradient
            return params - self.lr * self.m

        elif self.optimizer == 'adam':
            if self.m is None:
                self.m = np.zeros_like(params)
                self.v = np.zeros_like(params)

            self.t += 1
            self.m = self.beta1 * self.m + (1 - self.beta1) * gradient
            self.v = self.beta2 * self.v + (1 - self.beta2) * (gradient ** 2)

            m_hat = self.m / (1 - self.beta1 ** self.t)
            v_hat = self.v / (1 - self.beta2 ** self.t)

            return params - self.lr * m_hat / (np.sqrt(v_hat) + self.epsilon)

        else:
            raise ValueError(f"Unknown optimizer: {self.optimizer}")

    def reset(self):
        """Reset optimizer state"""
        self.m = None
        self.v = None
        self.t = 0


class QuantumMetrics:
    """Metrics for quantum systems"""

    @staticmethod
    def fidelity(state1: np.ndarray, state2: np.ndarray) -> float:
        """Compute fidelity between two quantum states"""
        overlap = np.abs(np.vdot(state1, state2)) ** 2
        return overlap

    @staticmethod
    def trace_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
        """Compute trace distance between density matrices"""
        diff = rho1 - rho2
        eigenvalues = np.linalg.eigvalsh(diff)
        return 0.5 * np.sum(np.abs(eigenvalues))

    @staticmethod
    def quantum_fisher_information(
        state_fn: Callable[[float], np.ndarray],
        theta: float,
        epsilon: float = 1e-5
    ) -> float:
        """
        Compute quantum Fisher information
        Measures sensitivity of state to parameter changes
        """
        state = state_fn(theta)
        state_plus = state_fn(theta + epsilon)
        state_minus = state_fn(theta - epsilon)

        # Symmetric logarithmic derivative (approximation)
        sld = (state_plus - state_minus) / (2 * epsilon)

        # QFI = Tr[ρ L^2]
        qfi = 4 * np.vdot(sld, sld) - 4 * np.abs(np.vdot(state, sld)) ** 2

        return qfi

    @staticmethod
    def quantum_volume(n_qubits: int, circuit_depth: int) -> float:
        """
        Compute quantum volume metric
        Measures effective number of qubits and gates
        """
        return 2 ** min(n_qubits, circuit_depth)


class QuantumErrorMitigation:
    """Error mitigation techniques"""

    @staticmethod
    def zero_noise_extrapolation(
        circuit_fn: Callable[[float], float],
        scale_factors: List[float]
    ) -> float:
        """
        Zero-noise extrapolation
        Extrapolate to zero noise by scaling noise and fitting
        """
        results = [circuit_fn(scale) for scale in scale_factors]

        # Linear extrapolation to scale = 0
        # Fit: f(scale) = a + b * scale
        A = np.vstack([scale_factors, np.ones(len(scale_factors))]).T
        b, a = np.linalg.lstsq(A, results, rcond=None)[0]

        return a  # Value at scale = 0

    @staticmethod
    def measurement_mitigation(
        counts: dict,
        calibration_matrix: np.ndarray
    ) -> dict:
        """
        Mitigate measurement errors using calibration matrix
        """
        # Convert counts to probability vector
        n_states = len(calibration_matrix)
        probs = np.zeros(n_states)

        for state, count in counts.items():
            idx = int(state, 2) if isinstance(state, str) else state
            probs[idx] = count

        probs = probs / np.sum(probs)

        # Apply inverse calibration matrix
        mitigated_probs = np.linalg.inv(calibration_matrix) @ probs
        mitigated_probs = np.clip(mitigated_probs, 0, 1)
        mitigated_probs = mitigated_probs / np.sum(mitigated_probs)

        # Convert back to counts
        mitigated_counts = {}
        for i, prob in enumerate(mitigated_probs):
            if prob > 0:
                mitigated_counts[format(i, f'0{int(np.log2(n_states))}b')] = prob

        return mitigated_counts

    @staticmethod
    def probabilistic_error_cancellation(
        circuit_fn: Callable[[], float],
        mitigation_prob: float,
        num_shots: int = 1000
    ) -> float:
        """
        Probabilistic error cancellation
        """
        results = []

        for _ in range(num_shots):
            if np.random.random() < mitigation_prob:
                # Apply mitigation
                result = -circuit_fn()  # Negative for cancellation
            else:
                result = circuit_fn()
            results.append(result)

        return np.mean(results) / mitigation_prob


# Utility functions
def tensor_product(states: List[np.ndarray]) -> np.ndarray:
    """Compute tensor product of multiple states"""
    result = states[0]
    for state in states[1:]:
        result = np.kron(result, state)
    return result


def partial_trace(
    density_matrix: np.ndarray,
    dims: List[int],
    trace_over: List[int]
) -> np.ndarray:
    """
    Compute partial trace of density matrix

    Args:
        density_matrix: Full density matrix
        dims: Dimensions of subsystems
        trace_over: Indices of subsystems to trace over
    """
    n_subsystems = len(dims)
    total_dim = np.prod(dims)

    # Reshape to tensor
    shape = dims + dims
    tensor = density_matrix.reshape(shape)

    # Trace over specified subsystems
    for idx in sorted(trace_over, reverse=True):
        tensor = np.trace(tensor, axis1=idx, axis2=idx + n_subsystems)

    # Reshape back to matrix
    remaining_dims = [dims[i] for i in range(n_subsystems) if i not in trace_over]
    new_dim = np.prod(remaining_dims)

    return tensor.reshape((new_dim, new_dim))


def schmidt_decomposition(
    state: np.ndarray,
    dim_a: int,
    dim_b: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Schmidt decomposition of bipartite state
    Returns (singular_values, basis_a, basis_b)
    """
    # Reshape to matrix
    matrix = state.reshape((dim_a, dim_b))

    # SVD
    U, S, Vh = np.linalg.svd(matrix, full_matrices=False)

    return S, U, Vh.T.conj()


def entanglement_entropy_schmidt(singular_values: np.ndarray) -> float:
    """Compute entanglement entropy from Schmidt coefficients"""
    probs = singular_values ** 2
    probs = probs[probs > 1e-10]
    return -np.sum(probs * np.log2(probs))


if __name__ == "__main__":
    # Test utilities
    encoder = QuantumStateEncoder()
    data = np.array([0.5, -0.3, 0.8, -0.2])

    angles = encoder.angle_encoding(data)
    print(f"Angle encoding: {angles}")

    amplitudes = encoder.amplitude_encoding(data)
    print(f"Amplitude encoding: {amplitudes}")

    # Test circuit builder
    builder = QuantumCircuitBuilder(4)
    params = np.random.randn(12)
    builder.build_variational_layer(params)
    qsharp_code = builder.to_qsharp()
    print(f"\nGenerated Q# code:\n{qsharp_code}")

    # Test metrics
    state1 = np.array([1, 0]) / np.sqrt(2)
    state2 = np.array([0, 1]) / np.sqrt(2)
    fidelity = QuantumMetrics.fidelity(state1, state2)
    print(f"\nFidelity: {fidelity}")
