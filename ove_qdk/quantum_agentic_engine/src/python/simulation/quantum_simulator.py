#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - High-Performance Quantum Simulator
State vector and density matrix simulation with GPU acceleration support
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from collections import defaultdict
import copy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import GPU libraries
try:
    import cupy as cp
    GPU_AVAILABLE = True
    logger.info("GPU acceleration available via CuPy")
except ImportError:
    GPU_AVAILABLE = False
    logger.info("GPU acceleration not available, using CPU")


class GateType(Enum):
    """Types of quantum gates"""
    X = auto()
    Y = auto()
    Z = auto()
    H = auto()
    S = auto()
    T = auto()
    RX = auto()
    RY = auto()
    RZ = auto()
    CNOT = auto()
    CZ = auto()
    SWAP = auto()
    TOFFOLI = auto()
    CUSTOM = auto()


@dataclass
class Gate:
    """Quantum gate representation"""
    gate_type: GateType
    targets: List[int]
    controls: List[int] = field(default_factory=list)
    params: Dict[str, float] = field(default_factory=dict)
    matrix: Optional[np.ndarray] = None

    def get_matrix(self, num_qubits: int) -> np.ndarray:
        """Get full matrix representation of gate"""
        if self.matrix is not None:
            return self.matrix

        # Build matrix from gate type
        base_matrix = self._get_base_matrix()

        # Expand to full Hilbert space
        return self._expand_matrix(base_matrix, num_qubits)

    def _get_base_matrix(self) -> np.ndarray:
        """Get base 1- or 2-qubit matrix"""
        if self.gate_type == GateType.X:
            return np.array([[0, 1], [1, 0]], dtype=complex)
        elif self.gate_type == GateType.Y:
            return np.array([[0, -1j], [1j, 0]], dtype=complex)
        elif self.gate_type == GateType.Z:
            return np.array([[1, 0], [0, -1]], dtype=complex)
        elif self.gate_type == GateType.H:
            return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        elif self.gate_type == GateType.S:
            return np.array([[1, 0], [0, 1j]], dtype=complex)
        elif self.gate_type == GateType.T:
            return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
        elif self.gate_type == GateType.RX:
            theta = self.params.get('theta', 0)
            return np.array([
                [np.cos(theta/2), -1j*np.sin(theta/2)],
                [-1j*np.sin(theta/2), np.cos(theta/2)]
            ], dtype=complex)
        elif self.gate_type == GateType.RY:
            theta = self.params.get('theta', 0)
            return np.array([
                [np.cos(theta/2), -np.sin(theta/2)],
                [np.sin(theta/2), np.cos(theta/2)]
            ], dtype=complex)
        elif self.gate_type == GateType.RZ:
            theta = self.params.get('theta', 0)
            return np.array([
                [np.exp(-1j*theta/2), 0],
                [0, np.exp(1j*theta/2)]
            ], dtype=complex)
        elif self.gate_type == GateType.CNOT:
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]
            ], dtype=complex)
        elif self.gate_type == GateType.CZ:
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, -1]
            ], dtype=complex)
        elif self.gate_type == GateType.SWAP:
            return np.array([
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1]
            ], dtype=complex)
        else:
            return np.eye(2, dtype=complex)

    def _expand_matrix(self, base_matrix: np.ndarray, num_qubits: int) -> np.ndarray:
        """Expand base matrix to full Hilbert space"""
        dim = 2 ** num_qubits
        full_matrix = np.eye(dim, dtype=complex)

        if len(self.targets) == 1 and len(self.controls) == 0:
            # Single qubit gate
            target = self.targets[0]
            for i in range(dim):
                for j in range(dim):
                    if ((i >> target) & 1) == 0 and ((j >> target) & 1) == 0:
                        full_matrix[i, j] = base_matrix[0, 0]
                    elif ((i >> target) & 1) == 0 and ((j >> target) & 1) == 1:
                        full_matrix[i, j] = base_matrix[0, 1]
                    elif ((i >> target) & 1) == 1 and ((j >> target) & 1) == 0:
                        full_matrix[i, j] = base_matrix[1, 0]
                    else:
                        full_matrix[i, j] = base_matrix[1, 1]

        return full_matrix


