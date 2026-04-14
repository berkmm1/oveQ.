#!/usr/bin/env python3
"""
Environment Interface for Quantum Agentic Engine
Supports various environment types and quantum-classical translation
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import gymnasium as gym
from gymnasium import spaces
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    state_dim: int = 16
    action_dim: int = 8
    max_steps: int = 1000
    reward_scale: float = 1.0
    normalize_observations: bool = True
    quantum_encode: bool = True


class QuantumEnvironment(ABC):
    """Abstract base class for quantum-compatible environments"""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.current_step = 0
        self.episode_reward = 0.0

    @abstractmethod
    def reset(self) -> np.ndarray:
        """Reset environment and return initial state"""
        pass

    @abstractmethod
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and return (next_state, reward, done, info)"""
        pass

    @abstractmethod
    def get_state_dim(self) -> int:
        """Get state dimension"""
        pass

    @abstractmethod
    def get_action_dim(self) -> int:
        """Get action dimension"""
        pass

    def quantum_encode_state(self, state: np.ndarray) -> np.ndarray:
        """Encode classical state for quantum processing"""
        if not self.config.quantum_encode:
            return state

        # Amplitude encoding simulation
        normalized = state / (np.linalg.norm(state) + 1e-8)

        # Add phase information
        phases = np.angle(normalized + 1e-8j)

        # Combine amplitude and phase
        encoded = np.concatenate([normalized, np.cos(phases), np.sin(phases)])

        return encoded[:self.config.state_dim]

    def normalize_reward(self, reward: float) -> float:
        """Normalize reward"""
        return reward * self.config.reward_scale


class GymEnvironmentWrapper(QuantumEnvironment):
    """Wrapper for Gymnasium environments"""

    def __init__(self, env_name: str, config: Optional[EnvironmentConfig] = None):
        self.env_name = env_name
        self.env = gym.make(env_name)

        # Infer dimensions from environment
        if hasattr(self.env.observation_space, 'shape'):
            state_dim = int(np.prod(self.env.observation_space.shape))
        else:
            state_dim = self.env.observation_space.n

        if hasattr(self.env.action_space, 'n'):
            action_dim = self.env.action_space.n
        else:
            action_dim = int(np.prod(self.env.action_space.shape))

        config = config or EnvironmentConfig()
        config.state_dim = state_dim
        config.action_dim = action_dim

        super().__init__(config)
        logger.info(f"Wrapped Gym environment: {env_name}")

    def reset(self) -> np.ndarray:
        state, info = self.env.reset()
        self.current_step = 0
        self.episode_reward = 0.0

        if isinstance(state, tuple):
            state = np.array(state)

        state = state.flatten()

        if self.config.normalize_observations:
            state = self._normalize(state)

        return self.quantum_encode_state(state)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        result = self.env.step(action)

        if len(result) == 5:
            state, reward, terminated, truncated, info = result
            done = terminated or truncated
        else:
            state, reward, done, info = result

        self.current_step += 1

        if isinstance(state, tuple):
            state = np.array(state)

        state = state.flatten()

        if self.config.normalize_observations:
            state = self._normalize(state)

        reward = self.normalize_reward(reward)
        self.episode_reward += reward

        # Enforce max steps
        if self.current_step >= self.config.max_steps:
            done = True

        info['episode_reward'] = self.episode_reward
        info['step'] = self.current_step

        return self.quantum_encode_state(state), reward, done, info

    def get_state_dim(self) -> int:
        return self.config.state_dim

    def get_action_dim(self) -> int:
        return self.config.action_dim

    def _normalize(self, state: np.ndarray) -> np.ndarray:
        """Normalize state to [-1, 1]"""
        return np.tanh(state / (np.std(state) + 1e-8))

    def close(self):
        self.env.close()


