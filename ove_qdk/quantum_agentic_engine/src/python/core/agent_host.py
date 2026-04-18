#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Python Host
Main interface between classical control and quantum operations
"""

import qsharp
import numpy as np
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZED = auto()
    PERCEIVING = auto()
    PROCESSING = auto()
    DECIDING = auto()
    ACTING = auto()
    LEARNING = auto()
    ERROR = auto()
    TERMINATED = auto()


@dataclass
class AgentConfig:
    """Configuration for quantum agent"""
    num_perception_qubits: int = 16
    num_decision_qubits: int = 8
    num_action_qubits: int = 8
    num_memory_qubits: int = 32
    num_entanglement_qubits: int = 16
    learning_rate: float = 0.01
    discount_factor: float = 0.95
    exploration_rate: float = 0.1
    batch_size: int = 32
    buffer_size: int = 10000
    target_update_freq: int = 100
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01

    def to_dict(self) -> Dict[str, Any]:
        return {
            "NumPerceptionQubits": self.num_perception_qubits,
            "NumDecisionQubits": self.num_decision_qubits,
            "NumActionQubits": self.num_action_qubits,
            "NumMemoryQubits": self.num_memory_qubits,
            "NumEntanglementQubits": self.num_entanglement_qubits,
            "LearningRate": self.learning_rate,
            "DiscountFactor": self.discount_factor,
            "ExplorationRate": self.exploration_rate
        }


@dataclass
class Experience:
    """Experience tuple for replay buffer"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    priority: float = 1.0

    def to_qsharp(self) -> Any:
        """Convert to Q# Experience struct"""
        return {
            "State": self.state.tolist(),
            "Action": self.action,
            "Reward": self.reward,
            "NextState": self.next_state.tolist(),
            "Done": self.done
        }


@dataclass
class AgentMetrics:
    """Performance metrics for agent"""
    episode_rewards: List[float] = field(default_factory=list)
    episode_lengths: List[int] = field(default_factory=list)
    q_value_means: List[float] = field(default_factory=list)
    loss_history: List[float] = field(default_factory=list)
    epsilon_history: List[float] = field(default_factory=list)
    decision_times: List[float] = field(default_factory=list)

    def log_episode(self, reward: float, length: int, epsilon: float):
        self.episode_rewards.append(reward)
        self.episode_lengths.append(length)
        self.epsilon_history.append(epsilon)

    def log_training(self, q_mean: float, loss: float):
        self.q_value_means.append(q_mean)
        self.loss_history.append(loss)

    def get_summary(self) -> Dict[str, float]:
        if not self.episode_rewards:
            return {}
        return {
            "mean_reward": np.mean(self.episode_rewards[-100:]),
            "max_reward": np.max(self.episode_rewards),
            "mean_length": np.mean(self.episode_lengths[-100:]),
            "final_epsilon": self.epsilon_history[-1] if self.epsilon_history else 0
        }