@dataclass
class Circuit:
    """Quantum circuit representation"""
    num_qubits: int
    gates: List[Gate] = field(default_factory=list)

    def add_gate(self, gate: Gate):
        """Add gate to circuit"""
        self.gates.append(gate)

    def x(self, target: int):
        """Add X gate"""
        self.add_gate(Gate(GateType.X, [target]))

    def y(self, target: int):
        """Add Y gate"""
        self.add_gate(Gate(GateType.Y, [target]))

    def z(self, target: int):
        """Add Z gate"""
        self.add_gate(Gate(GateType.Z, [target]))

    def h(self, target: int):
        """Add H gate"""
        self.add_gate(Gate(GateType.H, [target]))

    def s(self, target: int):
        """Add S gate"""
        self.add_gate(Gate(GateType.S, [target]))

    def t(self, target: int):
        """Add T gate"""
        self.add_gate(Gate(GateType.T, [target]))

    def rx(self, target: int, theta: float):
        """Add RX gate"""
        self.add_gate(Gate(GateType.RX, [target], params={'theta': theta}))

    def ry(self, target: int, theta: float):
        """Add RY gate"""
        self.add_gate(Gate(GateType.RY, [target], params={'theta': theta}))

    def rz(self, target: int, theta: float):
        """Add RZ gate"""
        self.add_gate(Gate(GateType.RZ, [target], params={'theta': theta}))

    def cnot(self, control: int, target: int):
        """Add CNOT gate"""
        self.add_gate(Gate(GateType.CNOT, [target], [control]))

    def cz(self, control: int, target: int):
        """Add CZ gate"""
        self.add_gate(Gate(GateType.CZ, [target], [control]))

    def swap(self, qubit1: int, qubit2: int):
        """Add SWAP gate"""
        self.add_gate(Gate(GateType.SWAP, [qubit1, qubit2]))

    def toffoli(self, control1: int, control2: int, target: int):
        """Add Toffoli (CCNOT) gate"""
        self.add_gate(Gate(GateType.TOFFOLI, [target], [control1, control2]))

    def copy(self) -> 'Circuit':
        """Create copy of circuit"""
        return Circuit(self.num_qubits, copy.deepcopy(self.gates))


class StateVectorSimulator:
    """
    State vector quantum simulator
    """

    def __init__(self, num_qubits: int, use_gpu: bool = False):
        self.num_qubits = num_qubits
        self.dim = 2 ** num_qubits
        self.use_gpu = use_gpu and GPU_AVAILABLE

        # Initialize state to |0...0>
        self.state = np.zeros(self.dim, dtype=complex)
        self.state[0] = 1.0

        if self.use_gpu:
            self.state = cp.array(self.state)

    def reset(self):
        """Reset to initial state"""
        if self.use_gpu:
            self.state = cp.zeros(self.dim, dtype=complex)
            self.state[0] = 1.0
        else:
            self.state = np.zeros(self.dim, dtype=complex)
            self.state[0] = 1.0

    def apply_gate(self, gate: Gate):
        """Apply single gate to state"""
        # Convert to matrix and apply
        if len(gate.targets) == 1 and len(gate.controls) == 0:
            self._apply_single_qubit_gate(gate)
        elif len(gate.targets) == 1 and len(gate.controls) == 1:
            self._apply_controlled_gate(gate)
        elif gate.gate_type == GateType.SWAP:
            self._apply_swap(gate)
        else:
            # General matrix application
            matrix = gate.get_matrix(self.num_qubits)
            if self.use_gpu:
                matrix = cp.array(matrix)
            self.state = matrix @ self.state

    def _apply_single_qubit_gate(self, gate: Gate):
        """Apply single qubit gate efficiently"""
        target = gate.targets[0]
        base_matrix = gate._get_base_matrix()

        # Reshape state for efficient application
        if self.use_gpu:
            state_cpu = cp.asnumpy(self.state)
        else:
            state_cpu = self.state

        # Reshape to separate target qubit
        new_shape = [2] * self.num_qubits
        state_reshaped = state_cpu.reshape(new_shape)

        # Apply gate using einsum
        axes = list(range(self.num_qubits))
        axes[target] = self.num_qubits

        result = np.einsum(base_matrix, [self.num_qubits, target], state_reshaped, axes)

        if self.use_gpu:
            self.state = cp.array(result.flatten())
        else:
            self.state = result.flatten()

    def _apply_controlled_gate(self, gate: Gate):
        """Apply controlled gate"""
        control = gate.controls[0]
        target = gate.targets[0]

        # Apply only to states where control is |1>
        for i in range(self.dim):
            if (i >> control) & 1:
                # Control is 1, apply gate to target
                j = i ^ (1 << target)  # Flip target bit

                if gate.gate_type == GateType.CNOT:
                    # Swap amplitudes
                    if self.use_gpu:
                        temp = self.state[i].copy()
                        self.state = cp.array(self.state)
                        # Manual swap
                    else:
                        self.state[i], self.state[j] = self.state[j], self.state[i]

    def _apply_swap(self, gate: Gate):
        """Apply SWAP gate"""
        qubit1, qubit2 = gate.targets

        for i in range(self.dim):
            bit1 = (i >> qubit1) & 1
            bit2 = (i >> qubit2) & 1

            if bit1 != bit2:
                j = i ^ (1 << qubit1) ^ (1 << qubit2)

                if i < j:  # Only swap once
                    if self.use_gpu:
                        temp = self.state[i].copy()
                        # Manual swap needed for GPU
                    else:
                        self.state[i], self.state[j] = self.state[j], self.state[i]

    def run_circuit(self, circuit: Circuit) -> np.ndarray:
        """Run complete circuit"""
        for gate in circuit.gates:
            self.apply_gate(gate)

        return self.get_state()

    def get_state(self) -> np.ndarray:
        """Get current state vector"""
        if self.use_gpu:
            return cp.asnumpy(self.state)
        return self.state

    def get_probabilities(self) -> np.ndarray:
        """Get measurement probabilities"""
        state = self.get_state()
        return np.abs(state) ** 2

    def measure(self, qubit: Optional[int] = None, num_shots: int = 1) -> List[int]:
        """Measure state"""
        probabilities = self.get_probabilities()

        results = []
        for _ in range(num_shots):
            outcome = np.random.choice(self.dim, p=probabilities)

            if qubit is not None:
                outcome = (outcome >> qubit) & 1

            results.append(outcome)

        return results

    def measure_all(self, num_shots: int = 1) -> Dict[int, int]:
        """Measure all qubits multiple times"""
        results = self.measure(num_shots=num_shots)

        counts = defaultdict(int)
        for outcome in results:
            counts[outcome] += 1

        return dict(counts)

    def expectation_value(self, observable: np.ndarray) -> float:
        """Compute expectation value of observable"""
        state = self.get_state()
        return np.real(np.vdot(state, observable @ state))

    def fidelity(self, target_state: np.ndarray) -> float:
        """Compute fidelity with target state"""
        state = self.get_state()
        return np.abs(np.vdot(state, target_state)) ** 2


