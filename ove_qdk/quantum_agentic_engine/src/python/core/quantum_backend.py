"""
Quantum Backend Interface
========================

Unified interface for different quantum backends including:
- Q# simulators
- Qiskit providers
- Cirq simulators
- Custom simulators
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import json
import time

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Types of quantum backends."""
    QSHARP = auto()
    QISKIT = auto()
    CIRQ = auto()
    CUSTOM = auto()
    NOISY = auto()


class NoiseModel(Enum):
    """Noise models for simulation."""
    NONE = auto()
    DEPOLARIZING = auto()
    AMPLITUDE_DAMPING = auto()
    PHASE_DAMPING = auto()
    GATE_CALIBRATION = auto()
    CUSTOM = auto()


@dataclass
class BackendConfig:
    """Configuration for quantum backend."""
    backend_type: BackendType = BackendType.CUSTOM
    num_qubits: int = 20
    shots: int = 1024
    noise_model: NoiseModel = NoiseModel.NONE
    noise_params: Dict[str, float] = field(default_factory=dict)
    optimization_level: int = 1
    max_parallel: int = 4
    timeout: float = 300.0


@dataclass
class ExecutionResult:
    """Result from quantum execution."""
    counts: Dict[str, int]
    probabilities: Dict[str, float]
    expectation_values: Dict[str, float]
    raw_state: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    backend_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitMetrics:
    """Metrics for a quantum circuit."""
    num_qubits: int = 0
    num_gates: int = 0
    depth: int = 0
    num_parameters: int = 0
    gate_counts: Dict[str, int] = field(default_factory=dict)
    two_qubit_gate_count: int = 0


class QuantumBackend(ABC):
    """Abstract base class for quantum backends."""

    def __init__(self, config: BackendConfig):
        """Initialize backend with configuration."""
        self.config = config
        self._initialized = False
        self._circuit_cache: Dict[str, Any] = {}
        self._execution_history: List[Dict] = []

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the backend."""
        pass

    @abstractmethod
    def execute(self, circuit: Any, parameters: Optional[Dict] = None) -> ExecutionResult:
        """Execute a quantum circuit."""
        pass

    @abstractmethod
    def compile_circuit(self, circuit: Any) -> Any:
        """Compile a circuit for this backend."""
        pass

    @abstractmethod
    def get_metrics(self, circuit: Any) -> CircuitMetrics:
        """Get circuit metrics."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Get backend capabilities."""
        return {
            'num_qubits': self.config.num_qubits,
            'supported_gates': self._get_supported_gates(),
            'supports_noise': self.config.noise_model != NoiseModel.NONE,
            'supports_parameters': True
        }

    @abstractmethod
    def _get_supported_gates(self) -> List[str]:
        """Get list of supported gates."""
        pass

    def cache_circuit(self, name: str, circuit: Any) -> None:
        """Cache a compiled circuit."""
        self._circuit_cache[name] = self.compile_circuit(circuit)

    def get_cached_circuit(self, name: str) -> Optional[Any]:
        """Get a cached circuit."""
        return self._circuit_cache.get(name)

    def get_execution_history(self) -> List[Dict]:
        """Get execution history."""
        return self._execution_history.copy()


