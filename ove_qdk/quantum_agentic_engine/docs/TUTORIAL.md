# Quantum Agentic Loop Engine - Tutorial

## Getting Started

This tutorial will guide you through building quantum-enhanced autonomous agents using the Quantum Agentic Loop Engine.

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/quantum-agentic-engine.git
cd quantum-agentic-engine

# Install dependencies
pip install -r requirements.txt

# Install QDK (optional, for Q# compilation)
dotnet tool install -g Microsoft.Quantum.IQSharp
iqsharp install
```

## Quick Start

### 1. Your First Quantum Agent

```python
#!/usr/bin/env python3
"""My First Quantum Agent"""

import numpy as np
from agents.quantum_agent_manager import AgentConfig, AgentRole, QuantumAgent
from environments.quantum_env import QuantumGridWorld

# Step 1: Create agent configuration
config = AgentConfig(
    agent_id="my_first_agent",
    role=AgentRole.EXPLORER,
    num_qubits=4,  # Start small
    learning_rate=0.01,
    epsilon=0.2  # Exploration rate
)

# Step 2: Create the agent
agent = QuantumAgent(config)
print(f"Created agent: {agent.config.agent_id}")

# Step 3: Create environment
env = QuantumGridWorld(size=5, num_goals=2)
print(f"Created environment: {env.config.name}")

# Step 4: Run an episode
observation = env.reset()
total_reward = 0
steps = 0

print("\nRunning episode...")
print("-" * 40)

for step in range(100):
    # Perceive environment
    encoded_state = agent.perceive(observation)

    # Make decision
    action = agent.decide(encoded_state)

    # Execute action
    next_observation, reward, done, info = env.step(action)

    # Store experience
    experience = (
        encoded_state,
        action,
        reward,
        agent.perceive(next_observation),
        done
    )
    agent.store_experience(experience)

    # Learn from experience
    if len(agent.memory) >= agent.config.batch_size:
        loss = agent.learn()
        if step % 20 == 0:
            print(f"Step {step}: Loss = {loss:.4f}")

    total_reward += reward
    steps += 1
    observation = next_observation

    if done:
        print(f"Episode completed in {steps} steps!")
        break

print(f"\nTotal reward: {total_reward:.2f}")
print(f"Goals collected: {len(agent.state.episode_reward)}")
```

### 2. Training Multiple Episodes

```python
#!/usr/bin/env python3
"""Training Multiple Episodes"""

from training.quantum_trainer import TrainingConfig, OptimizerType, QuantumTrainer

def train_agent(num_episodes=100):
    """Train agent for multiple episodes"""

    # Create training configuration
    train_config = TrainingConfig(
        optimizer=OptimizerType.ADAM,
        learning_rate=0.001,
        gamma=0.99,
        num_epochs=5,
        batch_size=32,
        log_frequency=10
    )

    # Create trainer
    trainer = QuantumTrainer(agent, env, train_config)

    # Train
    print(f"\nTraining for {num_episodes} episodes...")
    trainer.train(num_episodes=num_episodes)

    # Get summary
    summary = trainer.get_training_summary()
    print("\nTraining Summary:")
    print(f"  Total episodes: {summary['total_episodes']}")
    print(f"  Best reward: {summary['best_reward']:.2f}")
    print(f"  Average reward: {summary['average_reward']:.2f}")

    return trainer

# Run training
trainer = train_agent(num_episodes=100)
```

### 3. Multi-Agent Coordination

```python
#!/usr/bin/env python3
"""Multi-Agent Coordination Example"""

from agents.quantum_agent_manager import (
    QuantumAgentManager,
    create_explorer_agent,
    create_exploiter_agent,
    create_coordinator_agent
)

# Create manager
manager = QuantumAgentManager()

# Create specialized agents
explorer = create_explorer_agent("explorer_1", num_qubits=6)
exploiter = create_exploiter_agent("exploiter_1", num_qubits=6)
coordinator = create_coordinator_agent("coordinator_1", num_qubits=8)

# Add to manager
manager.create_agent(explorer.config)
manager.create_agent(exploiter.config)
manager.create_agent(coordinator.config)

print("Created 3 agents:")
for agent_id in manager.get_all_agents().keys():
    print(f"  - {agent_id}")

# Establish quantum entanglement
print("\nEstablishing entanglement...")
manager.establish_entanglement("explorer_1", "coordinator_1")
manager.establish_entanglement("exploiter_1", "coordinator_1")

# Coordinate exploration task
print("\nCoordinating exploration task...")
manager.coordinate_agents(
    "explore_region",
    {"target_area": "north", "priority": "high"}
)

# Run parallel episodes
print("\nRunning parallel episodes...")
rewards = manager.run_parallel_episodes(
    environment_factory=lambda: QuantumGridWorld(size=6, num_goals=2),
    num_episodes=10
)

print(f"\nAverage reward: {np.mean(rewards):.2f}")

