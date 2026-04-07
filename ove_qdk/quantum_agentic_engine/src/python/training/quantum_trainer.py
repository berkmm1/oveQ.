#!/usr/bin/env python3
"""
Quantum Training Module
Training loops and optimization for quantum agents
Part of the Quantum Agentic Loop Engine
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
import json
from collections import deque
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingMode(Enum):
    """Training modes"""
    ONLINE = auto()
    OFFLINE = auto()
    BATCH = auto()
    EPISODIC = auto()
    CONTINUOUS = auto()


class OptimizerType(Enum):
    """Optimizer types"""
    SGD = auto()
    ADAM = auto()
    RMSPROP = auto()
    ADAGRAD = auto()
    QUANTUM_NATURAL = auto()


@dataclass
class TrainingConfig:
    """Training configuration"""
    mode: TrainingMode = TrainingMode.EPISODIC
    optimizer: OptimizerType = OptimizerType.ADAM
    learning_rate: float = 0.001
    gamma: float = 0.99
    lambda_gae: float = 0.95
    epsilon_clip: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5
    num_epochs: int = 10
    batch_size: int = 64
    num_workers: int = 4
    save_frequency: int = 100
    log_frequency: int = 10
    eval_frequency: int = 50
    checkpoint_dir: str = "./checkpoints"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mode': self.mode.name,
            'optimizer': self.optimizer.name,
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'lambda_gae': self.lambda_gae,
            'epsilon_clip': self.epsilon_clip,
            'value_coef': self.value_coef,
            'entropy_coef': self.entropy_coef,
            'max_grad_norm': self.max_grad_norm,
            'num_epochs': self.num_epochs,
            'batch_size': self.batch_size,
            'num_workers': self.num_workers,
            'save_frequency': self.save_frequency,
            'log_frequency': self.log_frequency,
            'eval_frequency': self.eval_frequency,
            'checkpoint_dir': self.checkpoint_dir
        }


@dataclass
class TrainingMetrics:
    """Training metrics"""
    episode_rewards: List[float] = field(default_factory=list)
    episode_lengths: List[int] = field(default_factory=list)
    policy_losses: List[float] = field(default_factory=list)
    value_losses: List[float] = field(default_factory=list)
    entropy_losses: List[float] = field(default_factory=list)
    total_losses: List[float] = field(default_factory=list)
    learning_rates: List[float] = field(default_factory=list)

    def get_recent_average(self, metric_name: str, window: int = 100) -> float:
        """Get recent average of a metric"""
        metric = getattr(self, metric_name, [])
        if not metric:
            return 0.0
        recent = metric[-window:] if len(metric) > window else metric
        return np.mean(recent)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'policy_losses': self.policy_losses,
            'value_losses': self.value_losses,
            'entropy_losses': self.entropy_losses,
            'total_losses': self.total_losses,
            'learning_rates': self.learning_rates
        }


class ExperienceBuffer:
    """Buffer for storing and sampling experiences"""

    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.position = 0

    def push(self, experience: Tuple):
        """Add experience to buffer"""
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Tuple]:
        """Sample batch of experiences"""
        if len(self.buffer) < batch_size:
            batch_size = len(self.buffer)
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]

    def get_all(self) -> List[Tuple]:
        """Get all experiences"""
        return list(self.buffer)

    def clear(self):
        """Clear buffer"""
        self.buffer.clear()

    def __len__(self) -> int:
        return len(self.buffer)

    def save(self, filepath: str):
        """Save buffer to file"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(list(self.buffer), f)

    def load(self, filepath: str):
        """Load buffer from file"""
        import pickle
        with open(filepath, 'rb') as f:
            experiences = pickle.load(f)
            self.buffer = deque(experiences, maxlen=self.capacity)