class QSharpBackend(QuantumBackend):
    """Backend for Q# execution."""

    def __init__(self, config: BackendConfig):
        super().__init__(config)
        self._simulator = None
        self._operation_registry: Dict[str, Callable] = {}

    def initialize(self) -> None:
        """Initialize Q# backend."""
        try:
            import qsharp
            self._simulator = qsharp.Simulator()

            # Configure noise if specified
            if self.config.noise_model != NoiseModel.NONE:
                self._setup_noise()

            self._initialized = True
            logger.info("Q# backend initialized successfully")

        except ImportError:
            logger.warning("Q# not available, using fallback")
            self._simulator = None

    def _setup_noise(self) -> None:
        """Setup noise model for Q#."""
        if self.config.noise_model == NoiseModel.DEPOLARIZING:
            rate = self.config.noise_params.get('depolarizing_rate', 0.001)
            # Configure Q# noise model
            logger.info(f"Depolarizing noise model with rate {rate}")

    def execute(self, operation: Callable, parameters: Optional[Dict] = None) -> ExecutionResult:
        """Execute a Q# operation."""
        start_time = time.time()

        try:
            if parameters:
                result = operation.simulate(**parameters)
            else:
                result = operation.simulate()

            execution_time = time.time() - start_time

            # Convert result to standard format
            counts = self._process_qsharp_result(result)

            return ExecutionResult(
                counts=counts,
                probabilities=self._counts_to_probabilities(counts),
                expectation_values={},
                execution_time=execution_time,
                backend_info={'type': 'Q#', 'simulator': 'default'}
            )

        except Exception as e:
            logger.error(f"Q# execution failed: {e}")
            raise

    def _process_qsharp_result(self, result: Any) -> Dict[str, int]:
        """Process Q# result into counts."""
        if isinstance(result, dict):
            return result
        elif isinstance(result, (list, tuple)):
            # Convert measurement array to counts
            counts = defaultdict(int)
            for measurement in result:
                key = ''.join(str(int(m)) for m in measurement)
                counts[key] += 1
            return dict(counts)
        else:
            return {'result': int(result)}

    def compile_circuit(self, circuit: Any) -> Any:
        """Compile for Q# (no-op for operations)."""
        return circuit

    def get_metrics(self, circuit: Any) -> CircuitMetrics:
        """Get circuit metrics for Q#."""
        # Q# doesn't expose circuit metrics easily
        return CircuitMetrics(
            num_qubits=self.config.num_qubits,
            num_gates=0,
            depth=0
        )

    def _get_supported_gates(self) -> List[str]:
        """Get supported Q# gates."""
        return ['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'Rx', 'Ry', 'Rz', 'SWAP', 'T', 'S']

    def register_operation(self, name: str, operation: Callable) -> None:
        """Register a Q# operation."""
        self._operation_registry[name] = operation


class QiskitBackend(QuantumBackend):
    """Backend for Qiskit execution."""

    def __init__(self, config: BackendConfig):
        super().__init__(config)
        self._provider = None
        self._backend = None

    def initialize(self) -> None:
        """Initialize Qiskit backend."""
        try:
            from qiskit import IBMQ, Aer, transpile
            from qiskit.providers.aer import AerSimulator
            from qiskit.providers.aer.noise import NoiseModel as QiskitNoiseModel

            # Use Aer simulator by default
            if self.config.noise_model == NoiseModel.NONE:
                self._backend = AerSimulator()
            else:
                noise_model = self._create_qiskit_noise_model()
                self._backend = AerSimulator(noise_model=noise_model)

            self._initialized = True
            logger.info("Qiskit backend initialized successfully")

        except ImportError:
            logger.warning("Qiskit not available")
            self._backend = None

    def _create_qiskit_noise_model(self):
        """Create Qiskit noise model."""
        from qiskit.providers.aer.noise import NoiseModel, depolarizing_error

        noise_model = NoiseModel()

        if self.config.noise_model == NoiseModel.DEPOLARIZING:
            rate = self.config.noise_params.get('depolarizing_rate', 0.001)
            error = depolarizing_error(rate, 1)
            noise_model.add_all_qubit_quantum_error(error, ['u1', 'u2', 'u3'])

        return noise_model

    def execute(self, circuit, parameters: Optional[Dict] = None) -> ExecutionResult:
        """Execute a Qiskit circuit."""
        from qiskit import transpile, execute

        start_time = time.time()

        # Bind parameters if provided
        if parameters:
            circuit = circuit.bind_parameters(parameters)

        # Transpile for backend
        transpiled = transpile(circuit, self._backend,
                              optimization_level=self.config.optimization_level)

        # Execute
        job = execute(transpiled, self._backend, shots=self.config.shots)
        result = job.result()

        execution_time = time.time() - start_time

        # Extract counts
        counts = result.get_counts()

        return ExecutionResult(
            counts=counts,
            probabilities=self._counts_to_probabilities(counts),
            expectation_values={},
            execution_time=execution_time,
            backend_info={'type': 'Qiskit', 'backend': str(self._backend)}
        )

    def compile_circuit(self, circuit) -> Any:
        """Compile a Qiskit circuit."""
        from qiskit import transpile
        return transpile(circuit, self._backend,
                        optimization_level=self.config.optimization_level)

    def get_metrics(self, circuit) -> CircuitMetrics:
        """Get Qiskit circuit metrics."""
        from qiskit.converters import circuit_to_dag

        dag = circuit_to_dag(circuit)

        gate_counts = {}
        two_qubit_count = 0

        for node in dag.op_nodes():
            gate_name = node.name
            gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1

            if len(node.qargs) == 2:
                two_qubit_count += 1

        return CircuitMetrics(
            num_qubits=circuit.num_qubits,
            num_gates=sum(gate_counts.values()),
            depth=circuit.depth(),
            num_parameters=len(circuit.parameters),
            gate_counts=gate_counts,
            two_qubit_gate_count=two_qubit_count
        )

    def _get_supported_gates(self) -> List[str]:
        """Get supported Qiskit gates."""
        return ['u1', 'u2', 'u3', 'cx', 'cz', 'id', 'x', 'y', 'z', 'h', 's', 'sdg',
                't', 'tdg', 'rx', 'ry', 'rz', 'swap', 'ccx']

    def _counts_to_probabilities(self, counts: Dict[str, int]) -> Dict[str, float]:
        """Convert counts to probabilities."""
        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()}


