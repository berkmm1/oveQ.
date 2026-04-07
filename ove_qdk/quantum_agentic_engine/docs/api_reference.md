# Quantum Agentic Loop Engine - API Reference

## Table of Contents

1. [Core Quantum Operations](#core-quantum-operations)
2. [Quantum Agent](#quantum-agent)
3. [Quantum Algorithms](#quantum-algorithms)
4. [Quantum Environments](#quantum-environments)
5. [Quantum Simulation](#quantum-simulation)
6. [Quantum Optimization](#quantum-optimization)
7. [Quantum Communication](#quantum-communication)
8. [Utilities](#utilities)

---

## Core Quantum Operations

### Q# Operations

#### `ExecuteAgenticLoop`

```qsharp
operation ExecuteAgenticLoop(
    agent : AgentQuantumState,
    environmentInput : Double[],
    config : AgentConfig
) : (AgentMeasurement, Double[])
```

Executes a complete agentic loop with quantum processing.

**Parameters:**
- `agent`: Quantum agent state containing all qubit registers
- `environmentInput`: Classical input from environment
- `config`: Agent configuration parameters

**Returns:**
- Measurement results and feedback values

#### `ApplyQuantumProcessing`

```qsharp
operation ApplyQuantumProcessing(
    agent : AgentQuantumState,
    config : AgentConfig
) : Unit
```

Applies quantum processing to agent state.

**Parameters:**
- `agent`: Agent quantum state
- `config`: Processing configuration

---

## Quantum Agent

### Python Classes

#### `QuantumAgent`

Main quantum agent class integrating all quantum-enhanced components.

```python
class QuantumAgent:
    def __init__(self, num_actions: int, config: Optional[AgentConfiguration] = None)
    def perceive(self, observation: np.ndarray) -> PerceptionData
    def decide(self, perception: PerceptionData) -> DecisionData
    def act(self, decision: DecisionData) -> int
    def learn(self, state, action, reward, next_state, done)
    def train(self, env_step, reset_env, num_episodes, eval_interval) -> Dict[str, Any]
```

**Example Usage:**

```python
from quantum_agent import QuantumAgent, AgentConfiguration

# Create configuration
config = AgentConfiguration(
    num_qubits=16,
    learning_rate=0.001,
    exploration_rate=0.1
)

# Create agent
agent = QuantumAgent(num_actions=4, config=config)

# Train
results = agent.train(env_step, reset_env, num_episodes=1000)

# Save
agent.save("agent.json")
```

#### `AgentConfiguration`

Configuration dataclass for quantum agent.

```python
@dataclass
class AgentConfiguration:
    num_qubits: int = 16
    num_ancilla: int = 4
    circuit_depth: int = 10
    learning_rate: float = 0.01
    discount_factor: float = 0.95
    exploration_rate: float = 0.1
    exploration_decay: float = 0.995
    min_exploration: float = 0.01
    memory_size: int = 10000
    batch_size: int = 32
    target_update_frequency: int = 100
    training_frequency: int = 4
    use_entanglement: bool = True
    use_superposition: bool = True
    use_interference: bool = True
    use_gpu: bool = False
    num_workers: int = 4
```

---

## Quantum Algorithms

### Grover's Algorithm

#### `GroverSearch`

```qsharp
operation GroverSearch(
    oracle : Oracle,
    config : GroverConfig
) : GroverResult
```

Implements Grover's quantum search algorithm.

**Parameters:**
- `oracle`: Quantum oracle marking target states
- `config`: Search configuration

**Returns:**
- Search result with solution and probability

#### Python Implementation

```python
from algorithms.quantum_grover import GroverSearch, GroverConfig

config = GroverConfig(num_qubits=8, num_solutions=1)
searcher = GroverSearch(config)
searcher.set_oracle(searcher.create_simple_oracle(target=42))
result = searcher.search(num_shots=100)
```

### Shor's Algorithm

#### `ShorsAlgorithm`

```python
from algorithms.quantum_shors import ShorsAlgorithm, ShorsConfig

config = ShorsConfig(max_trials=10)
shor = ShorsAlgorithm(config)
result = shor.factor(N=15)
print(f"Factors: {result.factors}")
```

### VQE (Variational Quantum Eigensolver)

```python
from optimization.quantum_optimizer import VQE

vqe = VQE(
    hamiltonian=hamiltonian_matrix,
    ansatz=ansatz_function,
    num_parameters=10
)
result = vqe.find_ground_state()
print(f"Ground state energy: {result.optimal_value}")
```

### QAOA (Quantum Approximate Optimization Algorithm)

```python
from optimization.quantum_optimizer import QAOA

qaoa = QAOA(
    cost_hamiltonian=cost_h,
    mixer_hamiltonian=mixer_h,
    num_qubits=4,
    num_layers=2
)
result = qaoa.optimize()
```

---

## Quantum Environments

### `QuantumGridWorld`

Grid world environment with quantum-enhanced observations.

```python
from environments.quantum_env_gym import QuantumGridWorld, QuantumEnvConfig

config = QuantumEnvConfig(
    state_dim=16,
    action_dim=4,
    use_quantum_observation=True
)

env = QuantumGridWorld(config)
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(action)
```

### `QuantumContinuousControl`

Continuous control environment with quantum features.

```python
from environments.quantum_env_gym import QuantumContinuousControl

env = QuantumContinuousControl(config)
```

---

## Quantum Simulation

### `StateVectorSimulator`

State vector quantum simulator.

```python
from simulation.quantum_simulator import StateVectorSimulator

sim = StateVectorSimulator(num_qubits=4, use_gpu=False)

# Create circuit
circuit = Circuit(num_qubits=4)
circuit.h(0)
circuit.cnot(0, 1)

# Run
result = sim.run_circuit(circuit)
probs = sim.get_probabilities()
```

### `DensityMatrixSimulator`

Density matrix simulator with noise support.

```python
from simulation.quantum_simulator import DensityMatrixSimulator

sim = DensityMatrixSimulator(num_qubits=4)

# Run with noise
result = sim.run_circuit(circuit, noise_model={
    'depolarizing': 0.1,
    'amplitude_damping': 0.05
})

entropy = sim.von_neumann_entropy()
```

---

## Quantum Optimization

### `QuantumOptimizer`

Classical optimizer wrapper for quantum objectives.

```python
from optimization.quantum_optimizer import QuantumOptimizer, OptimizerConfig

config = OptimizerConfig(
    optimizer_type=OptimizerType.ADAM,
    max_iterations=1000,
    learning_rate=0.01
)

optimizer = QuantumOptimizer(config)
result = optimizer.optimize(objective_fn, initial_parameters)
```

### Optimizer Types

- `COBYLA`: Constrained Optimization BY Linear Approximation
- `L_BFGS_B`: Limited-memory BFGS with bounds
- `SLSQP`: Sequential Least Squares Programming
- `ADAM`: Adaptive Moment Estimation
- `QUANTUM_NATURAL_GRADIENT`: Quantum natural gradient descent

---

## Quantum Communication

### `BB84Protocol`

BB84 quantum key distribution protocol.

```python
from networking.quantum_communication import BB84Protocol, QuantumChannel

bb84 = BB84Protocol(num_qubits=1000)
channel = QuantumChannel(distance_km=10.0)

alice_key, bob_key = bb84.generate_key(channel)
print(f"Key length: {alice_key.key_length}")
```

### `QuantumNetwork`

Multi-node quantum network.

```python
from networking.quantum_communication import QuantumNetwork, QuantumNode

network = QuantumNetwork()

# Add nodes
network.add_node("alice", QuantumNode("alice"))
network.add_node("bob", QuantumNode("bob"))

# Add channel
network.add_channel("alice", "bob", QuantumChannel(10.0))

# Establish key
network.establish_key("alice", "bob")

# Send secure message
encrypted = network.send_secure_message("alice", "bob", b"secret message")
```

---

## Utilities

### Quantum Metrics

```python
from analysis.quantum_metrics import (
    FidelityAnalyzer,
    EntanglementAnalyzer,
    CircuitAnalyzer
)

# Fidelity
fidelity = FidelityAnalyzer.state_fidelity(state1, state2)

# Entanglement
entropy = EntanglementAnalyzer.von_neumann_entropy(density_matrix)
concurrence = EntanglementAnalyzer.concurrence(bell_state)

# Circuit analysis
depth = CircuitAnalyzer.circuit_depth(circuit.gates)
gate_counts = CircuitAnalyzer.gate_count(circuit.gates)
```

### Visualization

```python
from visualization.quantum_viz import (
    QuantumStateVisualizer,
    CircuitVisualizer,
    ResultVisualizer
)

# State visualization
print(QuantumStateVisualizer.state_to_string(state))

# Circuit visualization
print(CircuitVisualizer.circuit_to_ascii(circuit, num_qubits=4))

# Results visualization
print(ResultVisualizer.measurement_histogram(counts))
```

---

## Error Handling

All operations may raise the following exceptions:

- `ValueError`: Invalid parameters or configuration
- `RuntimeError`: Quantum execution error
- `NotImplementedError`: Feature not yet implemented

**Example:**

```python
try:
    result = agent.train(env_step, reset_env, num_episodes=100)
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
except RuntimeError as e:
    logger.error(f"Execution failed: {e}")
```

---

## Performance Considerations

1. **GPU Acceleration**: Set `use_gpu=True` for large simulations
2. **Circuit Depth**: Keep circuits shallow for NISQ devices
3. **Batch Processing**: Use batch operations when possible
4. **Memory Management**: Monitor memory usage for large state vectors

---

## Version Information

- **Version**: 1.0.0
- **Q# Version**: 0.28.0
- **Python Version**: 3.9+
- **Last Updated**: 2024

---

## See Also

- [Architecture Documentation](architecture.md)
- [README](../README.md)
- [Examples](../examples/)
