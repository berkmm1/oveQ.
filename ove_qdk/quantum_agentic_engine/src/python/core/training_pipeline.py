#!/usr/bin/env python3
"""
Training Pipeline for Quantum Agentic Engine
Orchestrates training, evaluation, and model management
"""

import numpy as np
import json
import pickle
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from tqdm import tqdm
import threading
import queue

from agent_host import QuantumAgentHost, AgentConfig, create_agent
from environment_interface import QuantumEnvironment, create_environment

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training configuration"""
    num_episodes: int = 1000
    max_steps_per_episode: int = 1000
    eval_frequency: int = 50
    save_frequency: int = 100
    batch_size: int = 32
    warmup_steps: int = 1000

    # Logging
    log_frequency: int = 10
    tensorboard: bool = False

    # Checkpointing
    checkpoint_dir: str = "./checkpoints"
    keep_last_n: int = 5

    # Early stopping
    early_stopping: bool = True
    patience: int = 50
    min_delta: float = 0.01

    # Distributed training
    num_workers: int = 1
    async_training: bool = False


@dataclass
class TrainingStats:
    """Training statistics"""
    episode_rewards: List[float]
    episode_lengths: List[int]
    eval_rewards: List[float]
    losses: List[float]
    q_values: List[float]
    epsilons: List[float]
    training_time: float = 0.0
    best_reward: float = -float('inf')
    best_episode: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'TrainingStats':
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


class TrainingPipeline:
    """Main training pipeline"""

    def __init__(
        self,
        agent: QuantumAgentHost,
        env: QuantumEnvironment,
        config: TrainingConfig
    ):
        self.agent = agent
        self.env = env
        self.config = config

        self.stats = TrainingStats(
            episode_rewards=[],
            episode_lengths=[],
            eval_rewards=[],
            losses=[],
            q_values=[],
            epsilons=[]
        )

        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.best_model_path = self.checkpoint_dir / "best_model.pkl"
        self._stop_training = False

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration"""
        log_file = self.checkpoint_dir / f"training_{datetime.now():%Y%m%d_%H%M%S}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.info("Training pipeline initialized")

    def train(self) -> TrainingStats:
        """Run complete training loop"""
        logger.info(f"Starting training for {self.config.num_episodes} episodes")

        start_time = time.time()
        episodes_without_improvement = 0

        for episode in tqdm(range(self.config.num_episodes), desc="Training"):
            if self._stop_training:
                logger.info("Training stopped by user")
                break

            # Run episode
            episode_stats = self._run_episode()

            # Update stats
            self.stats.episode_rewards.append(episode_stats['reward'])
            self.stats.episode_lengths.append(episode_stats['length'])
            self.stats.epsilons.append(episode_stats['epsilon'])

            # Check for improvement
            if episode_stats['reward'] > self.stats.best_reward + self.config.min_delta:
                self.stats.best_reward = episode_stats['reward']
                self.stats.best_episode = episode
                episodes_without_improvement = 0
                self._save_best_model()
            else:
                episodes_without_improvement += 1

            # Logging
            if episode % self.config.log_frequency == 0:
                self._log_progress(episode)

            # Evaluation
            if episode % self.config.eval_frequency == 0 and episode > 0:
                eval_reward = self.evaluate(num_episodes=5)
                self.stats.eval_rewards.append(eval_reward)
                logger.info(f"Episode {episode}: Eval reward = {eval_reward:.2f}")

            # Checkpointing
            if episode % self.config.save_frequency == 0:
                self._save_checkpoint(episode)

            # Early stopping
            if self.config.early_stopping and episodes_without_improvement >= self.config.patience:
                logger.info(f"Early stopping triggered after {episode} episodes")
                break

        self.stats.training_time = time.time() - start_time

        # Final save
        self._save_final_stats()

        logger.info(f"Training complete. Best reward: {self.stats.best_reward:.2f} "
                   f"at episode {self.stats.best_episode}")

        return self.stats

    def _run_episode(self) -> Dict[str, Any]:
        """Run single episode"""
        state = self.env.reset()
        episode_reward = 0.0
        episode_length = 0

        for step in range(self.config.max_steps_per_episode):
            # Agent step
            encoded_state = self.agent.perceive(state)
            processed = self.agent.process(encoded_state)
            action, q_values = self.agent.decide(processed)

            # Environment step
            next_state, reward, done, info = self.env.step(action)

            # Store experience
            from agent_host import Experience
            exp = Experience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done
            )
            self.agent.replay_buffer.add(exp)

            # Learn
            if len(self.agent.replay_buffer) >= self.agent.config.batch_size:
                train_result = self.agent.learn()
                if 'loss' in train_result:
                    self.stats.losses.append(train_result['loss'])

            episode_reward += reward
            episode_length += 1
            state = next_state

            if done:
                break

        return {
            'reward': episode_reward,
            'length': episode_length,
            'epsilon': self.agent.epsilon
        }

    def evaluate(self, num_episodes: int = 10) -> float:
        """Evaluate agent performance"""
        logger.info(f"Evaluating for {num_episodes} episodes")

        eval_rewards = []

        for _ in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0.0

            for step in range(self.config.max_steps_per_episode):
                # Greedy action selection
                encoded_state = self.agent.perceive(state)
                processed = self.agent.process(encoded_state)
                action, _ = self.agent.decide(processed)

                state, reward, done, _ = self.env.step(action)
                episode_reward += reward

                if done:
                    break

            eval_rewards.append(episode_reward)

        return float(np.mean(eval_rewards))

    def _log_progress(self, episode: int):
        """Log training progress"""
        recent_rewards = self.stats.episode_rewards[-100:]
        mean_reward = np.mean(recent_rewards) if recent_rewards else 0

        logger.info(
            f"Episode {episode}: "
            f"Mean Reward = {mean_reward:.2f}, "
            f"Epsilon = {self.agent.epsilon:.4f}, "
            f"Buffer = {len(self.agent.replay_buffer)}"
        )

    def _save_checkpoint(self, episode: int):
        """Save training checkpoint"""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{episode}.pkl"

        checkpoint = {
            'episode': episode,
            'agent_config': self.agent.config.__dict__,
            'epsilon': self.agent.epsilon,
            'stats': self.stats.to_dict()
        }

        with open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint, f)

        logger.info(f"Checkpoint saved: {checkpoint_path}")

        # Clean old checkpoints
        self._clean_old_checkpoints()

    def _save_best_model(self):
        """Save best model"""
        best_model = {
            'agent_config': self.agent.config.__dict__,
            'epsilon': self.agent.epsilon,
            'best_reward': self.stats.best_reward,
            'best_episode': self.stats.best_episode
        }

        with open(self.best_model_path, 'wb') as f:
            pickle.dump(best_model, f)

        logger.info(f"Best model saved: {self.best_model_path}")

    def _clean_old_checkpoints(self):
        """Remove old checkpoints, keeping only last N"""
        checkpoints = sorted(
            self.checkpoint_dir.glob("checkpoint_*.pkl"),
            key=lambda p: p.stat().st_mtime
        )

        while len(checkpoints) > self.config.keep_last_n:
            old_checkpoint = checkpoints.pop(0)
            old_checkpoint.unlink()
            logger.debug(f"Removed old checkpoint: {old_checkpoint}")

    def _save_final_stats(self):
        """Save final training statistics"""
        stats_path = self.checkpoint_dir / "training_stats.json"
        self.stats.save(stats_path)

        # Plot training curves
        self._plot_training_curves()

        logger.info(f"Final stats saved: {stats_path}")

    def _plot_training_curves(self):
        """Plot and save training curves"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Episode rewards
        ax = axes[0, 0]
        ax.plot(self.stats.episode_rewards, alpha=0.3, label='Raw')
        if len(self.stats.episode_rewards) >= 100:
            smoothed = np.convolve(
                self.stats.episode_rewards,
                np.ones(100) / 100,
                mode='valid'
            )
            ax.plot(smoothed, label='Smoothed (100)')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Reward')
        ax.set_title('Episode Rewards')
        ax.legend()
        ax.grid(True)

        # Episode lengths
        ax = axes[0, 1]
        ax.plot(self.stats.episode_lengths)
        ax.set_xlabel('Episode')
        ax.set_ylabel('Length')
        ax.set_title('Episode Lengths')
        ax.grid(True)

        # Losses
        if self.stats.losses:
            ax = axes[1, 0]
            ax.plot(self.stats.losses)
            ax.set_xlabel('Training Step')
            ax.set_ylabel('Loss')
            ax.set_title('Training Loss')
            ax.grid(True)

        # Epsilon decay
        ax = axes[1, 1]
        ax.plot(self.stats.epsilons)
        ax.set_xlabel('Episode')
        ax.set_ylabel('Epsilon')
        ax.set_title('Exploration Rate')
        ax.grid(True)

        plt.tight_layout()
        plot_path = self.checkpoint_dir / "training_curves.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()

        logger.info(f"Training curves saved: {plot_path}")

    def stop(self):
        """Signal training to stop"""
        self._stop_training = True

    def load_checkpoint(self, checkpoint_path: str):
        """Load from checkpoint"""
        with open(checkpoint_path, 'rb') as f:
            checkpoint = pickle.load(f)

        self.agent.epsilon = checkpoint['epsilon']
        self.stats = TrainingStats(**checkpoint['stats'])

        logger.info(f"Checkpoint loaded: {checkpoint_path}")


class DistributedTrainingPipeline(TrainingPipeline):
    """Distributed training with multiple workers"""

    def __init__(
        self,
        agent: QuantumAgentHost,
        env_factory: Callable[[], QuantumEnvironment],
        config: TrainingConfig
    ):
        super().__init__(agent, env_factory(), config)
        self.env_factory = env_factory
        self.experience_queue = queue.Queue(maxsize=1000)
        self.worker_threads = []

    def _start_workers(self):
        """Start worker threads"""
        for i in range(self.config.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,)
            )
            worker.start()
            self.worker_threads.append(worker)

    def _worker_loop(self, worker_id: int):
        """Worker thread loop"""
        env = self.env_factory()

        while not self._stop_training:
            # Collect experiences
            state = env.reset()

            for _ in range(self.config.max_steps_per_episode):
                if self._stop_training:
                    break

                # Get action from agent (thread-safe)
                with self.agent._lock:
                    encoded_state = self.agent.perceive(state)
                    processed = self.agent.process(encoded_state)
                    action, _ = self.agent.decide(processed)

                # Execute action
                next_state, reward, done, _ = env.step(action)

                # Add to queue
                from agent_host import Experience
                exp = Experience(
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                    done=done
                )

                try:
                    self.experience_queue.put(exp, timeout=1)
                except queue.Full:
                    pass

                state = next_state

                if done:
                    break

    def train(self) -> TrainingStats:
        """Run distributed training"""
        logger.info(f"Starting distributed training with {self.config.num_workers} workers")

        # Start workers
        self._start_workers()

        # Main training loop
        start_time = time.time()

        for episode in range(self.config.num_episodes):
            if self._stop_training:
                break

            # Process experiences from queue
            experiences = []
            while len(experiences) < self.config.batch_size:
                try:
                    exp = self.experience_queue.get(timeout=0.1)
                    experiences.append(exp)
                except queue.Empty:
                    break

            # Add to replay buffer
            for exp in experiences:
                self.agent.replay_buffer.add(exp)

            # Learn
            if len(self.agent.replay_buffer) >= self.agent.config.batch_size:
                self.agent.learn()

            # Periodic evaluation and logging
            if episode % self.config.eval_frequency == 0:
                eval_reward = self.evaluate()
                logger.info(f"Episode {episode}: Eval reward = {eval_reward:.2f}")

        # Stop workers
        self._stop_training = True
        for worker in self.worker_threads:
            worker.join()

        self.stats.training_time = time.time() - start_time
        return self.stats


def create_training_pipeline(
    env_type: str,
    env_kwargs: Dict[str, Any],
    agent_kwargs: Dict[str, Any],
    training_kwargs: Dict[str, Any]
) -> TrainingPipeline:
    """Factory function to create training pipeline"""

    # Create environment
    env = create_environment(env_type, **env_kwargs)

    # Create agent
    agent_config = AgentConfig(**agent_kwargs)
    agent = create_agent(**agent_kwargs)

    # Create training config
    training_config = TrainingConfig(**training_kwargs)

    # Create pipeline
    return TrainingPipeline(agent, env, training_config)


if __name__ == "__main__":
    # Example training run
    pipeline = create_training_pipeline(
        env_type="gridworld",
        env_kwargs={"size": 8},
        agent_kwargs={
            "num_perception_qubits": 128,
            "num_decision_qubits": 64,
            "num_action_qubits": 4,
            "learning_rate": 0.001
        },
        training_kwargs={
            "num_episodes": 100,
            "max_steps_per_episode": 200,
            "eval_frequency": 20
        }
    )

    stats = pipeline.train()
    print(f"Training complete! Best reward: {stats.best_reward}")