# Get system metrics
metrics = manager.get_system_metrics()
print(f"\nSystem metrics:")
print(f"  Total episodes: {metrics['system']['total_episodes']}")
print(f"  Messages exchanged: {metrics['system']['messages_exchanged']}")
```

### 4. Quantum Machine Learning

```python
#!/usr/bin/env python3
"""Quantum Machine Learning Example"""

from ml.quantum_ml import (
    QuantumNeuralNetwork, QuantumMLConfig,
    QuantumFeatureMap, QuantumKernel,
    QuantumSupportVectorMachine,
    create_quantum_classifier
)
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# Generate dataset
print("Generating dataset...")
X, y = make_classification(
    n_samples=200,
    n_features=16,
    n_informative=8,
    n_redundant=4,
    n_classes=2,
    random_state=42
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")

# Method 1: Quantum Neural Network
print("\n" + "="*40)
print("Method 1: Quantum Neural Network")
print("="*40)

config = QuantumMLConfig(
    num_qubits=8,
    num_layers=3,
    learning_rate=0.01,
    epochs=50,
    batch_size=16
)

qnn = QuantumNeuralNetwork(config)
qnn.build(input_dim=16)

print("Training QNN...")
qnn.fit(X_train, y_train, verbose=True)

metrics = qnn.evaluate(X_test, y_test)
print(f"\nTest accuracy: {metrics.get('accuracy', 0):.4f}")

# Method 2: Quantum SVM
print("\n" + "="*40)
print("Method 2: Quantum SVM")
print("="*40)

qsvm = QuantumSupportVectorMachine(num_qubits=8, kernel_type="zz")

print("Training QSVM...")
qsvm.fit(X_train, y_train)

accuracy = qsvm.score(X_test, y_test)
print(f"\nTest accuracy: {accuracy:.4f}")

# Method 3: Quantum Kernel with Classical SVM
print("\n" + "="*40)
print("Method 3: Quantum Kernel")
print("="*40)

kernel = QuantumKernel(num_qubits=8, kernel_type="zz")

print("Computing kernel matrices...")
K_train = kernel.compute_kernel_matrix(X_train)
K_test = kernel.compute_kernel_matrix(X_test, X_train)

# Use with classical SVM
from sklearn.svm import SVC
svm = SVC(kernel='precomputed')
svm.fit(K_train, y_train)

predictions = svm.predict(K_test)
accuracy = np.mean(predictions == y_test)
print(f"\nTest accuracy: {accuracy:.4f}")
```

### 5. Custom Environment

```python
#!/usr/bin/env python3
"""Custom Environment Example"""

import gym
from gym import spaces
import numpy as np
from environments.quantum_env import (
    EnvironmentConfig, EnvironmentType,
    QuantumObservationWrapper, QuantumRewardFunction
)

class CustomQuantumEnv(gym.Env):
    """Custom quantum-enhanced environment"""

    def __init__(self):
        super().__init__()

        # Configuration
        self.config = EnvironmentConfig(
            name="CustomEnv",
            env_type=EnvironmentType.HYBRID,
            state_dim=10,
            action_dim=3,
            num_qubits=6,
            use_quantum_observation=True,
            use_quantum_reward=True
        )

        # Spaces
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(3)

        # Quantum components
        self.obs_wrapper = QuantumObservationWrapper(10, 6)
        self.reward_func = QuantumRewardFunction(6)

        # State
        self.state = None
        self.target = None

    def reset(self):
        """Reset environment"""
        self.state = np.random.randn(10)
        self.target = np.random.randn(10)
        return self._get_obs()

    def step(self, action):
        """Execute action"""
        # Update state based on action
        if action == 0:
            self.state += 0.1 * np.random.randn(10)
        elif action == 1:
            self.state -= 0.1 * np.random.randn(10)
        else:
            self.state *= 0.9

        # Compute distance to target
        distance = np.linalg.norm(self.state - self.target)

        # Base reward
        base_reward = -distance

        # Quantum-enhanced reward
        obs = self._get_obs()
        reward = self.reward_func.compute(
            obs, action, obs, base_reward
        )

        # Done condition
        done = distance < 0.5

        info = {'distance': distance}

        return obs, reward, done, info

    def _get_obs(self):
        """Get observation"""
        obs = self.state.copy()
        if self.config.use_quantum_observation:
            obs = self.obs_wrapper.wrap(obs)
        return obs

    def render(self, mode='console'):
        """Render environment"""
        if mode == 'console':
            distance = np.linalg.norm(self.state - self.target)
            print(f"State: {self.state[:3]}... | Distance: {distance:.4f}")

# Use the custom environment
print("Custom Quantum Environment")
print("="*40)

env = CustomQuantumEnv()
obs = env.reset()

print(f"Observation shape: {obs.shape}")
print(f"Action space: {env.action_space}")

for step in range(20):
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)

    if step % 5 == 0:
        env.render()

    if done:
        print("Target reached!")
        break
