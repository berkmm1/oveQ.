#!/usr/bin/env python3
"""
Integration Tests for Quantum Agentic Loop Engine
"""

import unittest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "python"))

from quantum_agent import QuantumAgent, AgentConfiguration
from core.environment_interface import create_environment

class TestIntegrationLoop(unittest.TestCase):
    """Integration tests for the full quantum agentic loop"""

    def test_full_loop_gridworld(self):
        # Create environment
        env = create_environment("gridworld", size=4)

        # Create agent
        config = AgentConfiguration(
            num_qubits=16,
            learning_rate=0.01,
            exploration_rate=0.1
        )
        agent = QuantumAgent(num_actions=4, config=config)

        # Run 5 episodes
        results = agent.train(
            env_step=env.step,
            reset_env=env.reset,
            num_episodes=5,
            eval_interval=1
        )

        self.assertEqual(results['num_episodes'], 5)
        self.assertGreater(results['total_steps'], 0)
        self.assertIn('avg_reward', results)

    def test_full_loop_maze(self):
        # Create environment
        env = create_environment("maze", size=6)

        # Create agent
        config = AgentConfiguration(
            num_qubits=36, # 6*6 for maze
            learning_rate=0.01
        )
        agent = QuantumAgent(num_actions=4, config=config)

        # Run 2 episodes
        results = agent.train(
            env_step=env.step,
            reset_env=env.reset,
            num_episodes=2,
            eval_interval=1
        )

        self.assertEqual(results['num_episodes'], 2)

if __name__ == '__main__':
    unittest.main()
