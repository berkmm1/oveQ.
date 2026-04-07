#!/usr/bin/env python3
"""
Quantum-Enhanced Environments Module
Custom environments with quantum state representations
Part of the Quantum Agentic Loop Engine
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import gym
from gym import spaces
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Types of quantum-enhanced environments"""
    DISCRETE = auto()
    CONTINUOUS = auto()
    QUANTUM_STATE = auto()
    HYBRID = auto()


@dataclass
class EnvironmentConfig:
    """Configuration for quantum environment"""
    name: str
    env_type: EnvironmentType
    state_dim: int
    action_dim: int
    num_qubits: int = 8
    max_steps: int = 1000
    reward_scale: float = 1.0
    use_quantum_observation: bool = True
    use_quantum_reward: bool = False
    quantum_noise_level: float = 0.01

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'env_type': self.env_type.name,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'num_qubits': self.num_qubits,
            'max_steps': self.max_steps,
            'reward_scale': self.reward_scale,
            'use_quantum_observation': self.use_quantum_observation,
            'use_quantum_reward': self.use_quantum_reward,
            'quantum_noise_level': self.quantum_noise_level
        }


class QuantumStateSpace:
    """Quantum state space representation"""

    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits

    def sample(self) -> np.ndarray:
        """Sample a random quantum state"""
        # Random state vector
        state = np.random.randn(self.dimension) + 1j * np.random.randn(self.dimension)
        # Normalize
        state = state / np.linalg.norm(state)
        return state

    def encode_classical(self, classical_state: np.ndarray) -> np.ndarray:
        """Encode classical state into quantum state"""
        # Amplitude encoding
        normalized = classical_state / (np.linalg.norm(classical_state) + 1e-8)

        # Pad to match dimension
        if len(normalized) < self.dimension:
            padded = np.zeros(self.dimension)
            padded[:len(normalized)] = normalized
            normalized = padded
        else:
            normalized = normalized[:self.dimension]

        # Normalize again
        normalized = normalized / np.linalg.norm(normalized)
        return normalized

    def decode_quantum(self, quantum_state: np.ndarray) -> np.ndarray:
        """Decode quantum state to classical probabilities"""
        probabilities = np.abs(quantum_state) ** 2
        return probabilities


class QuantumObservationWrapper:
    """Wrapper to add quantum features to observations"""

    def __init__(self, base_observation_dim: int, num_qubits: int):
        self.base_dim = base_observation_dim
        self.num_qubits = num_qubits
        self.quantum_dim = 2 ** num_qubits
        self.total_dim = base_observation_dim + self.quantum_dim

    def wrap(self, observation: np.ndarray) -> np.ndarray:
        """Add quantum features to observation"""
        # Create quantum encoding
        quantum_features = self._compute_quantum_features(observation)

        # Concatenate
        wrapped = np.concatenate([observation, quantum_features])
        return wrapped

    def _compute_quantum_features(self, observation: np.ndarray) -> np.ndarray:
        """Compute quantum-inspired features"""
        # Normalize observation
        normalized = (observation - np.mean(observation)) / (np.std(observation) + 1e-8)

        # Create superposition-like features
        features = np.zeros(self.quantum_dim)

        for i in range(min(len(normalized), self.num_qubits)):
            # Encode as rotation angles
            angle = np.arctan(normalized[i]) * np.pi

            # Create interference pattern
            for j in range(self.quantum_dim):
                features[j] += np.cos(angle * j + i * np.pi / 4) / self.num_qubits

        # Normalize
        features = np.abs(features)
        features = features / (np.sum(features) + 1e-8)

        return features


class QuantumRewardFunction:
    """Quantum-enhanced reward computation"""

    def __init__(self, num_qubits: int, noise_level: float = 0.01):
        self.num_qubits = num_qubits
        self.noise_level = noise_level
        self.reward_history = []

    def compute(self, state: np.ndarray, action: int, next_state: np.ndarray,
                base_reward: float) -> float:
        """Compute quantum-enhanced reward"""
        # Add quantum fluctuation
        quantum_noise = np.random.randn() * self.noise_level

        # Compute quantum coherence bonus
        coherence = self._compute_coherence(next_state)

        # Combine rewards
        enhanced_reward = base_reward + quantum_noise + 0.1 * coherence

        self.reward_history.append(enhanced_reward)

        return enhanced_reward

    def _compute_coherence(self, state: np.ndarray) -> float:
        """Compute quantum coherence measure"""
        # Simplified coherence: variance of state elements
        if len(state) > 0:
            return np.var(state)
        return 0.0

    def get_statistics(self) -> Dict[str, float]:
        """Get reward statistics"""
        if not self.reward_history:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}

        return {
            'mean': np.mean(self.reward_history),
            'std': np.std(self.reward_history),
            'min': np.min(self.reward_history),
            'max': np.max(self.reward_history)
        }


