#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Main Quantum Agent
Integration of all quantum components into unified agent
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
import asyncio
from collections import deque
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentPhase(Enum):
    """Phases of quantum agentic loop"""
    INITIALIZATION = auto()
    PERCEPTION = auto()
    PROCESSING = auto()
    DECISION = auto()
    ACTION = auto()
    LEARNING = auto()
    REFLECTION = auto()


class AgentMode(Enum):
    """Operating modes of quantum agent"""
    EXPLORATION = auto()
    EXPLOITATION = auto()
    BALANCED = auto()
    ADAPTIVE = auto()


@dataclass
class AgentConfiguration:
    """Configuration for quantum agent"""
    # Quantum parameters
    num_qubits: int = 16
    num_ancilla: int = 4
    circuit_depth: int = 10

    # Agent parameters
    learning_rate: float = 0.01
    discount_factor: float = 0.95
    exploration_rate: float = 0.1
    exploration_decay: float = 0.995
    min_exploration: float = 0.01

    # Memory parameters
    memory_size: int = 10000
    batch_size: int = 32

    # Training parameters
    target_update_frequency: int = 100
    training_frequency: int = 4

    # Quantum-specific
    use_entanglement: bool = True
    use_superposition: bool = True
    use_interference: bool = True

    # Performance
    use_gpu: bool = False
    num_workers: int = 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            'num_qubits': self.num_qubits,
            'num_ancilla': self.num_ancilla,
            'circuit_depth': self.circuit_depth,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'exploration_rate': self.exploration_rate,
            'memory_size': self.memory_size,
            'batch_size': self.batch_size
        }


@dataclass
class PerceptionData:
    """Data from perception phase"""
    raw_observation: np.ndarray
    encoded_state: np.ndarray
    quantum_state: Optional[np.ndarray] = None
    timestamp: float = field(default_factory=time.time)

    def to_quantum(self) -> np.ndarray:
        """Convert to quantum state representation"""
        if self.quantum_state is not None:
            return self.quantum_state

        # Encode classical state into quantum amplitudes
        normalized = self.encoded_state / np.linalg.norm(self.encoded_state)
        return normalized.astype(complex)


@dataclass
class DecisionData:
    """Data from decision phase"""
    action: int
    action_probabilities: np.ndarray
    value_estimate: float
    q_values: Optional[np.ndarray] = None
    confidence: float = 0.0
    quantum_enhanced: bool = False


