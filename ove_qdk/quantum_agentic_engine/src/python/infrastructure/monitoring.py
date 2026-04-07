#!/usr/bin/env python3
"""
Monitoring and Observability for Quantum Agentic Engine
Real-time metrics, logging, and visualization
"""

import numpy as np
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import json
import threading
from pathlib import Path
import logging

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: float
    episode: int
    reward: float
    loss: float
    q_value_mean: float
    epsilon: float
    buffer_size: int
    decision_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'episode': self.episode,
            'reward': self.reward,
            'loss': self.loss,
            'q_value_mean': self.q_value_mean,
            'epsilon': self.epsilon,
            'buffer_size': self.buffer_size,
            'decision_time_ms': self.decision_time_ms
        }


class MetricsCollector:
    """Collect and aggregate metrics"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history = deque(maxlen=10000)

        # Running statistics
        self.episode_rewards = deque(maxlen=window_size)
        self.losses = deque(maxlen=window_size)
        self.q_values = deque(maxlen=window_size)
        self.decision_times = deque(maxlen=window_size)

        self._lock = threading.Lock()

    def record_episode(
        self,
        episode: int,
        reward: float,
        loss: float,
        q_value_mean: float,
        epsilon: float,
        buffer_size: int,
        decision_time_ms: float
    ):
        """Record metrics for an episode"""
        with self._lock:
            snapshot = MetricSnapshot(
                timestamp=time.time(),
                episode=episode,
                reward=reward,
                loss=loss,
                q_value_mean=q_value_mean,
                epsilon=epsilon,
                buffer_size=buffer_size,
                decision_time_ms=decision_time_ms
            )

            self.metrics_history.append(snapshot)
            self.episode_rewards.append(reward)
            self.losses.append(loss)
            self.q_values.append(q_value_mean)
            self.decision_times.append(decision_time_ms)

    def get_summary(self) -> Dict[str, float]:
        """Get summary statistics"""
        with self._lock:
            if not self.episode_rewards:
                return {}

            return {
                'mean_reward': np.mean(self.episode_rewards),
                'std_reward': np.std(self.episode_rewards),
                'min_reward': np.min(self.episode_rewards),
                'max_reward': np.max(self.episode_rewards),
                'mean_loss': np.mean(self.losses) if self.losses else 0,
                'mean_q_value': np.mean(self.q_values) if self.q_values else 0,
                'mean_decision_time_ms': np.mean(self.decision_times) if self.decision_times else 0,
                'total_episodes': len(self.metrics_history)
            }

    def get_recent_metrics(self, n: int = 10) -> List[MetricSnapshot]:
        """Get recent n metrics"""
        with self._lock:
            return list(self.metrics_history)[-n:]

    def export_to_json(self, filepath: str):
        """Export metrics to JSON"""
        with self._lock:
            data = [m.to_dict() for m in self.metrics_history]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

    def clear(self):
        """Clear all metrics"""
        with self._lock:
            self.metrics_history.clear()
            self.episode_rewards.clear()
            self.losses.clear()
            self.q_values.clear()
            self.decision_times.clear()


class PrometheusExporter:
    """Export metrics to Prometheus"""

    def __init__(self, port: int = 8000):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available")
            return

        self.port = port

        # Define metrics
        self.episode_counter = Counter(
            'quantum_agent_episodes_total',
            'Total number of episodes'
        )
        self.reward_histogram = Histogram(
            'quantum_agent_reward',
            'Episode rewards',
            buckets=(-100, -50, -10, -5, 0, 5, 10, 50, 100, 500, 1000)
        )
        self.loss_histogram = Histogram(
            'quantum_agent_loss',
            'Training loss',
            buckets=(0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0)
        )
        self.q_value_gauge = Gauge(
            'quantum_agent_q_value_mean',
            'Mean Q-value'
        )
        self.epsilon_gauge = Gauge(
            'quantum_agent_epsilon',
            'Exploration rate'
        )
        self.buffer_size_gauge = Gauge(
            'quantum_agent_buffer_size',
            'Replay buffer size'
        )
        self.decision_time_histogram = Histogram(
            'quantum_agent_decision_time_ms',
            'Decision time in milliseconds',
            buckets=(0.1, 1, 5, 10, 50, 100, 500)
        )

        # Start server
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")

    def record_episode(self, metrics: MetricSnapshot):
        """Record episode metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.episode_counter.inc()
        self.reward_histogram.observe(metrics.reward)
        self.loss_histogram.observe(metrics.loss)
        self.q_value_gauge.set(metrics.q_value_mean)
        self.epsilon_gauge.set(metrics.epsilon)
        self.buffer_size_gauge.set(metrics.buffer_size)
        self.decision_time_histogram.observe(metrics.decision_time_ms)