class QuantumGridWorld(gym.Env):
    """Quantum-enhanced grid world environment"""

    def __init__(self, size: int = 8, num_goals: int = 3, config: Optional[EnvironmentConfig] = None):
        super().__init__()

        self.size = size
        self.num_goals = num_goals
        self.config = config or EnvironmentConfig(
            name="QuantumGridWorld",
            env_type=EnvironmentType.QUANTUM_STATE,
            state_dim=size * size * 3,
            action_dim=4
        )

        # Action space: 0=up, 1=down, 2=left, 3=right
        self.action_space = spaces.Discrete(4)

        # Observation space
        obs_dim = self.config.state_dim
        if self.config.use_quantum_observation:
            self.observation_wrapper = QuantumObservationWrapper(
                self.config.state_dim,
                self.config.num_qubits
            )
            obs_dim = self.observation_wrapper.total_dim

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32
        )

        # Quantum components
        self.quantum_state_space = QuantumStateSpace(self.config.num_qubits)
        self.quantum_reward = QuantumRewardFunction(
            self.config.num_qubits,
            self.config.quantum_noise_level
        )

        # State variables
        self.agent_pos = None
        self.goal_positions = []
        self.obstacle_positions = []
        self.collected_goals = set()
        self.steps = 0

        # Rendering
        self.viewer = None

        self.reset()

    def reset(self) -> np.ndarray:
        """Reset environment"""
        # Random agent position
        self.agent_pos = [
            np.random.randint(0, self.size),
            np.random.randint(0, self.size)
        ]

        # Random goal positions
        self.goal_positions = []
        for _ in range(self.num_goals):
            while True:
                pos = [
                    np.random.randint(0, self.size),
                    np.random.randint(0, self.size)
                ]
                if pos != self.agent_pos and pos not in self.goal_positions:
                    self.goal_positions.append(pos)
                    break

        # Random obstacles
        self.obstacle_positions = []
        num_obstacles = self.size
        for _ in range(num_obstacles):
            while True:
                pos = [
                    np.random.randint(0, self.size),
                    np.random.randint(0, self.size)
                ]
                if (pos != self.agent_pos and
                    pos not in self.goal_positions and
                    pos not in self.obstacle_positions):
                    self.obstacle_positions.append(pos)
                    break

        self.collected_goals = set()
        self.steps = 0

        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute one step"""
        self.steps += 1

        # Store old position
        old_pos = self.agent_pos.copy()

        # Move agent
        if action == 0:  # up
            self.agent_pos[1] = max(0, self.agent_pos[1] - 1)
        elif action == 1:  # down
            self.agent_pos[1] = min(self.size - 1, self.agent_pos[1] + 1)
        elif action == 2:  # left
            self.agent_pos[0] = max(0, self.agent_pos[0] - 1)
        elif action == 3:  # right
            self.agent_pos[0] = min(self.size - 1, self.agent_pos[0] + 1)

        # Check for obstacles
        if self.agent_pos in self.obstacle_positions:
            # Bounce back
            self.agent_pos = old_pos
            base_reward = -1.0
        else:
            base_reward = -0.01  # Small penalty for each step

        # Check for goals
        goal_id = None
        for i, goal in enumerate(self.goal_positions):
            if self.agent_pos == goal and i not in self.collected_goals:
                self.collected_goals.add(i)
                base_reward += 10.0
                goal_id = i
                break

        # Check if all goals collected
        done = len(self.collected_goals) == len(self.goal_positions)

        # Check max steps
        if self.steps >= self.config.max_steps:
            done = True

        # Compute quantum-enhanced reward
        observation = self._get_observation()
        next_observation = observation

        if self.config.use_quantum_reward:
            reward = self.quantum_reward.compute(
                observation, action, next_observation, base_reward
            )
        else:
            reward = base_reward

        reward *= self.config.reward_scale

        info = {
            'steps': self.steps,
            'goals_collected': len(self.collected_goals),
            'total_goals': len(self.goal_positions),
            'goal_id': goal_id
        }

        return next_observation, reward, done, info

    def _get_observation(self) -> np.ndarray:
        """Get current observation"""
        # Create grid representation
        grid = np.zeros((self.size, self.size, 3))

        # Agent channel
        grid[self.agent_pos[0], self.agent_pos[1], 0] = 1.0

        # Goal channel
        for i, goal in enumerate(self.goal_positions):
            if i not in self.collected_goals:
                grid[goal[0], goal[1], 1] = 1.0

        # Obstacle channel
        for obs in self.obstacle_positions:
            grid[obs[0], obs[1], 2] = 1.0

        # Flatten
        observation = grid.flatten()

        # Add quantum features if enabled
        if self.config.use_quantum_observation:
            observation = self.observation_wrapper.wrap(observation)

        return observation.astype(np.float32)

    def render(self, mode: str = 'human'):
        """Render environment"""
        if mode == 'console':
            grid = [['.' for _ in range(self.size)] for _ in range(self.size)]

            # Place obstacles
            for obs in self.obstacle_positions:
                grid[obs[0]][obs[1]] = '#'

            # Place goals
            for i, goal in enumerate(self.goal_positions):
                if i not in self.collected_goals:
                    grid[goal[0]][goal[1]] = 'G'

            # Place agent
            grid[self.agent_pos[0]][self.agent_pos[1]] = 'A'

            print('\n'.join([' '.join(row) for row in grid]))
            print()

    def close(self):
        """Close environment"""
        pass


class QuantumContinuousEnvironment(gym.Env):
    """Quantum-enhanced continuous control environment"""

    def __init__(self, state_dim: int = 8, action_dim: int = 4,
                 config: Optional[EnvironmentConfig] = None):
        super().__init__()

        self.config = config or EnvironmentConfig(
            name="QuantumContinuous",
            env_type=EnvironmentType.CONTINUOUS,
            state_dim=state_dim,
            action_dim=action_dim
        )

        # Action space: continuous
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(action_dim,),
            dtype=np.float32
        )

        # Observation space
        obs_dim = state_dim
        if self.config.use_quantum_observation:
            self.observation_wrapper = QuantumObservationWrapper(
                state_dim,
                self.config.num_qubits
            )
            obs_dim = self.observation_wrapper.total_dim

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32
        )

        # Quantum components
        self.quantum_reward = QuantumRewardFunction(
            self.config.num_qubits,
            self.config.quantum_noise_level
        )

        # State
        self.state = None
        self.target_state = None
        self.steps = 0

        self.reset()

    def reset(self) -> np.ndarray:
        """Reset environment"""
        self.state = np.random.randn(self.config.state_dim) * 0.5
        self.target_state = np.random.randn(self.config.state_dim) * 0.5
        self.steps = 0
        return self._get_observation()

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute one step"""
        self.steps += 1

        # Apply action (dynamics)
        self.state += action * 0.1
        self.state = np.clip(self.state, -5.0, 5.0)

        # Compute distance to target
        distance = np.linalg.norm(self.state - self.target_state)

        # Base reward: negative distance
        base_reward = -distance

        # Bonus for reaching target
        if distance < 0.5:
            base_reward += 10.0

        # Quantum-enhanced reward
        observation = self._get_observation()

        if self.config.use_quantum_reward:
            reward = self.quantum_reward.compute(
                observation, 0, observation, base_reward
            )
        else:
            reward = base_reward

        reward *= self.config.reward_scale

        # Check termination
        done = self.steps >= self.config.max_steps or distance < 0.1

        info = {
            'distance': distance,
            'steps': self.steps
        }

        return self._get_observation(), reward, done, info

    def _get_observation(self) -> np.ndarray:
        """Get observation"""
        observation = self.state.copy()

        if self.config.use_quantum_observation:
            observation = self.observation_wrapper.wrap(observation)

        return observation.astype(np.float32)

    def render(self, mode: str = 'human'):
        """Render environment"""
        if mode == 'console':
            print(f"State: {self.state}")
            print(f"Target: {self.target_state}")
            print(f"Distance: {np.linalg.norm(self.state - self.target_state):.4f}")
            print()


