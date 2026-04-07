#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Quantum Metrics and Analysis
Comprehensive metrics for quantum algorithm performance analysis
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of quantum metrics"""
    FIDELITY = auto()
    ENTANGLEMENT = auto()
    COHERENCE = auto()
    GATE_COUNT = auto()
    CIRCUIT_DEPTH = auto()
    ERROR_RATE = auto()
    EXECUTION_TIME = auto()
    QUBIT_UTILIZATION = auto()
    PARALLELISM = auto()


@dataclass
class QuantumMetrics:
    """Collection of quantum metrics"""
    # Fidelity metrics
    state_fidelity: float = 0.0
    process_fidelity: float = 0.0
    gate_fidelity: float = 0.0
    measurement_fidelity: float = 0.0

    # Entanglement metrics
    entanglement_entropy: float = 0.0
    concurrence: float = 0.0
    negativity: float = 0.0
    mutual_information: float = 0.0

    # Coherence metrics
    t1_time: float = 0.0
    t2_time: float = 0.0
    coherence_time: float = 0.0
    dephasing_rate: float = 0.0

    # Circuit metrics
    num_qubits: int = 0
    num_gates: int = 0
    circuit_depth: int = 0
    num_parameters: int = 0
    num_two_qubit_gates: int = 0

    # Performance metrics
    execution_time_ms: float = 0.0
    compilation_time_ms: float = 0.0
    optimization_time_ms: float = 0.0

    # Error metrics
    error_rate: float = 0.0
    success_probability: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'fidelity': {
                'state': self.state_fidelity,
                'process': self.process_fidelity,
                'gate': self.gate_fidelity,
                'measurement': self.measurement_fidelity
            },
            'entanglement': {
                'entropy': self.entanglement_entropy,
                'concurrence': self.concurrence,
                'negativity': self.negativity,
                'mutual_information': self.mutual_information
            },
            'coherence': {
                't1': self.t1_time,
                't2': self.t2_time,
                'coherence_time': self.coherence_time,
                'dephasing_rate': self.dephasing_rate
            },
            'circuit': {
                'num_qubits': self.num_qubits,
                'num_gates': self.num_gates,
                'depth': self.circuit_depth,
                'num_parameters': self.num_parameters,
                'num_two_qubit_gates': self.num_two_qubit_gates
            },
            'performance': {
                'execution_time_ms': self.execution_time_ms,
                'compilation_time_ms': self.compilation_time_ms,
                'optimization_time_ms': self.optimization_time_ms
            },
            'error': {
                'rate': self.error_rate,
                'success_probability': self.success_probability,
                'confidence_interval': self.confidence_interval
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuantumMetrics':
        """Create metrics from dictionary"""
        return cls(
            state_fidelity=data.get('fidelity', {}).get('state', 0.0),
            process_fidelity=data.get('fidelity', {}).get('process', 0.0),
            gate_fidelity=data.get('fidelity', {}).get('gate', 0.0),
            measurement_fidelity=data.get('fidelity', {}).get('measurement', 0.0),
            entanglement_entropy=data.get('entanglement', {}).get('entropy', 0.0),
            concurrence=data.get('entanglement', {}).get('concurrence', 0.0),
            negativity=data.get('entanglement', {}).get('negativity', 0.0),
            mutual_information=data.get('entanglement', {}).get('mutual_information', 0.0),
            t1_time=data.get('coherence', {}).get('t1', 0.0),
            t2_time=data.get('coherence', {}).get('t2', 0.0),
            coherence_time=data.get('coherence', {}).get('coherence_time', 0.0),
            dephasing_rate=data.get('coherence', {}).get('dephasing_rate', 0.0),
            num_qubits=data.get('circuit', {}).get('num_qubits', 0),
            num_gates=data.get('circuit', {}).get('num_gates', 0),
            circuit_depth=data.get('circuit', {}).get('depth', 0),
            num_parameters=data.get('circuit', {}).get('num_parameters', 0),
            num_two_qubit_gates=data.get('circuit', {}).get('num_two_qubit_gates', 0),
            execution_time_ms=data.get('performance', {}).get('execution_time_ms', 0.0),
            compilation_time_ms=data.get('performance', {}).get('compilation_time_ms', 0.0),
            optimization_time_ms=data.get('performance', {}).get('optimization_time_ms', 0.0),
            error_rate=data.get('error', {}).get('rate', 0.0),
            success_probability=data.get('error', {}).get('success_probability', 0.0),
            confidence_interval=tuple(data.get('error', {}).get('confidence_interval', [0.0, 0.0]))
        )


class FidelityAnalyzer:
    """Analyze quantum state and process fidelity"""

    @staticmethod
    def state_fidelity(state1: np.ndarray, state2: np.ndarray) -> float:
        """
        Calculate fidelity between two quantum states

        For pure states: |<ψ|φ>|²
        For mixed states: Tr[√(√ρ σ √ρ)]²
        """
        if state1.ndim == 1 and state2.ndim == 1:
            # Both pure states
            return np.abs(np.vdot(state1, state2)) ** 2
        elif state1.ndim == 2 and state2.ndim == 2:
            # Both density matrices
            sqrt_rho1 = FidelityAnalyzer._matrix_sqrt(state1)
            fidelity_matrix = sqrt_rho1 @ state2 @ sqrt_rho1
            return np.real(np.trace(FidelityAnalyzer._matrix_sqrt(fidelity_matrix))) ** 2
        elif state1.ndim == 1 and state2.ndim == 2:
            # state1 pure, state2 mixed
            return np.real(np.vdot(state1, state2 @ state1))
        elif state1.ndim == 2 and state2.ndim == 1:
            # state1 mixed, state2 pure
            return np.real(np.vdot(state2, state1 @ state2))
        else:
            raise ValueError("Invalid state dimensions")

    @staticmethod
    def _matrix_sqrt(matrix: np.ndarray) -> np.ndarray:
        """Compute matrix square root"""
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        sqrt_eigenvalues = np.sqrt(np.maximum(eigenvalues, 0))
        return eigenvectors @ np.diag(sqrt_eigenvalues) @ eigenvectors.conj().T

    @staticmethod
    def process_fidelity(
        process_matrix1: np.ndarray,
        process_matrix2: np.ndarray
    ) -> float:
        """Calculate fidelity between two quantum processes"""
        # Process fidelity using Choi matrices
        dim = process_matrix1.shape[0]

        # Normalize
        process_matrix1 = process_matrix1 / np.trace(process_matrix1)
        process_matrix2 = process_matrix2 / np.trace(process_matrix2)

        # Fidelity
        return np.real(np.trace(process_matrix1 @ process_matrix2))

    @staticmethod
    def average_gate_fidelity(
        ideal_gate: np.ndarray,
        noisy_gate: np.ndarray,
        num_samples: int = 1000
    ) -> float:
        """Calculate average gate fidelity"""
        dim = ideal_gate.shape[0]
        fidelities = []

        for _ in range(num_samples):
            # Random input state
            random_state = np.random.randn(dim) + 1j * np.random.randn(dim)
            random_state = random_state / np.linalg.norm(random_state)

            # Apply gates
            ideal_output = ideal_gate @ random_state
            noisy_output = noisy_gate @ random_state

            # Calculate fidelity
            fid = np.abs(np.vdot(ideal_output, noisy_output)) ** 2
            fidelities.append(fid)

        return np.mean(fidelities)

    @staticmethod
    def diamond_norm(process_matrix1: np.ndarray, process_matrix2: np.ndarray) -> float:
        """Calculate diamond norm distance between processes"""
        # Simplified diamond norm calculation
        diff = process_matrix1 - process_matrix2
        return np.linalg.norm(diff, ord='nuc')


class EntanglementAnalyzer:
    """Analyze quantum entanglement"""

    @staticmethod
    def von_neumann_entropy(density_matrix: np.ndarray) -> float:
        """Calculate von Neumann entropy"""
        eigenvalues = np.linalg.eigvalsh(density_matrix)

        entropy = 0.0
        for ev in eigenvalues:
            if ev > 1e-10:
                entropy -= ev * np.log2(ev)

        return entropy

    @staticmethod
    def bipartite_entropy(
        state: np.ndarray,
        subsystem_a: List[int],
        subsystem_b: List[int]
    ) -> float:
        """Calculate entanglement entropy between two subsystems"""
        # Trace out subsystem B to get reduced density matrix
        rho_a = EntanglementAnalyzer._partial_trace(state, subsystem_b)

        return EntanglementAnalyzer.von_neumann_entropy(rho_a)

    @staticmethod
    def _partial_trace(
        state: np.ndarray,
        indices_to_trace: List[int]
    ) -> np.ndarray:
        """Partial trace over specified indices"""
        if state.ndim == 1:
            # Pure state
            dim = int(np.log2(len(state)))
            density_matrix = np.outer(state, state.conj())
        else:
            # Density matrix
            dim = int(np.log2(state.shape[0]))
            density_matrix = state

        # Reshape for tracing
        shape = [2] * (2 * dim)
        reshaped = density_matrix.reshape(shape)

        # Trace out indices
        axes = [i for i in range(dim) if i in indices_to_trace]
        axes += [i + dim for i in indices_to_trace]

        reduced = np.trace(reshaped, axis1=axes[0], axis2=axes[1])

        return reduced.reshape(2 ** (dim - len(indices_to_trace)), -1)

    @staticmethod
    def concurrence(state: np.ndarray) -> float:
        """Calculate concurrence for 2-qubit state"""
        if len(state) != 4:
            raise ValueError("Concurrence only defined for 2-qubit states")

        # Spin-flipped state
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        spin_flip = np.kron(sigma_y, sigma_y)

        if state.ndim == 1:
            # Pure state
            tilde_state = spin_flip @ state.conj()
            conc = np.abs(np.vdot(state, tilde_state))
        else:
            # Mixed state
            rho_tilde = spin_flip @ state.conj() @ spin_flip

            # R matrix
            r_matrix = state @ rho_tilde
            eigenvalues = np.sort(np.linalg.eigvalsh(r_matrix))[::-1]

            conc = max(0, np.sqrt(eigenvalues[0]) - np.sqrt(eigenvalues[1])
                      - np.sqrt(eigenvalues[2]) - np.sqrt(eigenvalues[3]))

        return conc

    @staticmethod
    def negativity(state: np.ndarray) -> float:
        """Calculate negativity"""
        if state.ndim == 1:
            density_matrix = np.outer(state, state.conj())
        else:
            density_matrix = state

        # Partial transpose
        rho_pt = EntanglementAnalyzer._partial_transpose(density_matrix)

        # Negativity
        eigenvalues = np.linalg.eigvalsh(rho_pt)
        return np.sum(np.abs(eigenvalues[eigenvalues < 0]))

    @staticmethod
    def _partial_transpose(density_matrix: np.ndarray) -> np.ndarray:
        """Partial transpose of density matrix"""
        dim = int(np.sqrt(density_matrix.shape[0]))

        # Reshape and transpose
        reshaped = density_matrix.reshape([dim, dim, dim, dim])
        transposed = np.transpose(reshaped, (0, 3, 2, 1))

        return transposed.reshape(density_matrix.shape)

    @staticmethod
    def mutual_information(
        state: np.ndarray,
        subsystem_a: List[int],
        subsystem_b: List[int]
    ) -> float:
        """Calculate quantum mutual information"""
        # S(A:B) = S(A) + S(B) - S(AB)

        if state.ndim == 1:
            density_matrix = np.outer(state, state.conj())
        else:
            density_matrix = state

        s_ab = EntanglementAnalyzer.von_neumann_entropy(density_matrix)

        # Trace out to get subsystems
        rho_a = EntanglementAnalyzer._partial_trace(density_matrix, subsystem_b)
        rho_b = EntanglementAnalyzer._partial_trace(density_matrix, subsystem_a)

        s_a = EntanglementAnalyzer.von_neumann_entropy(rho_a)
        s_b = EntanglementAnalyzer.von_neumann_entropy(rho_b)

        return s_a + s_b - s_ab

    @staticmethod
    def entanglement_spectrum(state: np.ndarray) -> np.ndarray:
        """Calculate entanglement spectrum"""
        if state.ndim == 1:
            density_matrix = np.outer(state, state.conj())
        else:
            density_matrix = state

        # Schmidt decomposition
        dim = int(np.sqrt(len(state))) if state.ndim == 1 else int(np.sqrt(state.shape[0]))

        if state.ndim == 1:
            reshaped = state.reshape(dim, dim)
            u, s, vh = np.linalg.svd(reshaped)
            return s ** 2
        else:
            eigenvalues = np.linalg.eigvalsh(density_matrix)
            return eigenvalues[eigenvalues > 1e-10]


class CircuitAnalyzer:
    """Analyze quantum circuit properties"""

    @staticmethod
    def circuit_depth(gates: List[Any]) -> int:
        """Calculate circuit depth"""
        # Simplified depth calculation
        # In practice, would need to account for gate dependencies
        return len(gates)

    @staticmethod
    def gate_count(gates: List[Any]) -> Dict[str, int]:
        """Count gates by type"""
        counts = defaultdict(int)

        for gate in gates:
            gate_type = getattr(gate, 'gate_type', 'unknown')
            counts[str(gate_type)] += 1

        return dict(counts)

    @staticmethod
    def two_qubit_gate_count(gates: List[Any]) -> int:
        """Count two-qubit gates"""
        count = 0

        for gate in gates:
            num_targets = len(getattr(gate, 'targets', []))
            num_controls = len(getattr(gate, 'controls', []))

            if num_targets + num_controls > 1:
                count += 1

        return count

    @staticmethod
    def qubit_utilization(gates: List[Any], num_qubits: int) -> Dict[int, int]:
        """Calculate qubit utilization"""
        utilization = defaultdict(int)

        for gate in gates:
            targets = getattr(gate, 'targets', [])
            controls = getattr(gate, 'controls', [])

            for qubit in targets + controls:
                utilization[qubit] += 1

        return dict(utilization)

    @staticmethod
    def circuit_parallelism(gates: List[Any], num_qubits: int) -> float:
        """Calculate circuit parallelism"""
        if not gates:
            return 0.0

        # Count unique qubits used
        used_qubits = set()

        for gate in gates:
            targets = getattr(gate, 'targets', [])
            controls = getattr(gate, 'controls', [])
            used_qubits.update(targets)
            used_qubits.update(controls)

        return len(used_qubits) / num_qubits

    @staticmethod
    def critical_path_length(gates: List[Any]) -> int:
        """Calculate critical path length"""
        # Simplified: assume all gates on critical path
        return CircuitAnalyzer.circuit_depth(gates)


class PerformanceAnalyzer:
    """Analyze quantum algorithm performance"""

    def __init__(self):
        self.execution_times: List[float] = []
        self.success_rates: List[float] = []
        self.error_rates: List[float] = []

    def record_execution(self, execution_time: float, success: bool):
        """Record execution result"""
        self.execution_times.append(execution_time)
        self.success_rates.append(1.0 if success else 0.0)

    def get_average_execution_time(self) -> float:
        """Get average execution time"""
        return np.mean(self.execution_times) if self.execution_times else 0.0

    def get_success_rate(self) -> float:
        """Get overall success rate"""
        return np.mean(self.success_rates) if self.success_rates else 0.0

    def get_statistics(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.execution_times:
            return {}

        return {
            'mean_execution_time': np.mean(self.execution_times),
            'std_execution_time': np.std(self.execution_times),
            'min_execution_time': np.min(self.execution_times),
            'max_execution_time': np.max(self.execution_times),
            'success_rate': self.get_success_rate(),
            'total_executions': len(self.execution_times)
        }

    def confidence_interval(
        self,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for success rate"""
        if not self.success_rates:
            return (0.0, 0.0)

        n = len(self.success_rates)
        p = self.get_success_rate()

        # Wilson score interval
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%

        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2*n)) / denominator
        width = z * np.sqrt(p * (1-p) / n + z**2 / (4*n**2)) / denominator

        return (max(0, centre - width), min(1, centre + width))