class CirqBackend(QuantumBackend):
    """Backend for Cirq execution."""

    def __init__(self, config: BackendConfig):
        super().__init__(config)
        self._simulator = None

    def initialize(self) -> None:
        """Initialize Cirq backend."""
        try:
            import cirq

            if self.config.noise_model == NoiseModel.NONE:
                self._simulator = cirq.Simulator()
            else:
                noise_model = self._create_cirq_noise_model()
                self._simulator = cirq.DensityMatrixSimulator(noise=noise_model)

            self._initialized = True
            logger.info("Cirq backend initialized successfully")

        except ImportError:
            logger.warning("Cirq not available")
            self._simulator = None

    def _create_cirq_noise_model(self):
        """Create Cirq noise model."""
        import cirq

        if self.config.noise_model == NoiseModel.DEPOLARIZING:
            rate = self.config.noise_params.get('depolarizing_rate', 0.001)
            return cirq.depolarize(rate)
        elif self.config.noise_model == NoiseModel.AMPLITUDE_DAMPING:
            gamma = self.config.noise_params.get('gamma', 0.01)
            return cirq.amplitude_damp(gamma)

        return cirq.depolarize(0)

    def execute(self, circuit, parameters: Optional[Dict] = None) -> ExecutionResult:
        """Execute a Cirq circuit."""
        import cirq

        start_time = time.time()

        # Resolve parameters if provided
        if parameters:
            resolver = cirq.ParamResolver(parameters)
            circuit = cirq.resolve_parameters(circuit, resolver)

        # Run simulation
        result = self._simulator.run(circuit, repetitions=self.config.shots)

        execution_time = time.time() - start_time

        # Extract measurement results
        counts = {}
        if result.measurements:
            for key, measurements in result.measurements.items():
                for measurement in measurements:
                    bitstring = ''.join(str(int(b)) for b in measurement)
                    counts[bitstring] = counts.get(bitstring, 0) + 1

        return ExecutionResult(
            counts=counts,
            probabilities=self._counts_to_probabilities(counts),
            expectation_values={},
            execution_time=execution_time,
            backend_info={'type': 'Cirq'}
        )

    def compile_circuit(self, circuit) -> Any:
        """Compile for Cirq (no-op)."""
        return circuit

    def get_metrics(self, circuit) -> CircuitMetrics:
        """Get Cirq circuit metrics."""
        return CircuitMetrics(
            num_qubits=len(circuit.all_qubits()),
            num_gates=len(list(circuit.all_operations())),
            depth=len(cirq.Circuit(circuit.all_operations()))
        )

    def _get_supported_gates(self) -> List[str]:
        """Get supported Cirq gates."""
        return ['H', 'X', 'Y', 'Z', 'CNOT', 'CZ', 'SWAP', 'Rx', 'Ry', 'Rz', 'T', 'S']