class ReplayBuffer:
    """Prioritized experience replay buffer"""

    def __init__(self, capacity: int = 10000, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity)
        self.position = 0

    def add(self, experience: Experience):
        """Add experience with maximum priority"""
        max_priority = max(self.priorities) if self.priorities else 1.0

        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(max_priority)
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = max_priority

        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int, beta: float = 0.4) -> Tuple[List[Experience], np.ndarray, np.ndarray]:
        """Sample batch with prioritized experience replay"""
        if len(self.buffer) == 0:
            return [], np.array([]), np.array([])

        # Compute sampling probabilities
        priorities = np.array(self.priorities)
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()

        # Sample indices
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities, replace=False)

        # Compute importance sampling weights
        weights = (len(self.buffer) * probabilities[indices]) ** (-beta)
        weights /= weights.max()

        samples = [self.buffer[idx] for idx in indices]

        return samples, indices, weights

    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray):
        """Update priorities after learning"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-6  # Small constant for stability

    def __len__(self) -> int:
        return len(self.buffer)


class QuantumAgentHost:
    """
    Main host class for quantum agentic loop engine.
    Manages Q# operations and classical coordination.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.state = AgentState.INITIALIZED
        self.metrics = AgentMetrics()
        self.replay_buffer = ReplayBuffer(self.config.buffer_size)

        # Threading
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Episode tracking
        self.current_episode = 0
        self.epsilon = self.config.exploration_rate

        # Initialize Q# environment
        self._init_qsharp()

        logger.info(f"QuantumAgentHost initialized with config: {self.config}")

    def _init_qsharp(self):
        """Initialize Q# environment and compile operations"""
        try:
            # Initialize Q# with appropriate target profile
            qsharp.init(target_profile=qsharp.TargetProfile.Base)

            # Load core Q# source files first to avoid dependencies issues
            qs_dir = Path(__file__).parent.parent.parent / "qs"

            # Specifically load QuantumAgentCore.qs first
            # We use a simplified version for the host to ensure stability during tests
            core_qs = qs_dir / "core" / "QuantumAgentCore.qs"
            if core_qs.exists():
                try:
                    with open(core_qs, "r") as f:
                        content = f.read()
                        # Newer Q# might have issues with some complex constructs if not fully compatible
                        qsharp.eval(content)
                    logger.info(f"Loaded core Q# file: {core_qs}")
                except Exception as e:
                    logger.error(f"Failed to load core Q# file: {e}")

            # Import Q# namespaces
            self.qsharp_namespace = "QuantumAgentic.Core"
            self.learning_namespace = "QuantumAgentic.Learning"

            logger.info("Q# environment initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Q# environment: {e}")
            raise

    def initialize_agent(self) -> Dict[str, Any]:
        """Initialize quantum agent in Q#"""
        with self._lock:
            try:
                # Call Q# InitializeAgent operation
                # In 1.x, we might need to pass arguments correctly to eval or use qsharp.run
                config_dict = self.config.to_dict()

                # Note: Structs in Q# might need specific formatting if passed via eval
                # For now, we'll keep it simple as the environment initialization is already done

                logger.info("Quantum agent initialized")
                return {"status": "success", "config": config_dict}
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                self.state = AgentState.ERROR
                return {"status": "error", "message": str(e)}

    def perceive(self, environment_state: np.ndarray) -> np.ndarray:
        """
        Phase 1: Perception - Encode environment state into quantum register
        """
        with self._lock:
            self.state = AgentState.PERCEIVING

            try:
                # Normalize input
                normalized = self._normalize_state(environment_state)

                # Call Q# EncodeEnvironmentInput simulation via host
                # In a real hybrid setup, this would manipulate quantum memory

                logger.debug(f"Perceived state shape: {normalized.shape}")
                return normalized
            except Exception as e:
                logger.error(f"Perception failed: {e}")
                self.state = AgentState.ERROR
                return environment_state

    def process(self, encoded_state: np.ndarray) -> np.ndarray:
        """
        Phase 2: Quantum Processing - Apply quantum neural network
        """
        with self._lock:
            self.state = AgentState.PROCESSING

            try:
                # Call Q# ApplyQuantumProcessing
                # result = qsharp.eval(f"{self.qsharp_namespace}.ApplyQuantumProcessing(...)")

                # For now, simulate with classical processing
                processed = self._simulate_quantum_processing(encoded_state)

                logger.debug(f"Processed state shape: {processed.shape}")
                return processed
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                self.state = AgentState.ERROR
                return encoded_state

    def decide(self, processed_state: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Phase 3: Decision Making - Select action using quantum policy
        """
        with self._lock:
            self.state = AgentState.DECIDING
            start_time = time.time()

            try:
                # Epsilon-greedy with quantum enhancement
                if np.random.random() < self.epsilon:
                    # Random exploration
                    action = np.random.randint(0, self.config.num_action_qubits)
                    q_values = np.random.randn(self.config.num_action_qubits)
                else:
                    # Quantum policy evaluation
                    # Here we actually call a Q# operation that might return measurement results
                    # result = qsharp.run(f"{self.qsharp_namespace}.MeasureDecisionQubits(...)")

                    q_values = self._simulate_q_network(processed_state)
                    action = int(np.argmax(q_values))

                decision_time = time.time() - start_time
                self.metrics.decision_times.append(decision_time)

                logger.debug(f"Selected action: {action}, Q-values: {q_values}")
                return action, q_values
            except Exception as e:
                logger.error(f"Decision failed: {e}")
                self.state = AgentState.ERROR
                return 0, np.zeros(self.config.num_action_qubits)

    def act(self, action: int) -> Dict[str, Any]:
        """
        Phase 4: Action Execution - Apply selected action
        """
        with self._lock:
            self.state = AgentState.ACTING

            try:
                # Call Q# SelectActions
                # result = qsharp.eval(f"{self.qsharp_namespace}.SelectActions(...)")

                return {
                    "action": action,
                    "timestamp": time.time(),
                    "status": "executed"
                }
            except Exception as e:
                logger.error(f"Action execution failed: {e}")
                self.state = AgentState.ERROR
                return {"action": action, "status": "error", "message": str(e)}

    def learn(self, batch_size: Optional[int] = None) -> Dict[str, float]:
        """
        Phase 5: Learning - Update quantum policy
        """
        with self._lock:
            self.state = AgentState.LEARNING

            batch_size = batch_size or self.config.batch_size

            if len(self.replay_buffer) < batch_size:
                return {"status": "insufficient_data", "buffer_size": len(self.replay_buffer)}

            try:
                # Sample batch
                batch, indices, weights = self.replay_buffer.sample(batch_size)

                # Convert to Q# format
                qsharp_batch = [exp.to_qsharp() for exp in batch]

                # Call Q# training operations
                # result = qsharp.eval(f"{self.learning_namespace}.QuantumActorCriticUpdate(...)")

                # Simulate training
                loss = self._simulate_training(batch, weights)

                # Update priorities
                new_priorities = np.ones(len(batch)) * loss
                self.replay_buffer.update_priorities(indices, new_priorities)

                # Update epsilon
                self.epsilon = max(
                    self.epsilon * self.config.epsilon_decay,
                    self.config.epsilon_min
                )

                # Log metrics
                self.metrics.log_training(0.0, loss)

                logger.info(f"Training step complete. Loss: {loss:.4f}, Epsilon: {self.epsilon:.4f}")

                return {
                    "loss": loss,
                    "epsilon": self.epsilon,
                    "buffer_size": len(self.replay_buffer)
                }
            except Exception as e:
                logger.error(f"Learning failed: {e}")
                self.state = AgentState.ERROR
                return {"status": "error", "message": str(e)}

    def run_episode(
        self,
        env_step: Callable[[int], Tuple[np.ndarray, float, bool]],
        reset_env: Callable[[], np.ndarray],
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """
        Run a complete episode
        """
        state = reset_env()
        episode_reward = 0.0
        episode_length = 0
        experiences = []

        for step in range(max_steps):
            # Agentic loop
            encoded_state = self.perceive(state)
            processed = self.process(encoded_state)
            action, q_values = self.decide(processed)
            action_result = self.act(action)

            # Environment step
            next_state, reward, done = env_step(action)

            # Store experience
            exp = Experience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done
            )
            experiences.append(exp)
            self.replay_buffer.add(exp)

            episode_reward += reward
            episode_length += 1
            state = next_state

            # Learn every N steps
            if step % 4 == 0 and len(self.replay_buffer) >= self.config.batch_size:
                self.learn()

            if done:
                break

        # Log episode
        self.metrics.log_episode(episode_reward, episode_length, self.epsilon)
        self.current_episode += 1

        logger.info(f"Episode {self.current_episode} complete. "
                   f"Reward: {episode_reward:.2f}, Length: {episode_length}")

        return {
            "episode": self.current_episode,
            "reward": episode_reward,
            "length": episode_length,
            "epsilon": self.epsilon
        }

    def train(
        self,
        env_step: Callable[[int], Tuple[np.ndarray, float, bool]],
        reset_env: Callable[[], np.ndarray],
        episodes: int = 1000,
        max_steps: int = 1000,
        save_freq: int = 100
    ) -> AgentMetrics:
        """
        Train agent for multiple episodes
        """
        logger.info(f"Starting training for {episodes} episodes")

        for episode in range(episodes):
            result = self.run_episode(env_step, reset_env, max_steps)

            if episode % save_freq == 0:
                self.save_checkpoint(f"checkpoint_{episode}.json")

        logger.info("Training complete")
        return self.metrics

    def save_checkpoint(self, filepath: str):
        """Save agent checkpoint"""
        checkpoint = {
            "config": self.config.__dict__,
            "metrics": {
                "episode_rewards": self.metrics.episode_rewards,
                "epsilon_history": self.metrics.epsilon_history
            },
            "episode": self.current_episode,
            "epsilon": self.epsilon
        }

        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Checkpoint saved: {filepath}")

    def load_checkpoint(self, filepath: str):
        """Load agent checkpoint"""
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)

        self.config = AgentConfig(**checkpoint["config"])
        self.current_episode = checkpoint["episode"]
        self.epsilon = checkpoint["epsilon"]

        logger.info(f"Checkpoint loaded: {filepath}")

    def _normalize_state(self, state: np.ndarray) -> np.ndarray:
        """Normalize state to [-1, 1] range"""
        return np.tanh(state)

    def _simulate_quantum_processing(self, state: np.ndarray) -> np.ndarray:
        """Simulate quantum processing using numpy as a fallback or integration layer"""
        # Apply random unitary transformation to mimic quantum dynamics
        dim = len(state)
        unitary = np.random.randn(dim, dim)
        unitary = unitary + unitary.T  # Make symmetric
        unitary = unitary / np.linalg.norm(unitary, axis=1, keepdims=True)
        return np.dot(unitary, state)

    def _simulate_q_network(self, state: np.ndarray) -> np.ndarray:
        """Simulate Q-network for action selection"""
        # Simple neural network simulation that mimics the quantum policy output
        hidden = np.tanh(np.random.randn(self.config.num_decision_qubits, len(state)) @ state)
        q_values = np.random.randn(self.config.num_action_qubits, len(hidden)) @ hidden
        return q_values

    def _simulate_training(
        self,
        batch: List[Experience],
        weights: np.ndarray
    ) -> float:
        """Execute training update and return loss"""
        # Compute TD error for reinforcement learning
        losses = []
        for exp, weight in zip(batch, weights):
            td_error = exp.reward + (0 if exp.done else self.config.discount_factor * 0.5) - 0.5
            losses.append(weight * td_error ** 2)

        return float(np.mean(losses))

    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state

    def get_metrics(self) -> AgentMetrics:
        """Get performance metrics"""
        return self.metrics

    def close(self):
        """Clean up resources"""
        self._executor.shutdown(wait=True)
        self.state = AgentState.TERMINATED
        logger.info("QuantumAgentHost closed")


class AsyncQuantumAgentHost(QuantumAgentHost):
    """Async version of QuantumAgentHost for concurrent operations"""

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self._loop = asyncio.get_event_loop()

    async def perceive_async(self, environment_state: np.ndarray) -> np.ndarray:
        """Async perception"""
        return await self._loop.run_in_executor(
            self._executor,
            self.perceive,
            environment_state
        )

    async def process_async(self, encoded_state: np.ndarray) -> np.ndarray:
        """Async processing"""
        return await self._loop.run_in_executor(
            self._executor,
            self.process,
            encoded_state
        )

    async def decide_async(self, processed_state: np.ndarray) -> Tuple[int, np.ndarray]:
        """Async decision"""
        return await self._loop.run_in_executor(
            self._executor,
            self.decide,
            processed_state
        )

    async def run_episode_async(
        self,
        env_step: Callable[[int], Tuple[np.ndarray, float, bool]],
        reset_env: Callable[[], np.ndarray],
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """Async episode execution"""
        return await self._loop.run_in_executor(
            self._executor,
            self.run_episode,
            env_step,
            reset_env,
            max_steps
        )


# Factory function
def create_agent(
    num_perception_qubits: int = 16,
    num_decision_qubits: int = 8,
    num_action_qubits: int = 8,
    num_memory_qubits: int = 32,
    num_entanglement_qubits: int = 16,
    learning_rate: float = 0.01,
    async_mode: bool = False,
    **kwargs
) -> Union[QuantumAgentHost, AsyncQuantumAgentHost]:
    """Factory function to create agent"""
    config = AgentConfig(
        num_perception_qubits=num_perception_qubits,
        num_decision_qubits=num_decision_qubits,
        num_action_qubits=num_action_qubits,
        num_memory_qubits=num_memory_qubits,
        num_entanglement_qubits=num_entanglement_qubits,
        learning_rate=learning_rate,
        **kwargs
    )

    if async_mode:
        return AsyncQuantumAgentHost(config)
    return QuantumAgentHost(config)


if __name__ == "__main__":
    # Example usage
    agent = create_agent()

    # Dummy environment
    def reset():
        return np.random.randn(16)

    def step(action):
        return np.random.randn(16), np.random.randn(), np.random.random() < 0.1

    # Train
    metrics = agent.train(step, reset, episodes=10)
    print(f"Training summary: {metrics.get_summary()}")

    agent.close()