class DensityMatrixSimulator:
    """
    Density matrix quantum simulator with noise support
    """

    def __init__(self, num_qubits: int, use_gpu: bool = False):
        self.num_qubits = num_qubits
        self.dim = 2 ** num_qubits
        self.use_gpu = use_gpu and GPU_AVAILABLE

        # Initialize to |0...0⟩⟨0...0|
        self.rho = np.zeros((self.dim, self.dim), dtype=complex)
        self.rho[0, 0] = 1.0

        if self.use_gpu:
            self.rho = cp.array(self.rho)

    def reset(self):
        """Reset to initial state"""
        if self.use_gpu:
            self.rho = cp.zeros((self.dim, self.dim), dtype=complex)
            self.rho[0, 0] = 1.0
        else:
            self.rho = np.zeros((self.dim, self.dim), dtype=complex)
            self.rho[0, 0] = 1.0

    def apply_gate(self, gate: Gate):
        """Apply unitary gate"""
        matrix = gate.get_matrix(self.num_qubits)

        if self.use_gpu:
            matrix = cp.array(matrix)
            matrix_dag = matrix.conj().T
            self.rho = matrix @ self.rho @ matrix_dag
        else:
            matrix_dag = matrix.conj().T
            self.rho = matrix @ self.rho @ matrix_dag

    def apply_kraus_operators(self, kraus_ops: List[np.ndarray]):
        """Apply Kraus operators for noise"""
        new_rho = np.zeros_like(self.rho) if not self.use_gpu else cp.zeros_like(self.rho)

        for k in kraus_ops:
            if self.use_gpu:
                k = cp.array(k)
                k_dag = k.conj().T
                new_rho += k @ self.rho @ k_dag
            else:
                k_dag = k.conj().T
                new_rho += k @ self.rho @ k_dag

        self.rho = new_rho

    def depolarizing_noise(self, qubit: int, p: float):
        """Apply depolarizing noise"""
        # Kraus operators for depolarizing channel
        dim = 2 ** self.num_qubits

        # Identity
        k0 = np.sqrt(1 - 3*p/4) * np.eye(dim, dtype=complex)

        # X, Y, Z on target qubit
        x_gate = np.array([[0, 1], [1, 0]], dtype=complex)
        y_gate = np.array([[0, -1j], [1j, 0]], dtype=complex)
        z_gate = np.array([[1, 0], [0, -1]], dtype=complex)

        kraus_ops = [k0]

        for gate in [x_gate, y_gate, z_gate]:
            k = np.sqrt(p/4) * self._expand_single_qubit_gate(gate, qubit)
            kraus_ops.append(k)

        self.apply_kraus_operators(kraus_ops)

    def _expand_single_qubit_gate(self, gate: np.ndarray, target: int) -> np.ndarray:
        """Expand single qubit gate to full Hilbert space"""
        dim = 2 ** self.num_qubits
        full_gate = np.eye(dim, dtype=complex)

        for i in range(dim):
            for j in range(dim):
                if self._differ_only_at_bit(i, j, target):
                    bit_i = (i >> target) & 1
                    bit_j = (j >> target) & 1
                    full_gate[i, j] = gate[bit_i, bit_j]

        return full_gate

    def _differ_only_at_bit(self, i: int, j: int, bit: int) -> bool:
        """Check if i and j differ only at specified bit"""
        mask = ~(1 << bit)
        return (i & mask) == (j & mask)

    def amplitude_damping(self, qubit: int, gamma: float):
        """Apply amplitude damping noise"""
        dim = 2 ** self.num_qubits

        # Kraus operators
        k0 = np.eye(dim, dtype=complex)
        k1 = np.zeros((dim, dim), dtype=complex)

        for i in range(dim):
            if (i >> qubit) & 1:  # |1⟩ state
                j = i ^ (1 << qubit)  # Flip to |0⟩
                k0[i, i] = np.sqrt(1 - gamma)
                k1[j, i] = np.sqrt(gamma)
            else:
                k0[i, i] = 1.0

        self.apply_kraus_operators([k0, k1])

    def phase_damping(self, qubit: int, lambda_: float):
        """Apply phase damping noise"""
        dim = 2 ** self.num_qubits

        k0 = np.eye(dim, dtype=complex)
        k1 = np.zeros((dim, dim), dtype=complex)

        for i in range(dim):
            if (i >> qubit) & 1:  # |1⟩ state
                k0[i, i] = np.sqrt(1 - lambda_)
                k1[i, i] = np.sqrt(lambda_)
            else:
                k0[i, i] = 1.0

        self.apply_kraus_operators([k0, k1])

    def run_circuit(self, circuit: Circuit, noise_model: Optional[Dict] = None) -> np.ndarray:
        """Run circuit with optional noise"""
        for gate in circuit.gates:
            self.apply_gate(gate)

            # Apply noise after each gate
            if noise_model:
                for qubit in range(self.num_qubits):
                    if 'depolarizing' in noise_model:
                        self.depolarizing_noise(qubit, noise_model['depolarizing'])
                    if 'amplitude_damping' in noise_model:
                        self.amplitude_damping(qubit, noise_model['amplitude_damping'])
                    if 'phase_damping' in noise_model:
                        self.phase_damping(qubit, noise_model['phase_damping'])

        return self.get_density_matrix()

    def get_density_matrix(self) -> np.ndarray:
        """Get density matrix"""
        if self.use_gpu:
            return cp.asnumpy(self.rho)
        return self.rho

    def get_statevector(self) -> Optional[np.ndarray]:
        """Extract statevector if pure state"""
        rho = self.get_density_matrix()

        # Check if pure state
        purity = np.real(np.trace(rho @ rho))

        if np.isclose(purity, 1.0):
            # Find eigenvector with eigenvalue 1
            eigenvalues, eigenvectors = np.linalg.eigh(rho)
            max_idx = np.argmax(eigenvalues)
            return eigenvectors[:, max_idx]

        return None

    def measure(self, qubit: Optional[int] = None) -> int:
        """Measure state"""
        rho = self.get_density_matrix()

        if qubit is None:
            # Measure all qubits
            probabilities = np.real(np.diag(rho))
            return np.random.choice(self.dim, p=probabilities)
        else:
            # Measure single qubit
            p0 = 0.0
            for i in range(self.dim):
                if not ((i >> qubit) & 1):
                    p0 += np.real(rho[i, i])

            outcome = 0 if np.random.random() < p0 else 1

            # Collapse state
            self._collapse(qubit, outcome)

            return outcome

    def _collapse(self, qubit: int, outcome: int):
        """Collapse state after measurement"""
        rho = self.get_density_matrix()

        # Project onto outcome
        projector = np.zeros((self.dim, self.dim), dtype=complex)

        for i in range(self.dim):
            if ((i >> qubit) & 1) == outcome:
                projector[i, i] = 1.0

        new_rho = projector @ rho @ projector
        trace = np.real(np.trace(new_rho))

        if trace > 0:
            new_rho = new_rho / trace

        if self.use_gpu:
            self.rho = cp.array(new_rho)
        else:
            self.rho = new_rho

    def von_neumann_entropy(self) -> float:
        """Compute von Neumann entropy"""
        rho = self.get_density_matrix()
        eigenvalues = np.linalg.eigvalsh(rho)

        entropy = 0.0
        for ev in eigenvalues:
            if ev > 1e-10:
                entropy -= ev * np.log2(ev)

        return entropy

    def fidelity(self, target_state: np.ndarray) -> float:
        """Compute fidelity with pure state"""
        rho = self.get_density_matrix()

        if target_state.ndim == 1:
            # Pure state target
            return np.real(np.vdot(target_state, rho @ target_state))
        else:
            # Density matrix target
            sqrt_rho = self._matrix_sqrt(rho)
            fidelity_matrix = sqrt_rho @ target_state @ sqrt_rho
            return np.real(np.trace(self._matrix_sqrt(fidelity_matrix))) ** 2

    def _matrix_sqrt(self, matrix: np.ndarray) -> np.ndarray:
        """Compute matrix square root"""
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        sqrt_eigenvalues = np.sqrt(np.maximum(eigenvalues, 0))
        return eigenvectors @ np.diag(sqrt_eigenvalues) @ eigenvectors.conj().T