class CustomSimulatorBackend(QuantumBackend):
    """Custom statevector simulator backend."""

    def __init__(self, config: BackendConfig):
        super().__init__(config)
        self._state = None
        self._num_qubits = config.num_qubits

    def initialize(self) -> None:
        """Initialize custom simulator."""
        # Initialize to |0...0>
        self._state = np.zeros(2 ** self._num_qubits, dtype=complex)
        self._state[0] = 1.0
        self._initialized = True
        logger.info("Custom simulator backend initialized")

    def execute(self, circuit: List[Tuple[str, List[int], List[float]]],
                parameters: Optional[Dict] = None) -> ExecutionResult:
        """
        Execute a circuit on the custom simulator.

        Args:
            circuit: List of (gate_name, qubits, params) tuples
            parameters: Optional parameter values

        Returns:
            Execution result
        """
        start_time = time.time()

        # Apply gates
        for gate_name, qubits, params in circuit:
            self._apply_gate(gate_name, qubits, params)

        # Sample measurements
        probabilities = np.abs(self._state) ** 2
        samples = np.random.choice(len(probabilities), size=self.config.shots, p=probabilities)

        # Count outcomes
        counts = {}
        for sample in samples:
            bitstring = format(sample, f'0{self._num_qubits}b')
            counts[bitstring] = counts.get(bitstring, 0) + 1

        execution_time = time.time() - start_time

        return ExecutionResult(
            counts=counts,
            probabilities={format(i, f'0{self._num_qubits}b'): p
                          for i, p in enumerate(probabilities)},
            expectation_values={},
            raw_state=self._state.copy(),
            execution_time=execution_time,
            backend_info={'type': 'CustomSimulator'}
        )

    def _apply_gate(self, gate_name: str, qubits: List[int], params: List[float]) -> None:
        """Apply a gate to the state."""
        if gate_name == 'H':
            self._apply_hadamard(qubits[0])
        elif gate_name == 'X':
            self._apply_pauli_x(qubits[0])
        elif gate_name == 'Y':
            self._apply_pauli_y(qubits[0])
        elif gate_name == 'Z':
            self._apply_pauli_z(qubits[0])
        elif gate_name == 'CNOT':
            self._apply_cnot(qubits[0], qubits[1])
        elif gate_name == 'Rx':
            self._apply_rx(qubits[0], params[0])
        elif gate_name == 'Ry':
            self._apply_ry(qubits[0], params[0])
        elif gate_name == 'Rz':
            self._apply_rz(qubits[0], params[0])

    def _apply_hadamard(self, target: int) -> None:
        """Apply Hadamard gate."""
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        self._apply_single_qubit_gate(H, target)

    def _apply_pauli_x(self, target: int) -> None:
        """Apply Pauli-X gate."""
        X = np.array([[0, 1], [1, 0]])
        self._apply_single_qubit_gate(X, target)

    def _apply_pauli_y(self, target: int) -> None:
        """Apply Pauli-Y gate."""
        Y = np.array([[0, -1j], [1j, 0]])
        self._apply_single_qubit_gate(Y, target)

    def _apply_pauli_z(self, target: int) -> None:
        """Apply Pauli-Z gate."""
        Z = np.array([[1, 0], [0, -1]])
        self._apply_single_qubit_gate(Z, target)

    def _apply_rx(self, target: int, theta: float) -> None:
        """Apply Rx rotation."""
        Rx = np.array([[np.cos(theta/2), -1j*np.sin(theta/2)],
                       [-1j*np.sin(theta/2), np.cos(theta/2)]])
        self._apply_single_qubit_gate(Rx, target)

    def _apply_ry(self, target: int, theta: float) -> None:
        """Apply Ry rotation."""
        Ry = np.array([[np.cos(theta/2), -np.sin(theta/2)],
                       [np.sin(theta/2), np.cos(theta/2)]])
        self._apply_single_qubit_gate(Ry, target)

    def _apply_rz(self, target: int, theta: float) -> None:
        """Apply Rz rotation."""
        Rz = np.array([[np.exp(-1j*theta/2), 0],
                       [0, np.exp(1j*theta/2)]])
        self._apply_single_qubit_gate(Rz, target)

    def _apply_cnot(self, control: int, target: int) -> None:
        """Apply CNOT gate."""
        # Build full CNOT matrix
        dim = 2 ** self._num_qubits
        cnot = np.eye(dim, dtype=complex)

        for i in range(dim):
            control_bit = (i >> control) & 1
            if control_bit == 1:
                target_bit = (i >> target) & 1
                j = i ^ (1 << target)  # Flip target bit
                cnot[i, i] = 0
                cnot[i, j] = 1

        self._state = cnot @ self._state

    def _apply_single_qubit_gate(self, gate: np.ndarray, target: int) -> None:
        """Apply single-qubit gate to target qubit."""
        # Build full gate matrix
        dim = 2 ** self._num_qubits
        full_gate = np.eye(dim, dtype=complex)

        for i in range(dim):
            for j in range(dim):
                # Check if other qubits match
                other_match = True
                for q in range(self._num_qubits):
                    if q != target:
                        if ((i >> q) & 1) != ((j >> q) & 1):
                            other_match = False
                            break

                if other_match:
                    target_i = (i >> target) & 1
                    target_j = (j >> target) & 1
                    full_gate[i, j] = gate[target_i, target_j]

        self._state = full_gate @ self._state

    def compile_circuit(self, circuit: List[Tuple[str, List[int], List[float]]]) -> List[Tuple[str, List[int], List[float]]]:
        """Compile circuit (basic optimization)."""
        # Simple optimization: merge consecutive single-qubit gates
        compiled = []
        pending_gates: Dict[int, List] = {}

        for gate_name, qubits, params in circuit:
            if len(qubits) == 1:
                target = qubits[0]
                if target in pending_gates:
                    # Merge gates
                    pending_gates[target].append((gate_name, params))
                else:
                    pending_gates[target] = [(gate_name, params)]
            else:
                # Flush pending single-qubit gates
                for target, gates in pending_gates.items():
                    merged = self._merge_gates(gates)
                    compiled.append((merged[0], [target], merged[1]))
                pending_gates = {}

                compiled.append((gate_name, qubits, params))

        # Flush remaining gates
        for target, gates in pending_gates.items():
            merged = self._merge_gates(gates)
            compiled.append((merged[0], [target], merged[1]))

        return compiled

    def _merge_gates(self, gates: List[Tuple[str, List[float]]]) -> Tuple[str, List[float]]:
        """Merge consecutive single-qubit gates."""
        # Simplified: just return the last gate
        if not gates:
            return ('I', [])
        return gates[-1]

    def get_metrics(self, circuit: List[Tuple[str, List[int], List[float]]]) -> CircuitMetrics:
        """Get circuit metrics."""
        gate_counts = defaultdict(int)
        two_qubit_count = 0

        for gate_name, qubits, _ in circuit:
            gate_counts[gate_name] += 1
            if len(qubits) == 2:
                two_qubit_count += 1

        return CircuitMetrics(
            num_qubits=self._num_qubits,
            num_gates=len(circuit),
            depth=len(circuit),  # Simplified
            gate_counts=dict(gate_counts),
            two_qubit_gate_count=two_qubit_count
        )

    def _get_supported_gates(self) -> List[str]:
        """Get supported gates."""
        return ['H', 'X', 'Y', 'Z', 'Rx', 'Ry', 'Rz', 'CNOT', 'CZ']

    def _counts_to_probabilities(self, counts: Dict[str, int]) -> Dict[str, float]:
        """Convert counts to probabilities."""
        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()}


