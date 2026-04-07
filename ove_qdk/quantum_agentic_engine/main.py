#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Main Entry Point
QDK (Q#) Based Autonomous Agent System

This is the main entry point for the Quantum Agentic Loop Engine,
a comprehensive quantum-classical hybrid system for autonomous agents.
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version info
__version__ = "1.0.0"
__author__ = "Quantum Agentic Engine Team"


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗████████╗██╗   ██╗███╗   ███╗      ║
    ║    ██╔═══██╗██║   ██║██╔══██╗████╗  ██║╚══██╔══╝██║   ██║████╗ ████║      ║
    ║    ██║   ██║██║   ██║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║      ║
    ║    ██║▄▄ ██║██║   ██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║      ║
    ║    ╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║      ║
    ║     ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝      ║
    ║                                                                           ║
    ║              A G E N T I C   L O O P   E N G I N E                       ║
    ║                                                                           ║
    ║                    QDK (Q#) Quantum Implementation                        ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝

    Version: {version}
    Author:  {author}

    A comprehensive quantum-classical hybrid system featuring:
    - Quantum Neural Networks with Variational Circuits
    - Quantum Reinforcement Learning (QRL)
    - Multi-Agent Quantum Coordination
    - Quantum Error Correction
    - Real-time Monitoring & Visualization
    """
    print(banner.format(version=__version__, author=__author__))


def create_default_config() -> Dict[str, Any]:
    """Create default configuration"""
    return {
        "agent": {
            "num_perception_qubits": 16,
            "num_decision_qubits": 8,
            "num_action_qubits": 8,
            "num_memory_qubits": 32,
            "num_entanglement_qubits": 16,
            "learning_rate": 0.01,
            "discount_factor": 0.95,
            "exploration_rate": 1.0,
            "epsilon_decay": 0.995,
            "epsilon_min": 0.01,
            "buffer_size": 10000,
            "batch_size": 32
        },
        "environment": {
            "type": "gridworld",
            "size": 8,
            "max_steps": 200,
            "reward_scale": 1.0,
            "normalize_observations": True,
            "quantum_encode": True
        },
        "training": {
            "num_episodes": 1000,
            "max_steps_per_episode": 200,
            "eval_frequency": 50,
            "save_frequency": 100,
            "log_frequency": 10,
            "early_stopping": True,
            "patience": 50,
            "checkpoint_dir": "./checkpoints"
        },
        "monitoring": {
            "prometheus_port": 8000,
            "tensorboard_dir": "./runs",
            "wandb_project": None,
            "console_log_freq": 10
        },
        "quantum": {
            "error_correction": True,
            "error_rate": 0.001,
            "noise_mitigation": True,
            "circuit_depth": 8,
            "entanglement_pattern": "linear"
        }
    }


def save_config(config: Dict[str, Any], filepath: str):
    """Save configuration to file"""
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration saved to {filepath}")


def load_config(filepath: str) -> Dict[str, Any]:
    """Load configuration from file"""
    with open(filepath, 'r') as f:
        config = json.load(f)
    logger.info(f"Configuration loaded from {filepath}")
    return config


def train_command(args):
    """Execute training command"""
    logger.info("Starting training mode")

    # Load or create config
    if args.config:
        config = load_config(args.config)
    else:
        config = create_default_config()
        if args.save_config:
            save_config(config, args.save_config)

    # Override with command line arguments
    if args.episodes:
        config['training']['num_episodes'] = args.episodes
    if args.checkpoint_dir:
        config['training']['checkpoint_dir'] = args.checkpoint_dir

    try:
        # Import training pipeline
        from src.python.core.training_pipeline import create_training_pipeline

        # Create pipeline
        pipeline = create_training_pipeline(
            env_type=config['environment']['type'],
            env_kwargs={k: v for k, v in config['environment'].items() if k != 'type'},
            agent_kwargs=config['agent'],
            training_kwargs=config['training']
        )

        # Train
        stats = pipeline.train()

        logger.info("Training completed successfully")
        logger.info(f"Best reward: {stats.best_reward:.2f}")
        logger.info(f"Total training time: {stats.training_time:.2f}s")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


def evaluate_command(args):
    """Execute evaluation command"""
    logger.info("Starting evaluation mode")

    if not args.checkpoint:
        logger.error("Checkpoint required for evaluation")
        sys.exit(1)

    try:
        # Load checkpoint
        import pickle
        with open(args.checkpoint, 'rb') as f:
            checkpoint = pickle.load(f)

        # Create agent
        from src.python.core.agent_host import QuantumAgentHost, AgentConfig
        agent_config = AgentConfig(**checkpoint['agent_config'])
        agent = QuantumAgentHost(agent_config)
        agent.epsilon = 0  # No exploration during evaluation

        # Create environment
        from src.python.core.environment_interface import create_environment
        env = create_environment(args.env_type or 'gridworld', size=8)

        # Evaluate
        total_reward = 0
        for episode in range(args.episodes or 10):
            state = env.reset()
            episode_reward = 0
            done = False
            steps = 0

            while not done and steps < 1000:
                encoded_state = agent.perceive(state)
                processed = agent.process(encoded_state)
                action, _ = agent.decide(processed)
                state, reward, done, _ = env.step(action)
                episode_reward += reward
                steps += 1

            total_reward += episode_reward
            logger.info(f"Episode {episode + 1}: Reward = {episode_reward:.2f}, Steps = {steps}")

        avg_reward = total_reward / (args.episodes or 10)
        logger.info(f"Average reward: {avg_reward:.2f}")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


def demo_command(args):
    """Execute demo command"""
    logger.info("Starting demo mode")

    try:
        # Create simple demo environment
        from src.python.core.environment_interface import GridWorldEnvironment, EnvironmentConfig

        env = GridWorldEnvironment(
            size=args.size or 5,
            config=EnvironmentConfig(max_steps=100)
        )

        # Run random agent demo
        state = env.reset()
        total_reward = 0
        done = False
        steps = 0

        print("\nRunning demo episode with random agent:")
        print("-" * 50)

        while not done and steps < 100:
            action = np.random.randint(0, env.get_action_dim())
            state, reward, done, info = env.step(action)
            total_reward += reward
            steps += 1

            if steps % 10 == 0:
                print(f"Step {steps}: Reward = {total_reward:.2f}")

        print("-" * 50)
        print(f"Demo complete: Total reward = {total_reward:.2f}, Steps = {steps}")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


def monitor_command(args):
    """Execute monitoring command"""
    logger.info("Starting monitoring server")

    try:
        from src.python.infrastructure.monitoring import MetricsCollector, MonitoringDashboard

        collector = MetricsCollector()
        dashboard = MonitoringDashboard(
            metrics_collector=collector,
            prometheus_port=args.prometheus_port or 8000,
            tensorboard_dir=args.tensorboard_dir or './runs'
        )

        print(f"\nMonitoring server started:")
        print(f"  - Prometheus: http://localhost:{args.prometheus_port or 8000}/metrics")
        print(f"  - TensorBoard: tensorboard --logdir={args.tensorboard_dir or './runs'}")
        print("\nPress Ctrl+C to stop")

        # Keep running
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nMonitoring server stopped")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise


def benchmark_command(args):
    """Execute benchmark command"""
    logger.info("Starting benchmark mode")

    try:
        import time

        print("\n" + "=" * 60)
        print("Quantum Agentic Engine Benchmark")
        print("=" * 60)

        # Benchmark 1: Quantum state encoding
        print("\n1. Quantum State Encoding Benchmark")
        print("-" * 60)

        from src.python.utils.quantum_utils import QuantumStateEncoder

        encoder = QuantumStateEncoder()
        data = np.random.randn(1000)

        start = time.perf_counter()
        for _ in range(1000):
            encoder.angle_encoding(data)
        angle_time = (time.perf_counter() - start) / 1000 * 1000

        start = time.perf_counter()
        for _ in range(1000):
            encoder.amplitude_encoding(data)
        amp_time = (time.perf_counter() - start) / 1000 * 1000

        print(f"  Angle encoding:    {angle_time:.3f} ms/op")
        print(f"  Amplitude encoding: {amp_time:.3f} ms/op")

        # Benchmark 2: Circuit building
        print("\n2. Quantum Circuit Building Benchmark")
        print("-" * 60)

        from src.python.utils.quantum_utils import QuantumCircuitBuilder

        builder = QuantumCircuitBuilder(16)
        params = np.random.randn(48)

        start = time.perf_counter()
        for _ in range(100):
            builder.build_variational_layer(params)
        circuit_time = (time.perf_counter() - start) / 100 * 1000

        print(f"  Variational layer: {circuit_time:.3f} ms/op")

        # Benchmark 3: Gradient estimation
        print("\n3. Gradient Estimation Benchmark")
        print("-" * 60)

        from src.python.utils.quantum_utils import QuantumGradientEstimator

        estimator = QuantumGradientEstimator()
        params = np.random.randn(10)

        def dummy_circuit(p):
            return np.sum(p ** 2)

        start = time.perf_counter()
        for _ in range(100):
            estimator.parameter_shift(dummy_circuit, params)
        grad_time = (time.perf_counter() - start) / 100 * 1000

        print(f"  Parameter shift:   {grad_time:.3f} ms/op")

        # Benchmark 4: Environment simulation
        print("\n4. Environment Simulation Benchmark")
        print("-" * 60)

        from src.python.core.environment_interface import GridWorldEnvironment

        env = GridWorldEnvironment(size=8)

        start = time.perf_counter()
        for _ in range(100):
            state = env.reset()
            for _ in range(100):
                action = np.random.randint(0, 4)
                state, _, done, _ = env.step(action)
                if done:
                    break
        env_time = (time.perf_counter() - start) / 100 * 1000

        print(f"  Episode simulation: {env_time:.3f} ms/episode")

        print("\n" + "=" * 60)
        print("Benchmark complete")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Quantum Agentic Loop Engine - QDK (Q#) Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train a new agent
  python main.py train --episodes 1000 --checkpoint-dir ./checkpoints

  # Evaluate a trained agent
  python main.py evaluate --checkpoint checkpoints/best_model.pkl

  # Run demo
  python main.py demo --size 5

  # Start monitoring server
  python main.py monitor --prometheus-port 8000

  # Run benchmarks
  python main.py benchmark
        """
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train a quantum agent')
    train_parser.add_argument('--config', '-c', type=str, help='Configuration file')
    train_parser.add_argument('--save-config', '-s', type=str, help='Save default config to file')
    train_parser.add_argument('--episodes', '-e', type=int, help='Number of training episodes')
    train_parser.add_argument('--checkpoint-dir', type=str, help='Checkpoint directory')

    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate a trained agent')
    eval_parser.add_argument('--checkpoint', '-c', type=str, required=True, help='Checkpoint file')
    eval_parser.add_argument('--episodes', '-e', type=int, help='Number of evaluation episodes')
    eval_parser.add_argument('--env-type', type=str, help='Environment type')

    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demo')
    demo_parser.add_argument('--size', '-s', type=int, help='Grid world size')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Start monitoring server')
    monitor_parser.add_argument('--prometheus-port', type=int, help='Prometheus port')
    monitor_parser.add_argument('--tensorboard-dir', type=str, help='TensorBoard log directory')

    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmarks')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    # Execute command
    if args.command == 'train':
        train_command(args)
    elif args.command == 'evaluate':
        evaluate_command(args)
    elif args.command == 'demo':
        demo_command(args)
    elif args.command == 'monitor':
        monitor_command(args)
    elif args.command == 'benchmark':
        benchmark_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