class GridWorldEnvironment(QuantumEnvironment):
    """Grid world navigation environment"""

    def __init__(self, size: int = 8, config: Optional[EnvironmentConfig] = None):
        config = config or EnvironmentConfig()
        config.state_dim = size * size
        config.action_dim = 4  # Up, Down, Left, Right

        super().__init__(config)
        self.size = size
        self.agent_pos = np.array([0, 0])
        self.goal_pos = np.array([size - 1, size - 1])
        self.obstacles = self._generate_obstacles()

    def _generate_obstacles(self) -> List[Tuple[int, int]]:
        """Generate random obstacles"""
        obstacles = []
        num_obstacles = self.size * self.size // 10

        for _ in range(num_obstacles):
            pos = (
                np.random.randint(0, self.size),
                np.random.randint(0, self.size)
            )
            if pos != (0, 0) and pos != (self.size - 1, self.size - 1):
                obstacles.append(pos)

        return obstacles

    def reset(self) -> np.ndarray:
        self.agent_pos = np.array([0, 0])
        self.current_step = 0
        self.episode_reward = 0.0
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        # Execute action
        moves = [
            np.array([-1, 0]),  # Up
            np.array([1, 0]),   # Down
            np.array([0, -1]),  # Left
            np.array([0, 1])    # Right
        ]

        new_pos = self.agent_pos + moves[action]

        # Check boundaries
        if (0 <= new_pos[0] < self.size and 0 <= new_pos[1] < self.size):
            # Check obstacles
            if tuple(new_pos) not in self.obstacles:
                self.agent_pos = new_pos

        self.current_step += 1

        # Compute reward
        distance = np.linalg.norm(self.agent_pos - self.goal_pos)
        reward = -0.1  # Step penalty

        done = False
        if np.array_equal(self.agent_pos, self.goal_pos):
            reward = 10.0
            done = True
        elif self.current_step >= self.config.max_steps:
            done = True

        reward = self.normalize_reward(reward)
        self.episode_reward += reward

        info = {
            'episode_reward': self.episode_reward,
            'step': self.current_step,
            'distance_to_goal': distance
        }

        return self._get_state(), reward, done, info

    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        # Flatten grid with agent and goal positions
        grid = np.zeros(self.size * self.size)

        # Mark agent position
        agent_idx = int(self.agent_pos[0] * self.size + self.agent_pos[1])
        if 0 <= agent_idx < len(grid):
            grid[agent_idx] = 1.0

        # Mark goal position
        goal_idx = int(self.goal_pos[0] * self.size + self.goal_pos[1])
        if 0 <= goal_idx < len(grid):
            grid[goal_idx] = 0.5

        # Mark obstacles
        for obs in self.obstacles:
            obs_idx = int(obs[0] * self.size + obs[1])
            if 0 <= obs_idx < len(grid):
                grid[obs_idx] = -1.0

        return self.quantum_encode_state(grid)

    def get_state_dim(self) -> int:
        return self.config.state_dim

    def get_action_dim(self) -> int:
        return self.config.action_dim


class ContinuousControlEnvironment(QuantumEnvironment):
    """Continuous control environment (e.g., for robotics)"""

    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 4,
        config: Optional[EnvironmentConfig] = None
    ):
        config = config or EnvironmentConfig()
        config.state_dim = state_dim * 2  # state + target
        config.action_dim = action_dim

        super().__init__(config)
        self.state_dim_base = state_dim
        self.state = np.zeros(state_dim)
        self.target = np.random.randn(state_dim) * 2

    def reset(self) -> np.ndarray:
        self.state = np.random.randn(self.state_dim_base) * 0.5
        self.target = np.random.randn(self.state_dim_base) * 2
        self.current_step = 0
        self.episode_reward = 0.0
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        # Convert discrete action to continuous control
        action_vectors = np.linspace(-1, 1, self.config.action_dim)
        control = np.ones(self.state_dim_base) * action_vectors[action]

        # Update state (simple dynamics)
        self.state += control * 0.1 + np.random.randn(self.state_dim_base) * 0.01

        # Compute reward (negative distance to target)
        distance = np.linalg.norm(self.state - self.target)
        reward = -distance

        self.current_step += 1

        done = distance < 0.1 or self.current_step >= self.config.max_steps

        reward = self.normalize_reward(reward)
        self.episode_reward += reward

        info = {
            'episode_reward': self.episode_reward,
            'step': self.current_step,
            'distance_to_target': distance
        }

        return self._get_state(), reward, done, info

    def _get_state(self) -> np.ndarray:
        """Get state with target information"""
        return self.quantum_encode_state(
            np.concatenate([self.state, self.target])
        )

    def get_state_dim(self) -> int:
        return self.config.state_dim * 2

    def get_action_dim(self) -> int:
        return self.config.action_dim