```

### 6. Advanced: Quantum Error Correction

```qsharp
namespace Tutorial.ErrorCorrection {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;

    /// # Tutorial: Bit-flip Code
    /// This tutorial demonstrates the 3-qubit bit-flip error correction code

    /// # Summary
    /// Encode a single qubit using 3-qubit repetition code
    operation BitFlipEncode(dataQubit : Qubit, codeQubits : Qubit[]) : Unit {
        // |ψ⟩ = α|0⟩ + β|1⟩
        // Encode as: α|000⟩ + β|111⟩

        CNOT(dataQubit, codeQubits[0]);
        CNOT(dataQubit, codeQubits[1]);
    }

    /// # Summary
    /// Measure error syndrome
    operation BitFlipSyndrome(codeQubits : Qubit[], ancillaQubits : Qubit[]) : (Result, Result) {
        // Syndrome measurement
        // ancilla[0] = qubit[0] ⊕ qubit[1]
        // ancilla[1] = qubit[1] ⊕ qubit[2]

        CNOT(codeQubits[0], ancillaQubits[0]);
        CNOT(codeQubits[1], ancillaQubits[0]);

        CNOT(codeQubits[1], ancillaQubits[1]);
        CNOT(codeQubits[2], ancillaQubits[1]);

        return (M(ancillaQubits[0]), M(ancillaQubits[1]));
    }

    /// # Summary
    /// Correct errors based on syndrome
    operation BitFlipCorrect(codeQubits : Qubit[], syndrome : (Result, Result)) : Unit {
        let (s1, s2) = syndrome;

        // Syndrome table:
        // (0, 0): No error
        // (1, 0): Error on qubit 0
        // (1, 1): Error on qubit 1
        // (0, 1): Error on qubit 2

        if s1 == One and s2 == Zero {
            X(codeQubits[0]);  // Correct qubit 0
        } elif s1 == One and s2 == One {
            X(codeQubits[1]);  // Correct qubit 1
        } elif s1 == Zero and s2 == One {
            X(codeQubits[2]);  // Correct qubit 2
        }
    }

    /// # Summary
    /// Decode the logical qubit
    operation BitFlipDecode(codeQubits : Qubit[], dataQubit : Qubit) : Unit {
        // Decode by majority voting
        CNOT(codeQubits[0], dataQubit);
        CNOT(codeQubits[1], dataQubit);

        // Reset code qubits
        ResetAll(codeQubits);
    }

    /// # Summary
    /// Complete error correction demonstration
    operation DemonstrateErrorCorrection() : Unit {
        use dataQubit = Qubit();
        use codeQubits = Qubit[2];
        use ancillaQubits = Qubit[2];

        // Prepare superposition state
        H(dataQubit);

        // Encode
        BitFlipEncode(dataQubit, codeQubits);

        // Simulate error (bit flip on first code qubit)
        X(codeQubits[0]);

        // Measure syndrome
        let syndrome = BitFlipSyndrome(codeQubits, ancillaQubits);
        Message($"Error syndrome: {syndrome}");

        // Correct error
        BitFlipCorrect(codeQubits, syndrome);

        // Decode
        BitFlipDecode(codeQubits, dataQubit);

        // Verify state is preserved
        H(dataQubit);
        let result = M(dataQubit);
        Message($"Corrected state: {result}");

        Reset(dataQubit);
    }
}
```

## Best Practices

### 1. Start Small

Begin with fewer qubits and simpler environments:

```python
# Good: Start small
config = AgentConfig(num_qubits=4, memory_size=1000)

# Avoid: Too complex initially
config = AgentConfig(num_qubits=20, memory_size=100000)
```

### 2. Use Classical Fallback

Implement classical alternatives for debugging:

```python
class HybridAgent:
    def __init__(self, use_quantum=True):
        self.use_quantum = use_quantum

    def perceive(self, observation):
        if self.use_quantum:
            return self._quantum_perceive(observation)
        else:
            return self._classical_perceive(observation)
```

### 3. Monitor Performance

Track key metrics during training:

```python
from utils.quantum_visualization import TrainingVisualizer

visualizer = TrainingVisualizer()

for episode in range(num_episodes):
    reward = train_episode()
    visualizer.update({'rewards': reward})

    if visualizer.detect_convergence('rewards'):
        print("Training converged!")
        break
```

### 4. Save Checkpoints

Regularly save training progress:

```python
if episode % 100 == 0:
    agent.save(f"checkpoint_{episode}.json")
    trainer.save_checkpoint(episode)
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more use cases
2. **Read API Reference**: See `API_REFERENCE.md` for detailed documentation
3. **Run Benchmarks**: Use `benchmarks/performance_suite.py` to test performance
4. **Contribute**: Submit improvements and new features

## Support

- GitHub Issues: https://github.com/your-org/quantum-agentic-engine/issues
- Documentation: https://quantum-agentic-engine.readthedocs.io
- Community Forum: https://forum.quantum-agentic-engine.org