class QuantumOptimizer:
    """Optimizer for quantum parameters"""

    def __init__(self, optimizer_type: OptimizerType, learning_rate: float):
        self.optimizer_type = optimizer_type
        self.learning_rate = learning_rate
        self.iteration = 0

        # Adam parameters
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.epsilon = 1e-8
        self.m = {}
        self.v = {}

        # RMSprop parameters
        self.rms_decay = 0.99
        self.rms_cache = {}

        # Adagrad parameters
        self.adagrad_cache = {}

    def step(self, parameters: np.ndarray, gradients: np.ndarray) -> np.ndarray:
        """Update parameters"""
        param_id = id(parameters)

        if self.optimizer_type == OptimizerType.SGD:
            return parameters - self.learning_rate * gradients

        elif self.optimizer_type == OptimizerType.ADAM:
            if param_id not in self.m:
                self.m[param_id] = np.zeros_like(parameters)
                self.v[param_id] = np.zeros_like(parameters)

            self.m[param_id] = self.beta1 * self.m[param_id] + (1 - self.beta1) * gradients
            self.v[param_id] = self.beta2 * self.v[param_id] + (1 - self.beta2) * (gradients ** 2)

            m_hat = self.m[param_id] / (1 - self.beta1 ** (self.iteration + 1))
            v_hat = self.v[param_id] / (1 - self.beta2 ** (self.iteration + 1))

            self.iteration += 1
            return parameters - self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)

        elif self.optimizer_type == OptimizerType.RMSPROP:
            if param_id not in self.rms_cache:
                self.rms_cache[param_id] = np.zeros_like(parameters)

            self.rms_cache[param_id] = (self.rms_decay * self.rms_cache[param_id] +
                                       (1 - self.rms_decay) * gradients ** 2)

            return parameters - self.learning_rate * gradients / (np.sqrt(self.rms_cache[param_id]) + self.epsilon)

        elif self.optimizer_type == OptimizerType.ADAGRAD:
            if param_id not in self.adagrad_cache:
                self.adagrad_cache[param_id] = np.zeros_like(parameters)

            self.adagrad_cache[param_id] += gradients ** 2

            return parameters - self.learning_rate * gradients / (np.sqrt(self.adagrad_cache[param_id]) + self.epsilon)

        elif self.optimizer_type == OptimizerType.QUANTUM_NATURAL:
            # Simplified quantum natural gradient
            return parameters - self.learning_rate * gradients * 2.0

        else:
            return parameters - self.learning_rate * gradients

    def get_learning_rate(self) -> float:
        """Get current learning rate"""
        return self.learning_rate

    def set_learning_rate(self, lr: float):
        """Set learning rate"""
        self.learning_rate = lr