class QuantumSimulator:
    """
    Unified quantum simulator interface
    """

    def __init__(self, num_qubits: int, use_density_matrix: bool = False, use_gpu: bool = False):
        self.num_qubits = num_qubits
        self.use_density_matrix = use_density_matrix

        if use_density_matrix:
            self.backend = DensityMatrixSimulator(num_qubits, use_gpu)
        else:
            self.backend = StateVectorSimulator(num_qubits, use_gpu)

    def run(self, circuit: Circuit, noise_model: Optional[Dict] = None) -> np.ndarray:
        """Run circuit"""
        if self.use_density_matrix:
            return self.backend.run_circuit(circuit, noise_model)
        else:
            if noise_model:
                logger.warning("Noise model ignored in state vector mode")
            return self.backend.run_circuit(circuit)

    def measure(self, qubit: Optional[int] = None, num_shots: int = 1):
        """Measure state"""
        return self.backend.measure(qubit, num_shots)

    def get_state(self) -> np.ndarray:
        """Get current state"""
        if self.use_density_matrix:
            return self.backend.get_density_matrix()
        return self.backend.get_state()


# Example usage
if __name__ == "__main__":
    print("Testing Quantum Simulator...")

    # Test state vector simulator
    print("\n=== State Vector Simulator ===")
    sim = StateVectorSimulator(num_qubits=3, use_gpu=False)

    # Create Bell state
    circuit = Circuit(num_qubits=3)
    circuit.h(0)
    circuit.cnot(0, 1)

    sim.run_circuit(circuit)

    print(f"State: {sim.get_state()}")
    print(f"Probabilities: {sim.get_probabilities()}")

    # Measure
    results = sim.measure_all(num_shots=1000)
    print(f"Measurement results: {results}")

    # Test density matrix simulator
    print("\n=== Density Matrix Simulator ===")
    dm_sim = DensityMatrixSimulator(num_qubits=2, use_gpu=False)

    circuit = Circuit(num_qubits=2)
    circuit.h(0)
    circuit.cnot(0, 1)

    dm_sim.run_circuit(circuit)

    print(f"Density matrix:\n{dm_sim.get_density_matrix()}")
    print(f"Von Neumann entropy: {dm_sim.von_neumann_entropy():.4f}")

    # Test with noise
    print("\n=== With Depolarizing Noise ===")
    dm_sim.reset()
    dm_sim.run_circuit(circuit, noise_model={'depolarizing': 0.1})

    print(f"Density matrix after noise:\n{dm_sim.get_density_matrix()}")
    print(f"Von Neumann entropy: {dm_sim.von_neumann_entropy():.4f}")

    # Benchmark
    print("\n=== Benchmark ===")
    import time

    for n in [4, 6, 8]:
        sim = StateVectorSimulator(num_qubits=n, use_gpu=False)
        circuit = Circuit(num_qubits=n)

        # Add random gates
        for _ in range(n * 10):
            circuit.h(np.random.randint(n))
            circuit.cnot(np.random.randint(n), np.random.randint(n))

        start = time.time()
        sim.run_circuit(circuit)
        elapsed = time.time() - start

        print(f"n={n} qubits, {len(circuit.gates)} gates: {elapsed:.4f}s")