class BackendManager:
    """Manager for multiple quantum backends."""

    def __init__(self):
        """Initialize backend manager."""
        self._backends: Dict[str, QuantumBackend] = {}
        self._default_backend: Optional[str] = None

    def register_backend(self, name: str, backend: QuantumBackend) -> None:
        """Register a backend."""
        self._backends[name] = backend
        if self._default_backend is None:
            self._default_backend = name

        if not backend._initialized:
            backend.initialize()

    def get_backend(self, name: Optional[str] = None) -> QuantumBackend:
        """Get a backend by name."""
        if name is None:
            name = self._default_backend

        if name not in self._backends:
            raise ValueError(f"Backend '{name}' not registered")

        return self._backends[name]

    def set_default(self, name: str) -> None:
        """Set default backend."""
        if name not in self._backends:
            raise ValueError(f"Backend '{name}' not registered")
        self._default_backend = name

    def list_backends(self) -> List[str]:
        """List registered backends."""
        return list(self._backends.keys())

    def get_backend_info(self) -> Dict[str, Dict]:
        """Get information about all backends."""
        info = {}
        for name, backend in self._backends.items():
            info[name] = {
                'capabilities': backend.get_capabilities(),
                'initialized': backend._initialized
            }
        return info


# Global backend manager
_backend_manager = BackendManager()


def get_backend_manager() -> BackendManager:
    """Get global backend manager."""
    return _backend_manager


def create_default_backends():
    """Create and register default backends."""
    manager = get_backend_manager()

    # Try to create Q# backend
    try:
        qsharp_config = BackendConfig(backend_type=BackendType.QSHARP)
        qsharp_backend = QSharpBackend(qsharp_config)
        manager.register_backend('qsharp', qsharp_backend)
    except Exception as e:
        logger.warning(f"Could not create Q# backend: {e}")

    # Try to create Qiskit backend
    try:
        qiskit_config = BackendConfig(backend_type=BackendType.QISKIT)
        qiskit_backend = QiskitBackend(qiskit_config)
        manager.register_backend('qiskit', qiskit_backend)
    except Exception as e:
        logger.warning(f"Could not create Qiskit backend: {e}")

    # Try to create Cirq backend
    try:
        cirq_config = BackendConfig(backend_type=BackendType.CIRQ)
        cirq_backend = CirqBackend(cirq_config)
        manager.register_backend('cirq', cirq_backend)
    except Exception as e:
        logger.warning(f"Could not create Cirq backend: {e}")

    # Always create custom simulator
    custom_config = BackendConfig(backend_type=BackendType.CUSTOM, num_qubits=20)
    custom_backend = CustomSimulatorBackend(custom_config)
    manager.register_backend('simulator', custom_backend)

    return manager


# Initialize default backends on import
try:
    create_default_backends()
except Exception as e:
    logger.warning(f"Could not initialize default backends: {e}")


if __name__ == "__main__":
    # Test backends
    manager = get_backend_manager()
    print("Registered backends:", manager.list_backends())
    print("Backend info:", manager.get_backend_info())