class QuantumTrainer:
    """Main training class for quantum agents"""

    def __init__(self, agent: Any, environment: Any, config: TrainingConfig):
        self.agent = agent
        self.environment = environment
        self.config = config

        # Optimizers
        self.policy_optimizer = QuantumOptimizer(
            config.optimizer,
            config.learning_rate
        )
        self.value_optimizer = QuantumOptimizer(
            config.optimizer,
            config.learning_rate
        )

        # Experience buffer
        self.buffer = ExperienceBuffer(capacity=100000)

        # Metrics
        self.metrics = TrainingMetrics()

        # Training state
        self.episode_count = 0
        self.step_count = 0
        self.best_reward = -np.inf
        self.running_reward = 0.0

        # Threading
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=config.num_workers)

        # Checkpointing
        Path(config.checkpoint_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"QuantumTrainer initialized with {config.optimizer.name} optimizer")

    def collect_episode(self, render: bool = False) -> Dict[str, Any]:
        """Collect one episode of experience"""
        observation = self.environment.reset()
        episode_data = {
            'observations': [],
            'actions': [],
            'rewards': [],
            'values': [],
            'log_probs': [],
            'dones': []
        }

        episode_reward = 0.0
        done = False
        step = 0

        while not done and step < 1000:
            # Get action from agent
            if hasattr(self.agent, 'select_action'):
                action, value, log_prob = self.agent.select_action(observation)
            else:
                action = self.agent.decide(observation)
                value = 0.0
                log_prob = 0.0

            # Execute action
            next_observation, reward, done, info = self.environment.step(action)

            # Store experience
            episode_data['observations'].append(observation)
            episode_data['actions'].append(action)
            episode_data['rewards'].append(reward)
            episode_data['values'].append(value)
            episode_data['log_probs'].append(log_prob)
            episode_data['dones'].append(done)

            episode_reward += reward
            observation = next_observation
            step += 1

            if render:
                self.environment.render()

        episode_data['episode_reward'] = episode_reward
        episode_data['episode_length'] = step

        return episode_data

    def compute_gae(self, rewards: List[float], values: List[float],
                    dones: List[bool]) -> Tuple[List[float], List[float]]:
        """Compute Generalized Advantage Estimation"""
        advantages = []
        returns = []

        gae = 0.0
        next_value = 0.0

        for t in reversed(range(len(rewards))):
            if dones[t]:
                next_value = 0.0

            delta = rewards[t] + self.config.gamma * next_value - values[t]
            gae = delta + self.config.gamma * self.config.lambda_gae * gae

            advantages.insert(0, gae)
            returns.insert(0, gae + values[t])

            next_value = values[t]

        return advantages, returns

    def update_policy(self, batch: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Update policy using PPO"""
        # This is a simplified version
        observations = batch['observations']
        actions = batch['actions']
        old_log_probs = batch['log_probs']
        advantages = batch['advantages']
        returns = batch['returns']

        policy_loss = 0.0
        value_loss = 0.0
        entropy_loss = 0.0

        for epoch in range(self.config.num_epochs):
            # Compute new log probs and values
            if hasattr(self.agent, 'evaluate'):
                new_log_probs, values, entropy = self.agent.evaluate(observations, actions)
            else:
                # Simplified evaluation
                new_log_probs = old_log_probs
                values = returns
                entropy = 0.1

            # Compute ratio
            ratio = np.exp(new_log_probs - old_log_probs)

            # Clipped surrogate objective
            surr1 = ratio * advantages
            surr2 = np.clip(ratio, 1 - self.config.epsilon_clip,
                          1 + self.config.epsilon_clip) * advantages

            policy_loss_epoch = -np.mean(np.minimum(surr1, surr2))
            value_loss_epoch = np.mean((returns - values) ** 2)
            entropy_loss_epoch = -np.mean(entropy)

            # Total loss
            total_loss = (policy_loss_epoch +
                         self.config.value_coef * value_loss_epoch +
                         self.config.entropy_coef * entropy_loss_epoch)

            # Update (simplified - would use actual backprop)
            policy_loss += policy_loss_epoch
            value_loss += value_loss_epoch
            entropy_loss += entropy_loss_epoch

        num_batches = self.config.num_epochs

        return {
            'policy_loss': policy_loss / num_batches,
            'value_loss': value_loss / num_batches,
            'entropy_loss': entropy_loss / num_batches,
            'total_loss': (policy_loss + value_loss + entropy_loss) / num_batches
        }

    def train_episode(self) -> float:
        """Train for one episode"""
        # Collect episode
        episode_data = self.collect_episode()

        episode_reward = episode_data['episode_reward']
        episode_length = episode_data['episode_length']

        # Compute GAE
        advantages, returns = self.compute_gae(
            episode_data['rewards'],
            episode_data['values'],
            episode_data['dones']
        )

        # Normalize advantages
        advantages = np.array(advantages)
        advantages = (advantages - np.mean(advantages)) / (np.std(advantages) + 1e-8)

        # Prepare batch
        batch = {
            'observations': np.array(episode_data['observations']),
            'actions': np.array(episode_data['actions']),
            'old_log_probs': np.array(episode_data['log_probs']),
            'advantages': advantages,
            'returns': np.array(returns)
        }

        # Update policy
        losses = self.update_policy(batch)

        # Update metrics
        with self.lock:
            self.metrics.episode_rewards.append(episode_reward)
            self.metrics.episode_lengths.append(episode_length)
            self.metrics.policy_losses.append(losses['policy_loss'])
            self.metrics.value_losses.append(losses['value_loss'])
            self.metrics.entropy_losses.append(losses['entropy_loss'])
            self.metrics.total_losses.append(losses['total_loss'])

            self.episode_count += 1
            self.step_count += episode_length

            # Update running reward
            self.running_reward = 0.05 * episode_reward + 0.95 * self.running_reward

            # Track best reward
            if episode_reward > self.best_reward:
                self.best_reward = episode_reward

        return episode_reward

    def train(self, num_episodes: int = 1000, render: bool = False):
        """Main training loop"""
        logger.info(f"Starting training for {num_episodes} episodes")

        start_time = time.time()

        for episode in range(num_episodes):
            # Train episode
            episode_reward = self.train_episode()

            # Logging
            if episode % self.config.log_frequency == 0:
                elapsed = time.time() - start_time
                fps = self.step_count / elapsed if elapsed > 0 else 0

                avg_reward = self.metrics.get_recent_average('episode_rewards', 100)
                avg_length = self.metrics.get_recent_average('episode_lengths', 100)

                logger.info(
                    f"Episode {episode}/{num_episodes} | "
                    f"Reward: {episode_reward:.2f} | "
                    f"Avg Reward: {avg_reward:.2f} | "
                    f"Avg Length: {avg_length:.1f} | "
                    f"FPS: {fps:.1f}"
                )

            # Evaluation
            if episode % self.config.eval_frequency == 0 and episode > 0:
                eval_reward = self.evaluate(num_episodes=5)
                logger.info(f"Evaluation reward: {eval_reward:.2f}")

            # Checkpointing
            if episode % self.config.save_frequency == 0 and episode > 0:
                self.save_checkpoint(episode)

        # Final save
        self.save_checkpoint(num_episodes)

        total_time = time.time() - start_time
        logger.info(f"Training completed in {total_time:.1f}s")

    def evaluate(self, num_episodes: int = 10) -> float:
        """Evaluate agent performance"""
        rewards = []

        for _ in range(num_episodes):
            episode_data = self.collect_episode(render=False)
            rewards.append(episode_data['episode_reward'])

        return np.mean(rewards)

    def save_checkpoint(self, episode: int):
        """Save training checkpoint"""
        checkpoint = {
            'episode': episode,
            'step_count': self.step_count,
            'best_reward': self.best_reward,
            'running_reward': self.running_reward,
            'metrics': self.metrics.to_dict(),
            'config': self.config.to_dict()
        }

        filepath = Path(self.config.checkpoint_dir) / f"checkpoint_{episode}.json"
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Checkpoint saved: {filepath}")

    def load_checkpoint(self, filepath: str):
        """Load training checkpoint"""
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)

        self.episode_count = checkpoint['episode']
        self.step_count = checkpoint['step_count']
        self.best_reward = checkpoint['best_reward']
        self.running_reward = checkpoint['running_reward']

        # Restore metrics
        metrics_data = checkpoint['metrics']
        self.metrics = TrainingMetrics(
            episode_rewards=metrics_data['episode_rewards'],
            episode_lengths=metrics_data['episode_lengths'],
            policy_losses=metrics_data['policy_losses'],
            value_losses=metrics_data['value_losses'],
            entropy_losses=metrics_data['entropy_losses'],
            total_losses=metrics_data['total_losses'],
            learning_rates=metrics_data.get('learning_rates', [])
        )

        logger.info(f"Checkpoint loaded: {filepath}")

    def get_training_summary(self) -> Dict[str, Any]:
        """Get training summary"""
        return {
            'total_episodes': self.episode_count,
            'total_steps': self.step_count,
            'best_reward': self.best_reward,
            'final_running_reward': self.running_reward,
            'average_reward': np.mean(self.metrics.episode_rewards) if self.metrics.episode_rewards else 0,
            'average_length': np.mean(self.metrics.episode_lengths) if self.metrics.episode_lengths else 0,
            'metrics': self.metrics.to_dict()
        }


class DistributedQuantumTrainer:
    """Distributed training across multiple agents"""

    def __init__(self, agent_manager: Any, config: TrainingConfig):
        self.agent_manager = agent_manager
        self.config = config
        self.trainers: Dict[str, QuantumTrainer] = {}

    def create_trainers(self, environment_factory: Callable):
        """Create trainers for all agents"""
        for agent_id, agent in self.agent_manager.get_all_agents().items():
            env = environment_factory()
            trainer = QuantumTrainer(agent, env, self.config)
            self.trainers[agent_id] = trainer

    def train_parallel(self, num_episodes: int = 1000):
        """Train all agents in parallel"""
        futures = []

        with ThreadPoolExecutor(max_workers=len(self.trainers)) as executor:
            for agent_id, trainer in self.trainers.items():
                future = executor.submit(trainer.train, num_episodes)
                futures.append((agent_id, future))

            for agent_id, future in futures:
                try:
                    future.result()
                    logger.info(f"Agent {agent_id} training completed")
                except Exception as e:
                    logger.error(f"Agent {agent_id} training failed: {e}")

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all trainers"""
        all_rewards = []

        for trainer in self.trainers.values():
            all_rewards.extend(trainer.metrics.episode_rewards)

        return {
            'num_agents': len(self.trainers),
            'total_episodes': sum(t.episode_count for t in self.trainers.values()),
            'average_reward': np.mean(all_rewards) if all_rewards else 0,
            'best_reward': max(t.best_reward for t in self.trainers.values()) if self.trainers else 0
        }


# Utility functions
def create_default_trainer(agent: Any, environment: Any) -> QuantumTrainer:
    """Create trainer with default configuration"""
    config = TrainingConfig()
    return QuantumTrainer(agent, environment, config)


def train_agent(agent: Any, environment: Any, num_episodes: int = 1000,
                **kwargs) -> Dict[str, Any]:
    """Quick training function"""
    config = TrainingConfig(**kwargs)
    trainer = QuantumTrainer(agent, environment, config)
    trainer.train(num_episodes)
    return trainer.get_training_summary()


if __name__ == "__main__":
    print("Quantum Training Module")
    print("=" * 40)

    # Example usage with dummy agent and environment
    class DummyAgent:
        def select_action(self, obs):
            return np.random.randint(4), 0.0, 0.0

        def evaluate(self, obs, actions):
            return np.zeros(len(obs)), np.zeros(len(obs)), np.ones(len(obs)) * 0.1

    class DummyEnv:
        def reset(self):
            return np.zeros(8)
        def step(self, action):
            return np.zeros(8), np.random.randn(), False, {}

    agent = DummyAgent()
    env = DummyEnv()

    trainer = create_default_trainer(agent, env)
    print(f"Trainer created with config: {trainer.config.to_dict()}")