class QuantumMazeEnvironment(gym.Env):
    """Quantum-enhanced maze navigation"""

    def __init__(self, width: int = 15, height: int = 15,
                 config: Optional[EnvironmentConfig] = None):
        super().__init__()

        self.width = width
        self.height = height
        self.config = config or EnvironmentConfig(
            name="QuantumMaze",
            env_type=EnvironmentType.HYBRID,
            state_dim=width * height * 2,
            action_dim=4
        )

        self.action_space = spaces.Discrete(4)

        obs_dim = self.config.state_dim
        if self.config.use_quantum_observation:
            self.observation_wrapper = QuantumObservationWrapper(
                self.config.state_dim,
                self.config.num_qubits
            )
            obs_dim = self.observation_wrapper.total_dim

        self.observation_space = spaces.Box(
            low=0,
            high=1,
            shape=(obs_dim,),
            dtype=np.float32
        )

        # Quantum components
        self.quantum_reward = QuantumRewardFunction(
            self.config.num_qubits,
            self.config.quantum_noise_level
        )

        # Maze generation
        self.maze = None
        self.start_pos = None
        self.end_pos = None
        self.agent_pos = None
        self.steps = 0

        self.reset()

    def _generate_maze(self):
        """Generate random maze using recursive backtracking"""
        # Initialize grid with walls
        self.maze = np.ones((self.width, self.height), dtype=int)

        # Start from random position
        start_x = np.random.randint(0, self.width // 2) * 2
        start_y = np.random.randint(0, self.height // 2) * 2
        self.maze[start_x, start_y] = 0

        # Stack for backtracking
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]

            # Find unvisited neighbors
            neighbors = []
            for dx, dy in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    self.maze[nx, ny] == 1):
                    neighbors.append((nx, ny, dx // 2, dy // 2))

            if neighbors:
                # Choose random neighbor
                nx, ny, wx, wy = neighbors[np.random.randint(len(neighbors))]

                # Remove wall
                self.maze[x + wx, y + wy] = 0
                self.maze[nx, ny] = 0

                stack.append((nx, ny))
            else:
                stack.pop()

        # Set start and end
        self.start_pos = [start_x, start_y]

        # Find furthest point for end
        max_dist = 0
        for x in range(self.width):
            for y in range(self.height):
                if self.maze[x, y] == 0:
                    dist = abs(x - start_x) + abs(y - start_y)
                    if dist > max_dist:
                        max_dist = dist
                        self.end_pos = [x, y]

    def reset(self) -> np.ndarray:
        """Reset environment"""
        self._generate_maze()
        self.agent_pos = self.start_pos.copy()
        self.steps = 0
        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute one step"""
        self.steps += 1

        # Calculate new position
        new_pos = self.agent_pos.copy()
        if action == 0:  # up
            new_pos[1] -= 1
        elif action == 1:  # down
            new_pos[1] += 1
        elif action == 2:  # left
            new_pos[0] -= 1
        elif action == 3:  # right
            new_pos[0] += 1

        # Check if valid move
        if (0 <= new_pos[0] < self.width and
            0 <= new_pos[1] < self.height and
            self.maze[new_pos[0], new_pos[1]] == 0):
            self.agent_pos = new_pos
            base_reward = -0.01
        else:
            base_reward = -0.5  # Hit wall

        # Check if reached end
        done = self.agent_pos == self.end_pos
        if done:
            base_reward += 100.0

        # Check max steps
        if self.steps >= self.config.max_steps:
            done = True

        # Quantum-enhanced reward
        if self.config.use_quantum_reward:
            observation = self._get_observation()
            reward = self.quantum_reward.compute(
                observation, action, observation, base_reward
            )
        else:
            reward = base_reward

        reward *= self.config.reward_scale

        info = {
            'steps': self.steps,
            'position': self.agent_pos.copy(),
            'reached_end': self.agent_pos == self.end_pos
        }

        return self._get_observation(), reward, done, info

    def _get_observation(self) -> np.ndarray:
        """Get observation"""
        # Maze layout
        maze_flat = self.maze.flatten()

        # Agent position one-hot
        pos_encoding = np.zeros(self.width * self.height)
        pos_idx = self.agent_pos[0] * self.height + self.agent_pos[1]
        pos_encoding[pos_idx] = 1.0

        observation = np.concatenate([maze_flat, pos_encoding])

        if self.config.use_quantum_observation:
            observation = self.observation_wrapper.wrap(observation)

        return observation.astype(np.float32)

    def render(self, mode: str = 'human'):
        """Render maze"""
        if mode == 'console':
            for y in range(self.height):
                row = ''
                for x in range(self.width):
                    if [x, y] == self.agent_pos:
                        row += 'A'
                    elif [x, y] == self.end_pos:
                        row += 'E'
                    elif self.maze[x, y] == 1:
                        row += '#'
                    else:
                        row += ' '
                print(row)
            print()


# Environment factory
def create_quantum_environment(env_type: str, **kwargs) -> gym.Env:
    """Create a quantum-enhanced environment"""
    if env_type == 'gridworld':
        return QuantumGridWorld(**kwargs)
    elif env_type == 'continuous':
        return QuantumContinuousEnvironment(**kwargs)
    elif env_type == 'maze':
        return QuantumMazeEnvironment(**kwargs)
    else:
        raise ValueError(f"Unknown environment type: {env_type}")


if __name__ == "__main__":
    print("Quantum Environments Module")
    print("=" * 40)

    # Test grid world
    print("\nTesting Quantum Grid World:")
    env = QuantumGridWorld(size=5, num_goals=2)
    obs = env.reset()
    print(f"Observation shape: {obs.shape}")

    for _ in range(5):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        env.render('console')
        print(f"Action: {action}, Reward: {reward:.2f}, Done: {done}")
        if done:
            break