class MultiAgentEnvironment(QuantumEnvironment):
    """Environment for multi-agent scenarios"""

    def __init__(
        self,
        num_agents: int = 4,
        state_dim_per_agent: int = 4,
        action_dim_per_agent: int = 4,
        config: Optional[EnvironmentConfig] = None
    ):
        config = config or EnvironmentConfig()
        config.state_dim = state_dim_per_agent * num_agents + 2 # + target
        config.action_dim = action_dim_per_agent

        super().__init__(config)
        self.num_agents = num_agents
        self.state_dim_per_agent = state_dim_per_agent
        self.action_dim_per_agent = action_dim_per_agent

        self.agent_positions = np.random.randn(num_agents, 2)
        self.target_position = np.random.randn(2)

    def reset(self) -> np.ndarray:
        self.agent_positions = np.random.randn(self.num_agents, self.state_dim_per_agent // 2)
        self.target_position = np.random.randn(2) * 3
        self.current_step = 0
        self.episode_reward = 0.0
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        # Decode action for specific agent
        agent_id = action // self.action_dim_per_agent
        agent_action = action % self.action_dim_per_agent

        if agent_id < self.num_agents:
            # Move agent
            moves = [
                np.array([0, 1]),
                np.array([0, -1]),
                np.array([1, 0]),
                np.array([-1, 0])
            ]
            # Ensure moves matches dimensionality
            move = moves[agent_action % len(moves)][:self.agent_positions.shape[1]]
            self.agent_positions[agent_id] += move * 0.1

        self.current_step += 1

        # Compute team reward (collective distance to target)
        total_distance = sum(
            np.linalg.norm(pos - self.target_position)
            for pos in self.agent_positions
        )
        reward = -total_distance / self.num_agents

        done = total_distance < 0.5 or self.current_step >= self.config.max_steps

        reward = self.normalize_reward(reward)
        self.episode_reward += reward

        info = {
            'episode_reward': self.episode_reward,
            'step': self.current_step,
            'total_distance': total_distance
        }

        return self._get_state(), reward, done, info

    def _get_state(self) -> np.ndarray:
        """Get global state with all agent positions"""
        state = np.concatenate([
            self.agent_positions.flatten(),
            self.target_position
        ])
        return self.quantum_encode_state(state)

    def get_state_dim(self) -> int:
        return self.config.state_dim + 2

    def get_action_dim(self) -> int:
        return self.config.action_dim * self.num_agents


class QuantumMazeEnvironment(QuantumEnvironment):
    """Maze environment with quantum-inspired features"""

    def __init__(self, size: int = 10, config: Optional[EnvironmentConfig] = None):
        config = config or EnvironmentConfig()
        config.state_dim = size * size * 2  # Position + visited
        config.action_dim = 4

        super().__init__(config)
        self.size = size
        self.maze = self._generate_maze()
        self.visited = np.zeros((size, size))

    def _generate_maze(self) -> np.ndarray:
        """Generate random maze using recursive backtracking"""
        maze = np.ones((self.size, self.size))

        def carve(x, y):
            maze[x, y] = 0
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            np.random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and maze[nx, ny] == 1:
                    maze[x + dx // 2, y + dy // 2] = 0
                    carve(nx, ny)

        carve(0, 0)
        maze[self.size - 1, self.size - 1] = 0

        return maze

    def reset(self) -> np.ndarray:
        self.agent_pos = np.array([0, 0])
        self.visited = np.zeros((self.size, self.size))
        self.current_step = 0
        self.episode_reward = 0.0
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        moves = [
            np.array([-1, 0]),
            np.array([1, 0]),
            np.array([0, -1]),
            np.array([0, 1])
        ]

        new_pos = self.agent_pos + moves[action]

        # Check valid move
        if (0 <= new_pos[0] < self.size and
            0 <= new_pos[1] < self.size and
            self.maze[new_pos[0], new_pos[1]] == 0):
            self.agent_pos = new_pos

        # Mark visited
        self.visited[self.agent_pos[0], self.agent_pos[1]] = 1

        self.current_step += 1

        # Reward
        reward = -0.1
        if np.array_equal(self.agent_pos, [self.size - 1, self.size - 1]):
            reward = 100.0
            done = True
        elif self.current_step >= self.config.max_steps:
            done = True
        else:
            done = False

        reward = self.normalize_reward(reward)
        self.episode_reward += reward

        info = {
            'episode_reward': self.episode_reward,
            'step': self.current_step,
            'visited_cells': int(self.visited.sum())
        }

        return self._get_state(), reward, done, info

    def _get_state(self) -> np.ndarray:
        """Get state with maze, position, and visited info"""
        position = np.zeros((self.size, self.size))
        position[self.agent_pos[0], self.agent_pos[1]] = 1

        state = np.concatenate([
            self.maze.flatten(),
            position.flatten(),
            self.visited.flatten()
        ])

        return self.quantum_encode_state(state)

    def get_state_dim(self) -> int:
        return self.config.state_dim

    def get_action_dim(self) -> int:
        return self.config.action_dim


# Environment factory
def create_environment(
    env_type: str,
    **kwargs
) -> QuantumEnvironment:
    """Factory function to create environments"""

    if env_type == "gym":
        return GymEnvironmentWrapper(kwargs['env_name'], kwargs.get('config'))
    elif env_type == "gridworld":
        return GridWorldEnvironment(kwargs.get('size', 8), kwargs.get('config'))
    elif env_type == "continuous":
        return ContinuousControlEnvironment(
            kwargs.get('state_dim', 24),
            kwargs.get('action_dim', 6),
            kwargs.get('config')
        )
    elif env_type == "multiagent":
        return MultiAgentEnvironment(
            kwargs.get('num_agents', 4),
            kwargs.get('state_dim_per_agent', 8),
            kwargs.get('action_dim_per_agent', 4),
            kwargs.get('config')
        )
    elif env_type == "maze":
        return QuantumMazeEnvironment(kwargs.get('size', 10), kwargs.get('config'))
    else:
        raise ValueError(f"Unknown environment type: {env_type}")


if __name__ == "__main__":
    # Test environments
    env = create_environment("gridworld", size=5)
    state = env.reset()
    print(f"Initial state shape: {state.shape}")

    for _ in range(10):
        action = np.random.randint(0, env.get_action_dim())
        state, reward, done, info = env.step(action)
        print(f"Action: {action}, Reward: {reward:.2f}, Done: {done}")
        if done:
            break
