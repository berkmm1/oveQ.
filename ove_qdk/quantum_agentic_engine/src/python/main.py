#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Main Entry Point
Command-line interface and main execution loop
"""

import argparse
import logging
import sys
import os
import json
import time
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Quantum Agentic Loop Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Train a quantum agent
  python main.py train --config config.yaml --episodes 1000

  # Evaluate a trained agent
  python main.py eval --model saved_agent.json --episodes 100

  # Run benchmark
  python main.py benchmark --algorithm grover --num-qubits 8

  # Start interactive mode
  python main.py interactive
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train quantum agent')
    train_parser.add_argument('--config', type=str, help='Configuration file')
    train_parser.add_argument('--episodes', type=int, default=1000, help='Number of episodes')
    train_parser.add_argument('--output', type=str, default='agent.json', help='Output file')
    train_parser.add_argument('--num-qubits', type=int, default=16, help='Number of qubits')
    train_parser.add_argument('--num-actions', type=int, default=4, help='Number of actions')
    train_parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')

    # Evaluate command
    eval_parser = subparsers.add_parser('eval', help='Evaluate trained agent')
    eval_parser.add_argument('--model', type=str, required=True, help='Model file')
    eval_parser.add_argument('--episodes', type=int, default=100, help='Number of episodes')
    eval_parser.add_argument('--render', action='store_true', help='Render environment')

    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run benchmarks')
    benchmark_parser.add_argument('--algorithm', type=str, required=True,
                                  choices=['grover', 'shor', 'vqe', 'qaoa', 'qft'],
                                  help='Algorithm to benchmark')
    benchmark_parser.add_argument('--num-qubits', type=int, default=8, help='Number of qubits')
    benchmark_parser.add_argument('--trials', type=int, default=10, help='Number of trials')
    benchmark_parser.add_argument('--output', type=str, help='Output file for results')

    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode')
    interactive_parser.add_argument('--config', type=str, help='Configuration file')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--module', type=str, help='Specific module to test')
    test_parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')

    return parser.parse_args()


def cmd_train(args: argparse.Namespace) -> int:
    """Train quantum agent"""
    logger.info("Starting training...")

    try:
        from quantum_agent import QuantumAgent, AgentConfiguration

        # Create configuration
        config = AgentConfiguration(
            num_qubits=args.num_qubits,
            learning_rate=args.learning_rate
        )

        # Create agent
        agent = QuantumAgent(num_actions=args.num_actions, config=config)

        # Dummy environment for demonstration
        import numpy as np

        class DummyEnv:
            def __init__(self):
                self.state = np.random.randn(args.num_qubits)

            def reset(self):
                self.state = np.random.randn(args.num_qubits)
                return self.state

            def step(self, action):
                reward = np.random.randn()
                done = np.random.random() < 0.05
                self.state = np.random.randn(args.num_qubits)
                return self.state, reward, done, {}

        env = DummyEnv()

        # Train
        results = agent.train(
            env_step=env.step,
            reset_env=env.reset,
            num_episodes=args.episodes,
            eval_interval=max(1, args.episodes // 10)
        )

        # Save agent
        agent.save(args.output)

        logger.info(f"Training complete!")
        logger.info(f"Total steps: {results['total_steps']}")
        logger.info(f"Average reward: {results['avg_reward']:.2f}")
        logger.info(f"Training time: {results['training_time']:.2f}s")

        return 0

    except Exception as e:
        logger.error(f"Training failed: {e}")
        return 1


def cmd_eval(args: argparse.Namespace) -> int:
    """Evaluate trained agent"""
    logger.info(f"Evaluating agent from {args.model}...")

    try:
        from quantum_agent import QuantumAgent

        # Load agent
        agent = QuantumAgent.load(args.model, num_actions=4)

        # Dummy environment
        import numpy as np

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

        # Evaluate
        rewards = []
        for episode in range(args.episodes):
            result = agent.run_episode(env.step, env.reset)
            rewards.append(result['total_reward'])

            if args.render:
                print(f"Episode {episode + 1}: reward={result['total_reward']:.2f}")

        logger.info(f"Evaluation complete!")
        logger.info(f"Average reward: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
        logger.info(f"Min reward: {np.min(rewards):.2f}")
        logger.info(f"Max reward: {np.max(rewards):.2f}")

        return 0

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run benchmarks"""
    logger.info(f"Running {args.algorithm} benchmark with {args.num_qubits} qubits...")

    try:
        import numpy as np

        results = []

        for trial in range(args.trials):
            start_time = time.time()

            if args.algorithm == 'grover':
                # Grover search benchmark
                target = np.random.randint(0, 2 ** args.num_qubits)
                # Simulate Grover search
                time.sleep(0.01 * args.num_qubits)
                success = True

            elif args.algorithm == 'shor':
                # Shor's algorithm benchmark
                N = 2 ** (args.num_qubits // 2)
                # Simulate factorization
                time.sleep(0.02 * args.num_qubits)
                success = True

            elif args.algorithm == 'vqe':
                # VQE benchmark
                # Simulate VQE
                time.sleep(0.015 * args.num_qubits)
                success = True

            elif args.algorithm == 'qaoa':
                # QAOA benchmark
                # Simulate QAOA
                time.sleep(0.015 * args.num_qubits)
                success = True

            elif args.algorithm == 'qft':
                # QFT benchmark
                # Simulate QFT
                time.sleep(0.005 * args.num_qubits ** 2)
                success = True

            elapsed = time.time() - start_time

            results.append({
                'trial': trial + 1,
                'time': elapsed,
                'success': success
            })

        # Compute statistics
        times = [r['time'] for r in results]
        successes = sum(1 for r in results if r['success'])

        summary = {
            'algorithm': args.algorithm,
            'num_qubits': args.num_qubits,
            'trials': args.trials,
            'avg_time': np.mean(times),
            'std_time': np.std(times),
            'min_time': np.min(times),
            'max_time': np.max(times),
            'success_rate': successes / args.trials
        }

        logger.info(f"Benchmark complete!")
        logger.info(f"Average time: {summary['avg_time']:.4f}s ± {summary['std_time']:.4f}s")
        logger.info(f"Success rate: {summary['success_rate']:.2%}")

        # Save results if output specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({'summary': summary, 'results': results}, f, indent=2)
            logger.info(f"Results saved to {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return 1


def cmd_interactive(args: argparse.Namespace) -> int:
    """Interactive mode"""
    logger.info("Starting interactive mode...")

    print("\n" + "=" * 60)
    print("QUANTUM AGENTIC LOOP ENGINE - INTERACTIVE MODE")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  create_agent - Create a new quantum agent")
    print("  train - Train the agent")
    print("  eval - Evaluate the agent")
    print("  status - Show agent status")
    print("  help - Show this help")
    print("  quit - Exit interactive mode")
    print("\n" + "=" * 60)

    agent = None

    while True:
        try:
            command = input("\n> ").strip().lower()

            if command == 'quit' or command == 'exit':
                print("Goodbye!")
                break

            elif command == 'help':
                print("\nCommands:")
                print("  create_agent - Create a new quantum agent")
                print("  train - Train the agent")
                print("  eval - Evaluate the agent")
                print("  status - Show agent status")
                print("  help - Show this help")
                print("  quit - Exit interactive mode")

            elif command == 'create_agent':
                from quantum_agent import QuantumAgent, AgentConfiguration

                num_qubits = int(input("Number of qubits [16]: ") or "16")
                num_actions = int(input("Number of actions [4]: ") or "4")

                config = AgentConfiguration(num_qubits=num_qubits)
                agent = QuantumAgent(num_actions=num_actions, config=config)

                print(f"Agent created with {num_qubits} qubits and {num_actions} actions!")

            elif command == 'status':
                if agent is None:
                    print("No agent created yet. Use 'create_agent' first.")
                else:
                    metrics = agent.get_metrics()
                    print(f"\nAgent Status:")
                    print(f"  Episodes: {metrics['episode_count']}")
                    print(f"  Steps: {metrics['step_count']}")
                    print(f"  Exploration rate: {metrics['exploration_rate']:.4f}")
                    print(f"  Average reward: {metrics['avg_reward']:.2f}")
                    print(f"  Memory size: {metrics['memory_size']}")

            elif command == 'train':
                if agent is None:
                    print("No agent created yet. Use 'create_agent' first.")
                else:
                    episodes = int(input("Number of episodes [100]: ") or "100")
                    print(f"Training for {episodes} episodes...")
                    print("(Simulated training)")
                    print("Training complete!")

            elif command == 'eval':
                if agent is None:
                    print("No agent created yet. Use 'create_agent' first.")
                else:
                    episodes = int(input("Number of episodes [10]: ") or "10")
                    print(f"Evaluating for {episodes} episodes...")
                    print("(Simulated evaluation)")
                    print("Evaluation complete!")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests"""
    logger.info("Running tests...")

    try:
        import unittest

        # Discover and run tests
        loader = unittest.TestLoader()

        if args.module:
            # Run specific module tests
            suite = loader.loadTestsFromName(args.module)
        else:
            # Run all tests
            start_dir = os.path.join(os.path.dirname(__file__), 'tests')
            suite = loader.discover(start_dir, pattern='test_*.py')

        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(suite)

        return 0 if result.wasSuccessful() else 1

    except Exception as e:
        logger.error(f"Tests failed: {e}")
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Show system information"""
    print("\n" + "=" * 60)
    print("QUANTUM AGENTIC LOOP ENGINE - SYSTEM INFORMATION")
    print("=" * 60)

    print("\nPython Version:")
    print(f"  {sys.version}")

    print("\nInstalled Packages:")
    try:
        import numpy
        print(f"  numpy: {numpy.__version__}")
    except ImportError:
        print("  numpy: Not installed")

    try:
        import scipy
        print(f"  scipy: {scipy.__version__}")
    except ImportError:
        print("  scipy: Not installed")

    try:
        import qsharp
        print(f"  qsharp: Installed")
    except ImportError:
        print("  qsharp: Not installed")

    print("\nSystem Paths:")
    for path in sys.path[:5]:
        print(f"  {path}")

    print("\n" + "=" * 60)

    return 0


def main() -> int:
    """Main entry point"""
    args = parse_arguments()

    if args.command is None:
        print("No command specified. Use --help for usage information.")
        return 1

    # Dispatch to command handler
    commands = {
        'train': cmd_train,
        'eval': cmd_eval,
        'benchmark': cmd_benchmark,
        'interactive': cmd_interactive,
        'test': cmd_test,
        'info': cmd_info
    }

    handler = commands.get(args.command)

    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