class MetricsCollector:
    """Collect and aggregate quantum metrics"""

    def __init__(self):
        self.metrics_history: List[QuantumMetrics] = []
        self.fidelity_analyzer = FidelityAnalyzer()
        self.entanglement_analyzer = EntanglementAnalyzer()
        self.circuit_analyzer = CircuitAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()

    def collect_metrics(self, metrics: QuantumMetrics):
        """Collect metrics"""
        self.metrics_history.append(metrics)

    def get_average_metrics(self) -> QuantumMetrics:
        """Get average metrics over history"""
        if not self.metrics_history:
            return QuantumMetrics()

        n = len(self.metrics_history)

        return QuantumMetrics(
            state_fidelity=np.mean([m.state_fidelity for m in self.metrics_history]),
            process_fidelity=np.mean([m.process_fidelity for m in self.metrics_history]),
            gate_fidelity=np.mean([m.gate_fidelity for m in self.metrics_history]),
            measurement_fidelity=np.mean([m.measurement_fidelity for m in self.metrics_history]),
            entanglement_entropy=np.mean([m.entanglement_entropy for m in self.metrics_history]),
            concurrence=np.mean([m.concurrence for m in self.metrics_history]),
            negativity=np.mean([m.negativity for m in self.metrics_history]),
            mutual_information=np.mean([m.mutual_information for m in self.metrics_history]),
            execution_time_ms=np.mean([m.execution_time_ms for m in self.metrics_history]),
            error_rate=np.mean([m.error_rate for m in self.metrics_history]),
            success_probability=np.mean([m.success_probability for m in self.metrics_history])
        )

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        data = {
            'metrics_history': [m.to_dict() for m in self.metrics_history],
            'average_metrics': self.get_average_metrics().to_dict()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_report(self) -> str:
        """Generate metrics report"""
        avg = self.get_average_metrics()

        report = []
        report.append("=" * 60)
        report.append("QUANTUM METRICS REPORT")
        report.append("=" * 60)
        report.append("")
        report.append("Fidelity Metrics:")
        report.append(f"  State Fidelity: {avg.state_fidelity:.4f}")
        report.append(f"  Process Fidelity: {avg.process_fidelity:.4f}")
        report.append(f"  Gate Fidelity: {avg.gate_fidelity:.4f}")
        report.append(f"  Measurement Fidelity: {avg.measurement_fidelity:.4f}")
        report.append("")
        report.append("Entanglement Metrics:")
        report.append(f"  Entanglement Entropy: {avg.entanglement_entropy:.4f}")
        report.append(f"  Concurrence: {avg.concurrence:.4f}")
        report.append(f"  Negativity: {avg.negativity:.4f}")
        report.append(f"  Mutual Information: {avg.mutual_information:.4f}")
        report.append("")
        report.append("Performance Metrics:")
        report.append(f"  Execution Time: {avg.execution_time_ms:.2f} ms")
        report.append(f"  Success Probability: {avg.success_probability:.4f}")
        report.append(f"  Error Rate: {avg.error_rate:.4f}")
        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    print("Testing Quantum Metrics...")

    # Test fidelity analyzer
    print("\n=== Fidelity Analysis ===")

    # Create test states
    state1 = np.array([1, 0], dtype=complex)  # |0>
    state2 = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)  # |+>

    fidelity = FidelityAnalyzer.state_fidelity(state1, state2)
    print(f"Fidelity between |0⟩ and |+⟩: {fidelity:.4f}")

    # Test entanglement analyzer
    print("\n=== Entanglement Analysis ===")

    # Bell state
    bell_state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)

    entropy = EntanglementAnalyzer.von_neumann_entropy(
        np.outer(bell_state, bell_state.conj())
    )
    print(f"Von Neumann entropy of Bell state: {entropy:.4f}")

    concurrence = EntanglementAnalyzer.concurrence(bell_state)
    print(f"Concurrence of Bell state: {concurrence:.4f}")

    negativity = EntanglementAnalyzer.negativity(bell_state)
    print(f"Negativity of Bell state: {negativity:.4f}")

    # Test metrics collector
    print("\n=== Metrics Collection ===")

    collector = MetricsCollector()

    # Simulate some metrics
    for i in range(10):
        metrics = QuantumMetrics(
            state_fidelity=0.9 + 0.05 * np.random.randn(),
            entanglement_entropy=0.5 + 0.1 * np.random.randn(),
            execution_time_ms=100 + 20 * np.random.randn(),
            success_probability=0.95 + 0.03 * np.random.randn()
        )
        collector.collect_metrics(metrics)

    print(collector.generate_report())

    # Export metrics
    collector.export_metrics("/tmp/quantum_metrics.json")
    print("\nMetrics exported to /tmp/quantum_metrics.json")