@dataclass
class Experience:
    """Experience tuple for learning"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    priority: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.tolist(),
            'action': self.action,
            'reward': self.reward,
            'next_state': self.next_state.tolist(),
            'done': self.done,
            'priority': self.priority
        }


class QuantumMemory:
    """Quantum-enhanced experience replay memory"""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.memory: deque = deque(maxlen=capacity)
        self.priorities: deque = deque(maxlen=capacity)
        self.position = 0

    def push(self, experience: Experience):
        """Add experience to memory"""
        max_priority = max(self.priorities) if self.priorities else 1.0

        self.memory.append(experience)
        self.priorities.append(max_priority)

    def sample(self, batch_size: int, alpha: float = 0.6) -> List[Experience]:
        """Sample batch with prioritized experience replay"""
        if len(self.memory) < batch_size:
            return list(self.memory)

        # Compute sampling probabilities
        priorities = np.array(self.priorities)
        probabilities = priorities ** alpha
        probabilities /= np.sum(probabilities)

        # Sample indices
        indices = np.random.choice(
            len(self.memory),
            size=batch_size,
            replace=False,
            p=probabilities
        )

        return [self.memory[i] for i in indices]

    def update_priorities(self, indices: List[int], priorities: List[float]):
        """Update priorities for sampled experiences"""
        for idx, priority in zip(indices, priorities):
            if idx < len(self.priorities):
                self.priorities[idx] = priority

    def __len__(self) -> int:
        return len(self.memory)

    def is_full(self) -> bool:
        return len(self.memory) >= self.capacity


class QuantumPerceptionModule:
    """Quantum-enhanced perception module"""

    def __init__(self, config: AgentConfiguration):
        self.config = config
        self.encoder = self._build_encoder()

    def _build_encoder(self) -> Callable:
        """Build state encoder"""
        def encoder(state: np.ndarray) -> np.ndarray:
            # Normalize and encode
            encoded = state.flatten()

            # Pad or truncate to match quantum register size
            target_size = 2 ** self.config.num_qubits

            if len(encoded) < target_size:
                encoded = np.pad(encoded, (0, target_size - len(encoded)))
            else:
                encoded = encoded[:target_size]

            # Normalize
            norm = np.linalg.norm(encoded)
            if norm > 0:
                encoded = encoded / norm

            return encoded

        return encoder

    def perceive(self, observation: np.ndarray) -> PerceptionData:
        """Process observation through perception module"""
        # Encode observation
        encoded = self.encoder(observation)

        # Create quantum state (amplitude encoding)
        quantum_state = encoded.astype(complex)

        return PerceptionData(
            raw_observation=observation,
            encoded_state=encoded,
            quantum_state=quantum_state
        )

    def batch_perceive(self, observations: List[np.ndarray]) -> List[PerceptionData]:
        """Process multiple observations"""
        return [self.perceive(obs) for obs in observations]


class QuantumDecisionModule:
    """Quantum-enhanced decision module"""

    def __init__(self, config: AgentConfiguration, num_actions: int):
        self.config = config
        self.num_actions = num_actions
        self.q_network = self._build_q_network()
        self.target_network = self._build_q_network()

    def _build_q_network(self) -> Callable:
        """Build Q-network"""
        # Simplified Q-network
        def q_network(state: np.ndarray) -> np.ndarray:
            # Compute Q-values (simplified)
            q_values = np.random.randn(self.num_actions) * 0.1
            return q_values

        return q_network

    def decide(
        self,
        perception: PerceptionData,
        exploration_rate: float
    ) -> DecisionData:
        """Make decision based on perception"""
        # Get Q-values
        q_values = self.q_network(perception.encoded_state)

        # Epsilon-greedy with quantum enhancement
        if np.random.random() < exploration_rate:
            # Explore
            action = np.random.randint(self.num_actions)
            confidence = 0.5
        else:
            # Exploit
            action = np.argmax(q_values)
            confidence = 1.0

        # Compute action probabilities (softmax)
        exp_q = np.exp(q_values - np.max(q_values))
        action_probs = exp_q / np.sum(exp_q)

        # Value estimate
        value = np.max(q_values)

        return DecisionData(
            action=action,
            action_probabilities=action_probs,
            value_estimate=value,
            q_values=q_values,
            confidence=confidence,
            quantum_enhanced=self.config.use_superposition
        )

    def update(self, batch: List[Experience], learning_rate: float):
        """Update decision module with batch of experiences"""
        # Simplified Q-learning update
        for experience in batch:
            # Compute TD error
            current_q = self.q_network(experience.state)[experience.action]
            next_max_q = np.max(self.target_network(experience.next_state))
            td_target = experience.reward + self.config.discount_factor * next_max_q * (not experience.done)
            td_error = td_target - current_q

            # Update (simplified)
            pass

    def update_target_network(self):
        """Update target network"""
        self.target_network = self.q_network


class QuantumLearningModule:
    """Quantum-enhanced learning module"""

    def __init__(self, config: AgentConfiguration):
        self.config = config
        self.optimizer = self._build_optimizer()

    def _build_optimizer(self) -> Callable:
        """Build optimizer"""
        def optimizer(params: np.ndarray, gradients: np.ndarray) -> np.ndarray:
            return params - self.config.learning_rate * gradients

        return optimizer

    def compute_gradients(
        self,
        batch: List[Experience],
        q_network: Callable,
        target_network: Callable
    ) -> np.ndarray:
        """Compute gradients for Q-network update"""
        # Simplified gradient computation
        gradients = np.zeros(2 ** self.config.num_qubits)

        for experience in batch:
            # Compute TD error
            current_q = q_network(experience.state)[experience.action]
            next_max_q = np.max(target_network(experience.next_state))
            td_target = experience.reward + self.config.discount_factor * next_max_q * (not experience.done)
            td_error = td_target - current_q

            # Accumulate gradients (simplified)
            gradients += td_error * experience.state

        return gradients / len(batch)

    def apply_update(self, params: np.ndarray, gradients: np.ndarray) -> np.ndarray:
        """Apply gradient update"""
        return self.optimizer(params, gradients)

    def quantum_gradient_boost(
        self,
        classical_gradients: np.ndarray,
        quantum_state: np.ndarray
    ) -> np.ndarray:
        """Enhance gradients with quantum information"""
        if not self.config.use_interference:
            return classical_gradients

        # Compute quantum interference term
        interference = np.abs(quantum_state) ** 2

        # Boost gradients based on quantum amplitudes
        boosted = classical_gradients * (1 + interference[:len(classical_gradients)])

        return boosted


class QuantumAgent:
    """
    Main Quantum Agent class
    Integrates all quantum-enhanced components
    """

    def __init__(
        self,
        num_actions: int,
        config: Optional[AgentConfiguration] = None
    ):
        self.config = config or AgentConfiguration()
        self.num_actions = num_actions

        # Initialize modules
        self.perception_module = QuantumPerceptionModule(self.config)
        self.decision_module = QuantumDecisionModule(self.config, num_actions)
        self.learning_module = QuantumLearningModule(self.config)
        self.memory = QuantumMemory(self.config.memory_size)

        # State
        self.current_phase = AgentPhase.INITIALIZATION
        self.exploration_rate = self.config.exploration_rate
        self.step_count = 0
        self.episode_count = 0

        # Metrics
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []
        self.loss_history: List[float] = []

        logger.info(f"Quantum Agent initialized with {num_actions} actions")

    def perceive(self, observation: np.ndarray) -> PerceptionData:
        """Perceive environment"""
        self.current_phase = AgentPhase.PERCEPTION
        return self.perception_module.perceive(observation)

    def decide(self, perception: PerceptionData) -> DecisionData:
        """Make decision"""
        self.current_phase = AgentPhase.DECISION
        return self.decision_module.decide(perception, self.exploration_rate)

    def act(self, decision: DecisionData) -> int:
        """Execute action"""
        self.current_phase = AgentPhase.ACTION
        return decision.action

    def learn(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Learn from experience"""
        self.current_phase = AgentPhase.LEARNING

        # Store experience
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done
        )
        self.memory.push(experience)

        # Learn if enough experiences
        if len(self.memory) >= self.config.batch_size:
            if self.step_count % self.config.training_frequency == 0:
                self._train_step()

        # Update exploration
        self.exploration_rate = max(
            self.config.min_exploration,
            self.exploration_rate * self.config.exploration_decay
        )

        self.step_count += 1

    def _train_step(self):
        """Perform single training step"""
        # Sample batch
        batch = self.memory.sample(self.config.batch_size)

        # Compute gradients
        gradients = self.learning_module.compute_gradients(
            batch,
            self.decision_module.q_network,
            self.decision_module.target_network
        )

        # Apply update (simplified)
        # self.decision_module.update(batch, self.config.learning_rate)

        # Update target network periodically
        if self.step_count % self.config.target_update_frequency == 0:
            self.decision_module.update_target_network()

    def run_episode(
        self,
        env_step: Callable[[int], Tuple[np.ndarray, float, bool, Dict]],
        reset_env: Callable[[], np.ndarray],
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """Run single episode"""
        state = reset_env()
        total_reward = 0.0
        steps = 0

        for step in range(max_steps):
            # Perceive
            perception = self.perceive(state)

            # Decide
            decision = self.decide(perception)

            # Act
            action = self.act(decision)

            # Environment step
            next_state, reward, done, info = env_step(action)

            # Learn
            self.learn(state, action, reward, next_state, done)

            total_reward += reward
            steps += 1
            state = next_state

            if done:
                break

        # Record metrics
        self.episode_rewards.append(total_reward)
        self.episode_lengths.append(steps)
        self.episode_count += 1

        return {
            'total_reward': total_reward,
            'steps': steps,
            'exploration_rate': self.exploration_rate
        }

    def train(
        self,
        env_step: Callable[[int], Tuple[np.ndarray, float, bool, Dict]],
        reset_env: Callable[[], np.ndarray],
        num_episodes: int,
        eval_interval: int = 100
    ) -> Dict[str, Any]:
        """Train agent for multiple episodes"""
        logger.info(f"Starting training for {num_episodes} episodes")

        start_time = time.time()

        for episode in range(num_episodes):
            result = self.run_episode(env_step, reset_env)

            if (episode + 1) % eval_interval == 0:
                avg_reward = np.mean(self.episode_rewards[-eval_interval:])
                logger.info(f"Episode {episode + 1}: avg_reward={avg_reward:.2f}, "
                           f"epsilon={self.exploration_rate:.4f}")

        training_time = time.time() - start_time

        return {
            'num_episodes': num_episodes,
            'total_steps': self.step_count,
            'avg_reward': np.mean(self.episode_rewards),
            'max_reward': max(self.episode_rewards),
            'training_time': training_time
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return {
            'episode_count': self.episode_count,
            'step_count': self.step_count,
            'exploration_rate': self.exploration_rate,
            'avg_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0,
            'avg_length': np.mean(self.episode_lengths) if self.episode_lengths else 0,
            'memory_size': len(self.memory)
        }

    def save(self, filepath: str):
        """Save agent state"""
        state = {
            'config': self.config.to_dict(),
            'episode_count': self.episode_count,
            'step_count': self.step_count,
            'exploration_rate': self.exploration_rate,
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Agent saved to {filepath}")

    @classmethod
    def load(cls, filepath: str, num_actions: int) -> 'QuantumAgent':
        """Load agent state"""
        with open(filepath, 'r') as f:
            state = json.load(f)

        config = AgentConfiguration(**state['config'])
        agent = cls(num_actions, config)

        agent.episode_count = state['episode_count']
        agent.step_count = state['step_count']
        agent.exploration_rate = state['exploration_rate']
        agent.episode_rewards = state['episode_rewards']
        agent.episode_lengths = state['episode_lengths']

        logger.info(f"Agent loaded from {filepath}")
        return agent


# Example usage
if __name__ == "__main__":
    print("Testing Quantum Agent...")

    # Create agent
    config = AgentConfiguration(
        num_qubits=4,
        learning_rate=0.001,
        exploration_rate=0.1,
        memory_size=1000
    )

    agent = QuantumAgent(num_actions=4, config=config)

    # Dummy environment
    class DummyEnv:
        def __init__(self):
            self.state = np.random.randn(16)

        def reset(self):
            self.state = np.random.randn(16)
            return self.state

        def step(self, action):
            reward = np.random.randn()
            done = np.random.random() < 0.05
            self.state = np.random.randn(16)
            return self.state, reward, done, {}

    env = DummyEnv()

    # Train
    print("\nTraining agent...")
    results = agent.train(
        env_step=env.step,
        reset_env=env.reset,
        num_episodes=100,
        eval_interval=25
    )

    print(f"\nTraining complete!")
    print(f"Total steps: {results['total_steps']}")
    print(f"Average reward: {results['avg_reward']:.2f}")
    print(f"Training time: {results['training_time']:.2f}s")

    # Get metrics
    metrics = agent.get_metrics()
    print(f"\nFinal metrics: {metrics}")

    # Save agent
    agent.save("/tmp/quantum_agent.json")
    print("\nAgent saved!")
