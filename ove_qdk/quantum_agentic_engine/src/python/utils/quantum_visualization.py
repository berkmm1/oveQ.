#!/usr/bin/env python3
"""
Quantum Visualization Module
Visualization tools for quantum states and circuits
Part of the Quantum Agentic Loop Engine
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BlochVector:
    """Bloch sphere vector representation"""
    x: float
    y: float
    z: float

    def to_cartesian(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_spherical(self) -> Tuple[float, float, float]:
        """Convert to spherical coordinates (r, theta, phi)"""
        r = np.sqrt(self.x**2 + self.y**2 + self.z**2)
        theta = np.arccos(self.z / (r + 1e-10))
        phi = np.arctan2(self.y, self.x)
        return (r, theta, phi)

    def normalize(self) -> 'BlochVector':
        """Normalize to unit sphere"""
        norm = np.sqrt(self.x**2 + self.y**2 + self.z**2)
        if norm > 0:
            return BlochVector(self.x/norm, self.y/norm, self.z/norm)
        return BlochVector(0, 0, 1)


class QuantumStateVisualizer:
    """Visualize quantum states"""

    def __init__(self, num_qubits: int = 1):
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits

    def state_to_bloch(self, state_vector: np.ndarray) -> List[BlochVector]:
        """Convert multi-qubit state to Bloch vectors"""
        bloch_vectors = []

        for qubit_idx in range(self.num_qubits):
            # Compute reduced density matrix
            rho = self._compute_reduced_density_matrix(state_vector, qubit_idx)

            # Compute Bloch vector components
            sx = np.array([[0, 1], [1, 0]])
            sy = np.array([[0, -1j], [1j, 0]])
            sz = np.array([[1, 0], [0, -1]])

            x = np.real(np.trace(rho @ sx))
            y = np.real(np.trace(rho @ sy))
            z = np.real(np.trace(rho @ sz))

            bloch_vectors.append(BlochVector(x, y, z))

        return bloch_vectors

    def _compute_reduced_density_matrix(self, state_vector: np.ndarray,
                                        qubit_idx: int) -> np.ndarray:
        """Compute reduced density matrix for a qubit"""
        # Reshape state vector
        state_tensor = state_vector.reshape([2] * self.num_qubits)

        # Trace out all other qubits
        axes = list(range(self.num_qubits))
        axes.remove(qubit_idx)

        # Compute density matrix
        rho = np.outer(state_vector, state_vector.conj())
        rho_tensor = rho.reshape([2] * (2 * self.num_qubits))

        # Partial trace (simplified)
        reduced_rho = np.zeros((2, 2), dtype=complex)
        for i in range(2):
            for j in range(2):
                # Sum over other qubit states
                for other_state in range(2 ** (self.num_qubits - 1)):
                    idx1 = i * (2 ** (self.num_qubits - 1)) + other_state
                    idx2 = j * (2 ** (self.num_qubits - 1)) + other_state
                    if idx1 < len(state_vector) and idx2 < len(state_vector):
                        reduced_rho[i, j] += state_vector[idx1] * state_vector[idx2].conj()

        return reduced_rho

    def compute_amplitudes(self, state_vector: np.ndarray) -> Dict[str, complex]:
        """Compute amplitudes for each basis state"""
        amplitudes = {}

        for i, amp in enumerate(state_vector):
            basis_state = format(i, f'0{self.num_qubits}b')
            amplitudes[basis_state] = amp

        return amplitudes

    def compute_probabilities(self, state_vector: np.ndarray) -> Dict[str, float]:
        """Compute probabilities for each basis state"""
        amplitudes = self.compute_amplitudes(state_vector)
        return {state: np.abs(amp)**2 for state, amp in amplitudes.items()}

    def compute_entropy(self, state_vector: np.ndarray) -> float:
        """Compute von Neumann entropy"""
        probabilities = self.compute_probabilities(state_vector)

        entropy = 0.0
        for prob in probabilities.values():
            if prob > 1e-10:
                entropy -= prob * np.log2(prob)

        return entropy

    def compute_concurrence(self, state_vector: np.ndarray) -> float:
        """Compute concurrence for two-qubit states"""
        if self.num_qubits != 2:
            return 0.0

        # Reshape to matrix
        psi_matrix = state_vector.reshape(2, 2)

        # Spin-flipped state
        sy = np.array([[0, -1j], [1j, 0]])
        psi_tilde = sy @ psi_matrix @ sy

        # Singular values
        R = psi_matrix @ psi_tilde.conj().T
        eigenvalues = np.linalg.eigvalsh(R)
        eigenvalues = np.sort(eigenvalues)[::-1]

        concurrence = max(0, np.sqrt(eigenvalues[0]) - np.sqrt(eigenvalues[1]) -
                         np.sqrt(eigenvalues[2]) - np.sqrt(eigenvalues[3]))

        return concurrence

    def compute_entanglement_spectrum(self, state_vector: np.ndarray) -> List[float]:
        """Compute entanglement spectrum"""
        # Reshape for bipartition
        half_qubits = self.num_qubits // 2
        dim_a = 2 ** half_qubits
        dim_b = 2 ** (self.num_qubits - half_qubits)

        # Reshape state vector to matrix
        psi_matrix = state_vector.reshape(dim_a, dim_b)

        # SVD
        u, s, vh = np.linalg.svd(psi_matrix, full_matrices=False)

        # Entanglement spectrum is squared singular values
        spectrum = s ** 2

        return spectrum.tolist()

    def compute_mutual_information(self, state_vector: np.ndarray,
                                   qubit_a: int, qubit_b: int) -> float:
        """Compute mutual information between two qubits"""
        # Reduced density matrices
        rho_a = self._compute_reduced_density_matrix(state_vector, qubit_a)
        rho_b = self._compute_reduced_density_matrix(state_vector, qubit_b)

        # Two-qubit reduced density matrix
        rho_ab = self._compute_two_qubit_density_matrix(state_vector, qubit_a, qubit_b)

        # Entropies
        s_a = self._von_neumann_entropy(rho_a)
        s_b = self._von_neumann_entropy(rho_b)
        s_ab = self._von_neumann_entropy(rho_ab)

        # Mutual information
        return s_a + s_b - s_ab

    def _compute_two_qubit_density_matrix(self, state_vector: np.ndarray,
                                          qubit_a: int, qubit_b: int) -> np.ndarray:
        """Compute two-qubit reduced density matrix"""
        # Simplified implementation
        rho = np.zeros((4, 4), dtype=complex)

        for i in range(4):
            for j in range(4):
                # Trace over other qubits
                for other_state in range(2 ** (self.num_qubits - 2)):
                    idx1 = self._combine_indices(i, other_state, qubit_a, qubit_b)
                    idx2 = self._combine_indices(j, other_state, qubit_a, qubit_b)
                    if idx1 < len(state_vector) and idx2 < len(state_vector):
                        rho[i, j] += state_vector[idx1] * state_vector[idx2].conj()

        return rho

    def _combine_indices(self, two_qubit_state: int, other_state: int,
                        qubit_a: int, qubit_b: int) -> int:
        """Combine indices for partial trace"""
        bit_a = (two_qubit_state >> 0) & 1
        bit_b = (two_qubit_state >> 1) & 1

        idx = 0
        other_idx = 0

        for q in range(self.num_qubits):
            if q == qubit_a:
                idx |= (bit_a << q)
            elif q == qubit_b:
                idx |= (bit_b << q)
            else:
                idx |= (((other_state >> other_idx) & 1) << q)
                other_idx += 1

        return idx

    def _von_neumann_entropy(self, rho: np.ndarray) -> float:
        """Compute von Neumann entropy of density matrix"""
        eigenvalues = np.linalg.eigvalsh(rho)

        entropy = 0.0
        for ev in eigenvalues:
            if ev > 1e-10:
                entropy -= ev * np.log2(ev)

        return entropy


class CircuitVisualizer:
    """Visualize quantum circuits"""

    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.gates = []

    def add_gate(self, gate_type: str, qubits: List[int], params: Optional[List[float]] = None):
        """Add a gate to the circuit"""
        self.gates.append({
            'type': gate_type,
            'qubits': qubits,
            'params': params or []
        })

    def to_ascii(self) -> str:
        """Generate ASCII circuit diagram"""
        lines = [''] * self.num_qubits

        for gate in self.gates:
            gate_type = gate['type']
            qubits = gate['qubits']

            if len(qubits) == 1:
                # Single-qubit gate
                q = qubits[0]
                for i in range(self.num_qubits):
                    if i == q:
                        lines[i] += f'─[{gate_type}]─'
                    else:
                        lines[i] += '──────'

            elif len(qubits) == 2:
                # Two-qubit gate
                control, target = qubits
                min_q = min(control, target)
                max_q = max(control, target)

                for i in range(self.num_qubits):
                    if i == control:
                        lines[i] += '─[●]──'
                    elif i == target:
                        lines[i] += f'─[{gate_type}]─'
                    elif min_q < i < max_q:
                        lines[i] += '──│───'
                    else:
                        lines[i] += '──────'

        # Add qubit labels
        labeled_lines = []
        for i, line in enumerate(lines):
            labeled_lines.append(f'q{i}: {line}')

        return '\n'.join(labeled_lines)

    def get_depth(self) -> int:
        """Compute circuit depth"""
        return len(self.gates)

    def get_gate_count(self) -> Dict[str, int]:
        """Count gates by type"""
        counts = {}
        for gate in self.gates:
            gate_type = gate['type']
            counts[gate_type] = counts.get(gate_type, 0) + 1
        return counts

    def estimate_error(self, error_rate: float = 0.001) -> float:
        """Estimate total circuit error"""
        num_gates = len(self.gates)
        # Simple error model
        return 1 - (1 - error_rate) ** num_gates


class TrainingVisualizer:
    """Visualize training progress"""

    def __init__(self):
        self.metrics_history = {
            'rewards': [],
            'losses': [],
            'episode_lengths': [],
            'learning_rates': [],
            'entropies': []
        }

    def update(self, metrics: Dict[str, float]):
        """Update with new metrics"""
        for key, value in metrics.items():
            if key in self.metrics_history:
                self.metrics_history[key].append(value)

    def get_moving_average(self, metric: str, window: int = 100) -> List[float]:
        """Get moving average of a metric"""
        if metric not in self.metrics_history:
            return []

        data = self.metrics_history[metric]
        if len(data) < window:
            return data

        averages = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            avg = np.mean(data[start:i+1])
            averages.append(avg)

        return averages

    def get_statistics(self, metric: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        if metric not in self.metrics_history:
            return {}

        data = self.metrics_history[metric]
        if not data:
            return {}

        return {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'last': data[-1] if data else 0
        }

    def detect_convergence(self, metric: str, window: int = 50,
                          threshold: float = 0.01) -> bool:
        """Detect if training has converged"""
        if metric not in self.metrics_history:
            return False

        data = self.metrics_history[metric]
        if len(data) < 2 * window:
            return False

        recent_std = np.std(data[-window:])
        return recent_std < threshold


class EntanglementVisualizer:
    """Visualize entanglement structure"""

    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits

    def compute_entanglement_graph(self, state_vector: np.ndarray) -> np.ndarray:
        """Compute entanglement graph adjacency matrix"""
        adjacency = np.zeros((self.num_qubits, self.num_qubits))

        visualizer = QuantumStateVisualizer(self.num_qubits)

        for i in range(self.num_qubits):
            for j in range(i + 1, self.num_qubits):
                # Compute mutual information as edge weight
                mi = visualizer.compute_mutual_information(state_vector, i, j)
                adjacency[i, j] = mi
                adjacency[j, i] = mi

        return adjacency

    def find_entangled_clusters(self, state_vector: np.ndarray,
                                threshold: float = 0.1) -> List[List[int]]:
        """Find clusters of entangled qubits"""
        adjacency = self.compute_entanglement_graph(state_vector)

        # Simple clustering: connected components
        visited = [False] * self.num_qubits
        clusters = []

        for i in range(self.num_qubits):
            if not visited[i]:
                cluster = []
                stack = [i]

                while stack:
                    q = stack.pop()
                    if not visited[q]:
                        visited[q] = True
                        cluster.append(q)

                        for j in range(self.num_qubits):
                            if not visited[j] and adjacency[q, j] > threshold:
                                stack.append(j)

                if cluster:
                    clusters.append(cluster)

        return clusters

    def compute_entanglement_entropy_profile(self, state_vector: np.ndarray) -> List[float]:
        """Compute entanglement entropy for each bipartition"""
        entropies = []

        visualizer = QuantumStateVisualizer(self.num_qubits)

        for k in range(1, self.num_qubits):
            # Bipartition into k and n-k qubits
            # Compute entropy of reduced density matrix
            spectrum = visualizer.compute_entanglement_spectrum(state_vector)

            entropy = 0.0
            for p in spectrum[:2**k]:
                if p > 1e-10:
                    entropy -= p * np.log2(p)

            entropies.append(entropy)

        return entropies


# Utility functions
def visualize_state(state_vector: np.ndarray, title: str = "Quantum State") -> str:
    """Create text visualization of quantum state"""
    num_qubits = int(np.log2(len(state_vector)))
    visualizer = QuantumStateVisualizer(num_qubits)

    output = f"\n{title}\n"
    output += "=" * 40 + "\n"

    # Probabilities
    probs = visualizer.compute_probabilities(state_vector)
    output += "\nProbabilities:\n"
    for state, prob in sorted(probs.items(), key=lambda x: -x[1])[:8]:
        bar = "█" * int(prob * 50)
        output += f"|{state}⟩: {prob:.4f} {bar}\n"

    # Entropy
    entropy = visualizer.compute_entropy(state_vector)
    output += f"\nEntropy: {entropy:.4f}\n"

    # Bloch vectors for single qubits
    if num_qubits <= 4:
        bloch_vectors = visualizer.state_to_bloch(state_vector)
        output += "\nBloch Vectors:\n"
        for i, bv in enumerate(bloch_vectors):
            output += f"Qubit {i}: ({bv.x:.3f}, {bv.y:.3f}, {bv.z:.3f})\n"

    return output


def print_circuit(circuit_gates: List[Dict[str, Any]], num_qubits: int):
    """Print circuit diagram"""
    visualizer = CircuitVisualizer(num_qubits)

    for gate in circuit_gates:
        visualizer.add_gate(
            gate['type'],
            gate['qubits'],
            gate.get('params')
        )

    print(visualizer.to_ascii())
    print(f"\nDepth: {visualizer.get_depth()}")
    print(f"Gate counts: {visualizer.get_gate_count()}")


if __name__ == "__main__":
    print("Quantum Visualization Module")
    print("=" * 40)

    # Test state visualization
    num_qubits = 3
    dim = 2 ** num_qubits

    # Create Bell-like state
    state = np.zeros(dim)
    state[0] = 1/np.sqrt(2)
    state[dim-1] = 1/np.sqrt(2)

    print(visualize_state(state, "Bell State"))

    # Test circuit visualization
    gates = [
        {'type': 'H', 'qubits': [0]},
        {'type': 'CNOT', 'qubits': [0, 1]},
        {'type': 'X', 'qubits': [2]},
        {'type': 'CNOT', 'qubits': [1, 2]}
    ]

    print("\nCircuit Diagram:")
    print_circuit(gates, 3)