class WandbLogger:
    """Log metrics to Weights & Biases"""

    def __init__(
        self,
        project: str = "quantum-agentic-engine",
        entity: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        if not WANDB_AVAILABLE:
            logger.warning("Wandb not available")
            return

        wandb.init(
            project=project,
            entity=entity,
            config=config
        )
        logger.info(f"Wandb initialized: {project}")

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Log metrics to wandb"""
        if not WANDB_AVAILABLE:
            return

        wandb.log(metrics, step=step)

    def log_model(self, model_path: str, name: str = "model"):
        """Log model artifact"""
        if not WANDB_AVAILABLE:
            return

        artifact = wandb.Artifact(name, type="model")
        artifact.add_file(model_path)
        wandb.log_artifact(artifact)

    def finish(self):
        """Finish wandb run"""
        if WANDB_AVAILABLE:
            wandb.finish()


class TensorBoardLogger:
    """Log metrics to TensorBoard"""

    def __init__(self, log_dir: str = "./runs"):
        try:
            from torch.utils.tensorboard import SummaryWriter
            self.writer = SummaryWriter(log_dir)
            self.available = True
            logger.info(f"TensorBoard logging to {log_dir}")
        except ImportError:
            self.available = False
            logger.warning("TensorBoard not available")

    def log_scalar(self, tag: str, value: float, step: int):
        """Log scalar value"""
        if self.available:
            self.writer.add_scalar(tag, value, step)

    def log_scalars(self, tag: str, values: Dict[str, float], step: int):
        """Log multiple scalars"""
        if self.available:
            self.writer.add_scalars(tag, values, step)

    def log_histogram(self, tag: str, values: np.ndarray, step: int):
        """Log histogram"""
        if self.available:
            self.writer.add_histogram(tag, values, step)

    def close(self):
        """Close writer"""
        if self.available:
            self.writer.close()


class ConsoleLogger:
    """Pretty console logging"""

    def __init__(self, log_frequency: int = 10):
        self.log_frequency = log_frequency
        self.start_time = time.time()

    def log_episode(self, episode: int, metrics: MetricSnapshot):
        """Log episode to console"""
        if episode % self.log_frequency != 0:
            return

        elapsed = time.time() - self.start_time
        eps_per_sec = episode / elapsed if elapsed > 0 else 0

        print(
            f"\rEpisode {episode:6d} | "
            f"Reward: {metrics.reward:8.2f} | "
            f"Loss: {metrics.loss:8.4f} | "
            f"Q-mean: {metrics.q_value_mean:7.3f} | "
            f"ε: {metrics.epsilon:.4f} | "
            f"Buffer: {metrics.buffer_size:5d} | "
            f"Time: {metrics.decision_time_ms:6.2f}ms | "
            f"EPS: {eps_per_sec:.2f}",
            end=''
        )

    def log_summary(self, summary: Dict[str, float]):
        """Log summary statistics"""
        print("\n" + "=" * 80)
        print("Training Summary")
        print("=" * 80)
        for key, value in summary.items():
            print(f"  {key:30s}: {value:10.4f}")
        print("=" * 80)


class QuantumStateMonitor:
    """Monitor quantum state during execution"""

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.state_snapshots = deque(maxlen=1000)
        self.entanglement_history = deque(maxlen=1000)

    def record_state(self, state_vector: np.ndarray):
        """Record quantum state snapshot"""
        self.state_snapshots.append({
            'timestamp': time.time(),
            'amplitudes': state_vector.copy(),
            'probabilities': np.abs(state_vector) ** 2
        })

    def record_entanglement(self, bipartition: Tuple[int, int], entropy: float):
        """Record entanglement entropy"""
        self.entanglement_history.append({
            'timestamp': time.time(),
            'bipartition': bipartition,
            'entropy': entropy
        })

    def get_state_evolution(self) -> List[Dict]:
        """Get state evolution over time"""
        return list(self.state_snapshots)

    def get_entanglement_dynamics(self) -> List[Dict]:
        """Get entanglement dynamics"""
        return list(self.entanglement_history)

    def compute_state_statistics(self) -> Dict[str, float]:
        """Compute statistics over state history"""
        if not self.state_snapshots:
            return {}

        probs = [s['probabilities'] for s in self.state_snapshots]

        return {
            'mean_entropy': np.mean([-np.sum(p * np.log2(p + 1e-10)) for p in probs]),
            'mean_purity': np.mean([np.sum(p ** 2) for p in probs]),
            'state_variance': np.mean([np.var(p) for p in probs])
        }


class PerformanceProfiler:
    """Profile performance of quantum operations"""

    def __init__(self):
        self.timings = {}
        self.call_counts = {}
        self._lock = threading.Lock()

    def profile(self, name: str):
        """Decorator to profile a function"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start

                with self._lock:
                    if name not in self.timings:
                        self.timings[name] = []
                        self.call_counts[name] = 0
                    self.timings[name].append(elapsed)
                    self.call_counts[name] += 1

                return result
            return wrapper
        return decorator

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get profiling summary"""
        with self._lock:
            summary = {}
            for name, times in self.timings.items():
                summary[name] = {
                    'total_calls': self.call_counts[name],
                    'total_time': np.sum(times),
                    'mean_time': np.mean(times),
                    'std_time': np.std(times),
                    'min_time': np.min(times),
                    'max_time': np.max(times)
                }
            return summary

    def print_summary(self):
        """Print profiling summary"""
        summary = self.get_summary()

        print("\n" + "=" * 100)
        print("Performance Profile")
        print("=" * 100)
        print(f"{'Function':<30} {'Calls':<10} {'Total (s)':<12} {'Mean (ms)':<12} {'Max (ms)':<12}")
        print("-" * 100)

        for name, stats in sorted(summary.items(), key=lambda x: x[1]['total_time'], reverse=True):
            print(
                f"{name:<30} "
                f"{stats['total_calls']:<10} "
                f"{stats['total_time']:<12.3f} "
                f"{stats['mean_time'] * 1000:<12.3f} "
                f"{stats['max_time'] * 1000:<12.3f}"
            )

        print("=" * 100)

    def reset(self):
        """Reset profiler"""
        with self._lock:
            self.timings.clear()
            self.call_counts.clear()


class MonitoringDashboard:
    """Combined monitoring dashboard"""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        prometheus_port: Optional[int] = 8000,
        wandb_project: Optional[str] = None,
        tensorboard_dir: Optional[str] = None,
        console_log_freq: int = 10
    ):
        self.metrics = metrics_collector

        # Setup exporters
        self.prometheus = None
        if prometheus_port:
            self.prometheus = PrometheusExporter(prometheus_port)

        self.wandb = None
        if wandb_project:
            self.wandb = WandbLogger(project=wandb_project)

        self.tensorboard = None
        if tensorboard_dir:
            self.tensorboard = TensorBoardLogger(tensorboard_dir)

        self.console = ConsoleLogger(console_log_freq)

    def log_episode(self, episode: int, metrics_snapshot: MetricSnapshot):
        """Log episode to all exporters"""
        # Record in collector
        self.metrics.record_episode(
            episode=episode,
            reward=metrics_snapshot.reward,
            loss=metrics_snapshot.loss,
            q_value_mean=metrics_snapshot.q_value_mean,
            epsilon=metrics_snapshot.epsilon,
            buffer_size=metrics_snapshot.buffer_size,
            decision_time_ms=metrics_snapshot.decision_time_ms
        )

        # Export to Prometheus
        if self.prometheus:
            self.prometheus.record_episode(metrics_snapshot)

        # Log to Wandb
        if self.wandb:
            self.wandb.log(metrics_snapshot.to_dict(), step=episode)

        # Log to TensorBoard
        if self.tensorboard:
            self.tensorboard.log_scalar('reward', metrics_snapshot.reward, episode)
            self.tensorboard.log_scalar('loss', metrics_snapshot.loss, episode)
            self.tensorboard.log_scalar('q_value_mean', metrics_snapshot.q_value_mean, episode)
            self.tensorboard.log_scalar('epsilon', metrics_snapshot.epsilon, episode)

        # Console output
        self.console.log_episode(episode, metrics_snapshot)

    def log_summary(self):
        """Log summary statistics"""
        summary = self.metrics.get_summary()
        self.console.log_summary(summary)

    def close(self):
        """Close all exporters"""
        if self.wandb:
            self.wandb.finish()
        if self.tensorboard:
            self.tensorboard.close()


if __name__ == "__main__":
    # Test monitoring
    collector = MetricsCollector()

    # Simulate episodes
    for episode in range(100):
        snapshot = MetricSnapshot(
            timestamp=time.time(),
            episode=episode,
            reward=np.random.randn() * 10,
            loss=np.random.exponential(0.1),
            q_value_mean=np.random.randn(),
            epsilon=max(0.01, 1.0 - episode * 0.01),
            buffer_size=min(10000, episode * 100),
            decision_time_ms=np.random.exponential(5)
        )
        collector.record_episode(
            episode, snapshot.reward, snapshot.loss,
            snapshot.q_value_mean, snapshot.epsilon,
            snapshot.buffer_size, snapshot.decision_time_ms
        )

    print(collector.get_summary())
