import sys
import os
import logging

# Add src/python to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "python"))

# Setup mocks
try:
    from utils.dependency_mocks import setup_mocks
    setup_mocks()
except ImportError:
    pass

import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from core.agent_host import create_agent
from core.environment_interface import create_environment

def test_minimal_loop():
    logger.info("Starting minimal loop test")

    # Create environment
    env = create_environment("gridworld", size=5)

    # Create agent
    agent = create_agent(
        num_perception_qubits=25, # matching grid size 5x5
        num_decision_qubits=8,
        num_action_qubits=4
    )

    # Run a few steps
    state = env.reset()
    for i in range(5):
        encoded_state = agent.perceive(state)
        processed = agent.process(encoded_state)
        action, q_values = agent.decide(processed)
        next_state, reward, done, info = env.step(action)

        logger.info(f"Step {i}: Action={action}, Reward={reward}, Done={done}")

        state = next_state
        if done:
            break

    logger.info("Minimal loop test completed successfully")

if __name__ == "__main__":
    test_minimal_loop()
