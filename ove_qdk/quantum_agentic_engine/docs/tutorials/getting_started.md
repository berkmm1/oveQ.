# Getting Started with Quantum Agentic Loop Engine

## Installation

### Prerequisites

- Python 3.9 or higher
- .NET SDK 6.0 or higher (for Q#)
- NumPy, SciPy

### Install from Source

```bash
git clone https://github.com/yourusername/quantum-agentic-engine.git
cd quantum-agentic-engine
pip install -e .
```

### Install Q# Development Kit

```bash
dotnet tool install -g Microsoft.Quantum.IQSharp
iqsharp install
```

## Quick Start

### 1. Create Your First Quantum Agent

```python
from quantum_agent import QuantumAgent, AgentConfiguration

# Configure agent
config = AgentConfiguration(
    num_qubits=8,
    learning_rate=0.001,
    exploration_rate=0.1
)

# Create agent
agent = QuantumAgent(num_actions=4, config=config)

print("Quantum agent created successfully!")
```

### 2. Define an Environment

```python
import numpy as np

class SimpleEnvironment:
    def __init__(self):
        self.state = np.zeros(8)
        self.step_count = 0

    def reset(self):
        self.state = np.random.randn(8)
        self.step_count = 0
        return self.state

    def step(self, action):
        # Simple reward based on action
        reward = -np.sum(self.state ** 2) + action * 0.1
        self.state = np.random.randn(8)
        self.step_count += 1
        done = self.step_count >= 100
        return self.state, reward, done, {}

env = SimpleEnvironment()
```

### 3. Train the Agent

```python
# Train for 100 episodes
results = agent.train(
    env_step=env.step,
    reset_env=env.reset,
    num_episodes=100,
    eval_interval=10
)

print(f"Training complete!")
print(f"Average reward: {results['avg_reward']:.2f}")
print(f"Total steps: {results['total_steps']}")
```

### 4. Evaluate and Save

```python
# Evaluate
rewards = []
for _ in range(10):
    result = agent.run_episode(env.step, env.reset)
    rewards.append(result['total_reward'])

print(f"Evaluation: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")

# Save agent
agent.save("my_agent.json")
```

## Quantum Algorithms Tutorial

### Grover's Search Algorithm

```python
from algorithms.quantum_grover import GroverSearch, GroverConfig

# Configure search
config = GroverConfig(
    num_qubits=8,
    num_solutions=1
)

# Create searcher
searcher = GroverSearch(config)

# Set oracle for target state
target_state = 42
searcher.set_oracle(searcher.create_simple_oracle(target_state))

# Search
result = searcher.search(num_shots=100)

print(f"Found solution: {result.solution}")
print(f"Success probability: {result.probability:.2%}")
print(f"Iterations: {result.iterations}")
```

### VQE for Ground State Energy

```python
from optimization.quantum_optimizer import VQE
import numpy as np

# Define Hamiltonian (e.g., H2 molecule)
hamiltonian = np.array([
    [0.5, 0, 0, 0],
    [0, -0.5, 0.1, 0],
    [0, 0.1, -0.5, 0],
    [0, 0, 0, 0.5]
], dtype=complex)

# Define ansatz
def ansatz(params):
    # Simple ansatz circuit
    state = np.array([1, 0, 0, 0], dtype=complex)
    # Apply rotations
    return state

# Create VQE
vqe = VQE(
    hamiltonian=hamiltonian,
    ansatz=ansatz,
    num_parameters=2
)

# Find ground state
result = vqe.find_ground_state()

print(f"Ground state energy: {result.optimal_value:.4f}")
print(f"Optimal parameters: {result.optimal_parameters}")
```

### Quantum Key Distribution

```python
from networking.quantum_communication import BB84Protocol, QuantumChannel

# Create protocol and channel
bb84 = BB84Protocol(num_qubits=1000)
channel = QuantumChannel(distance_km=10.0)

# Generate keys
alice_key, bob_key = bb84.generate_key(channel)

print(f"Alice's key length: {alice_key.key_length}")
print(f"Bob's key length: {bob_key.key_length}")
print(f"Error rate: {alice_key.error_rate:.4f}")
print(f"Keys match: {alice_key.key_bits == bob_key.key_bits}")
```

## Advanced Topics

### Custom Quantum Circuits

```python
from simulation.quantum_simulator import Circuit, StateVectorSimulator

# Create circuit
circuit = Circuit(num_qubits=3)

# Add gates
circuit.h(0)           # Hadamard on qubit 0
circuit.cnot(0, 1)     # CNOT with control 0, target 1
circuit.rz(2, np.pi/4) # RZ rotation on qubit 2
circuit.swap(1, 2)     # SWAP qubits 1 and 2

# Simulate
sim = StateVectorSimulator(num_qubits=3)
result = sim.run_circuit(circuit)

# Get probabilities
probs = sim.get_probabilities()
print(f"Probabilities: {probs}")
```

### Quantum Error Correction

```python
from qs.core.QuantumErrorCorrection import (
    EncodeSteane,
    MeasureSyndrome,
    ApplyCorrection
)

# Encode logical qubit
use logical = Qubit[7];
EncodeSteane(logical);

// Apply error
X(logical[0]);

// Measure syndrome
let syndrome = MeasureSyndrome(logical);

// Apply correction
ApplyCorrection(logical, syndrome);
```

### Distributed Quantum Computing

```python
from distributed.distributed_quantum import (
    DistributedQuantumExecutor,
    ComputeNode
)

# Create executor
executor = DistributedQuantumExecutor(max_workers=4)

# Register nodes
for i in range(4):
    node = ComputeNode(
        node_id=f"node_{i}",
        host="localhost",
        port=8000 + i,
        num_qubits=20
    )
    executor.scheduler.register_node(node)

# Start executor
executor.start()

# Submit circuits
circuits = [
    {"num_qubits": 4, "gates": ["H", "CNOT"]},
    {"num_qubits": 6, "gates": ["H", "CNOT", "RZ"]},
]

results = executor.batch_execute(circuits, num_shots=1000)

# Stop executor
executor.stop()
```

## Best Practices

### 1. Circuit Optimization

- Minimize circuit depth for NISQ devices
- Use gate fusion when possible
- Remove redundant gates

```python
# Before optimization
circuit = Circuit(num_qubits=2)
circuit.h(0)
circuit.h(0)  # Redundant
circuit.cnot(0, 1)

# After optimization
circuit = Circuit(num_qubits=2)
circuit.h(0)
circuit.cnot(0, 1)
```

### 2. Noise Mitigation

- Use error correction codes
- Apply zero-noise extrapolation
- Use probabilistic error cancellation

```python
# Use density matrix simulator for noise
from simulation.quantum_simulator import DensityMatrixSimulator

sim = DensityMatrixSimulator(num_qubits=4)
result = sim.run_circuit(circuit, noise_model={
    'depolarizing': 0.01,
    'amplitude_damping': 0.005
})
```

### 3. Performance Tuning

- Use GPU acceleration for large simulations
- Batch process multiple circuits
- Cache intermediate results

```python
# GPU-accelerated simulation
sim = StateVectorSimulator(num_qubits=20, use_gpu=True)

# Batch processing
results = executor.batch_execute(circuits, num_shots=1000)
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```
ModuleNotFoundError: No module named 'qsharp'
```

**Solution:** Install Q# development kit:
```bash
dotnet tool install -g Microsoft.Quantum.IQSharp
iqsharp install
```

#### 2. Memory Errors

```
MemoryError: Unable to allocate array
```

**Solution:** Reduce number of qubits or use GPU:
```python
sim = StateVectorSimulator(num_qubits=15, use_gpu=True)
```

#### 3. Convergence Issues

```
Agent not learning
```

**Solution:** Adjust hyperparameters:
```python
config = AgentConfiguration(
    learning_rate=0.001,  # Try smaller value
    exploration_rate=0.3,  # Increase exploration
    batch_size=64  # Larger batches
)
```

## Examples

### Example 1: Quantum Maze Solver

```python
import numpy as np
from quantum_agent import QuantumAgent, AgentConfiguration

class QuantumMaze:
    def __init__(self, size=5):
        self.size = size
        self.maze = np.random.choice([0, 1], (size, size), p=[0.7, 0.3])
        self.maze[0, 0] = 0  # Start
        self.maze[-1, -1] = 0  # Goal
        self.position = [0, 0]

    def reset(self):
        self.position = [0, 0]
        return self._get_observation()

    def step(self, action):
        # 0: up, 1: down, 2: left, 3: right
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        new_pos = [
            self.position[0] + moves[action][0],
            self.position[1] + moves[action][1]
        ]

        # Check bounds and walls
        if (0 <= new_pos[0] < self.size and
            0 <= new_pos[1] < self.size and
            self.maze[new_pos[0], new_pos[1]] == 0):
            self.position = new_pos

        # Reward
        reward = -1  # Step penalty
        if self.position == [self.size - 1, self.size - 1]:
            reward = 100  # Goal reached

        done = self.position == [self.size - 1, self.size - 1]
        return self._get_observation(), reward, done, {}

    def _get_observation(self):
        obs = np.zeros(self.size * self.size)
        idx = self.position[0] * self.size + self.position[1]
        obs[idx] = 1
        return obs

# Create and train agent
maze = QuantumMaze(size=5)
config = AgentConfiguration(num_qubits=25, learning_rate=0.001)
agent = QuantumAgent(num_actions=4, config=config)

results = agent.train(
    env_step=maze.step,
    reset_env=maze.reset,
    num_episodes=500
)

print(f"Average reward: {results['avg_reward']:.2f}")
```

### Example 2: Portfolio Optimization

```python
import numpy as np
from optimization.quantum_optimizer import QAOA

# Define portfolio optimization problem
num_assets = 4
returns = np.array([0.1, 0.15, 0.12, 0.08])
covariance = np.array([
    [0.1, 0.02, 0.01, 0.03],
    [0.02, 0.15, 0.03, 0.01],
    [0.01, 0.03, 0.12, 0.02],
    [0.03, 0.01, 0.02, 0.08]
])

# Build QUBO matrix
risk_tolerance = 0.5
Q = covariance - risk_tolerance * np.diag(returns)

# Convert to Hamiltonian
cost_hamiltonian = np.zeros((2**num_assets, 2**num_assets))
for i in range(num_assets):
    for j in range(num_assets):
        if i == j:
            cost_hamiltonian += Q[i, i] * np.kron(
                np.eye(2**i),
                np.kron(np.array([[0, 0], [0, 1]]), np.eye(2**(num_assets-i-1)))
            )

# Run QAOA
qaoa = QAOA(
    cost_hamiltonian=cost_hamiltonian,
    mixer_hamiltonian=np.eye(2**num_assets),  # Simplified
    num_qubits=num_assets,
    num_layers=2
)

result = qaoa.optimize()
print(f"Optimal portfolio value: {result.optimal_value:.4f}")
```

## Next Steps

- Read the [Architecture Documentation](architecture.md)
- Explore [API Reference](api_reference.md)
- Check out more [Examples](../examples/)
- Join the community discussions

## Support

- GitHub Issues: [Report bugs and request features](https://github.com/yourusername/quantum-agentic-engine/issues)
- Documentation: [Full documentation](https://quantum-agentic-engine.readthedocs.io)
- Discussions: [Community forum](https://github.com/yourusername/quantum-agentic-engine/discussions)
