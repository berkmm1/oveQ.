#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Gym-compatible Quantum Environments
OpenAI Gym interface for quantum-enhanced environments
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_gym_availability():
    """Check if gym/gymnasium is available"""
    try:
        import gymnasium as gym
        return gym, "gymnasium"
    except ImportError:
        try:
            import gym
            return gym, "gym"
        except ImportError:
            return None, None


# Get gym module
gym_module, gym_name = check_gym_availability()

if gym_module:
    Env = gym_module.Env
    Space = gym_module.Space
else:
    # Define base classes if gym not available
    class Env:
        """Base environment class"""
        def __init__(self):
            pass

        def reset(self, **kwargs):
            raise NotImplementedError

        def step(self, action):
            raise NotImplementedError

        def render(self, mode='human'):
            pass

        def close(self):
            pass

    class Space:
        """Base space class"""
        def sample(self):
            raise NotImplementedError


@dataclass
class QuantumEnvConfig:
    """Configuration for quantum environment"""
    state_dim: int = 16
    action_dim: int = 4
    max_steps: int = 1000
    use_quantum_observation: bool = True
    use_quantum_reward: bool = False
    quantum_noise_level: float = 0.01
    entanglement_strength: float = 0.5
    use_superposition_actions: bool = True
    reward_scale: float = 1.0
    done_on_quantum_error: bool = False


class QuantumObservationSpace:
    """Observation space with quantum features"""

    def __init__(self, shape: Tuple[int, ...], dtype=np.float32):
        self.shape = shape
        self.dtype = dtype
        self.low = -np.inf * np.ones(shape, dtype=dtype)
        self.high = np.inf * np.ones(shape, dtype=dtype)

    def sample(self) -> np.ndarray:
        """Sample from observation space"""
        return np.random.randn(*self.shape).astype(self.dtype)

    def contains(self, x: np.ndarray) -> bool:
        """Check if value is in space"""
        return x.shape == self.shape and np.all(x >= self.low) and np.all(x <= self.high)


class QuantumActionSpace:
    """Action space with quantum superposition"""

    def __init__(self, n: int, use_superposition: bool = True):
        self.n = n
        self.use_superposition = use_superposition
        self.amplitudes = np.ones(n) / np.sqrt(n)  # Uniform superposition

    def sample(self) -> int:
        """Sample action from superposition"""
        if self.use_superposition:
            probabilities = np.abs(self.amplitudes) ** 2
            return np.random.choice(self.n, p=probabilities)
        else:
            return np.random.randint(self.n)

    def sample_superposition(self) -> np.ndarray:
        """Sample action in superposition"""
        return self.amplitudes.copy()

    def update_amplitudes(self, new_amplitudes: np.ndarray):
        """Update action amplitudes"""
        self.amplitudes = new_amplitudes / np.linalg.norm(new_amplitudes)

    def contains(self, x: Union[int, np.ndarray]) -> bool:
        """Check if value is in space"""
        if isinstance(x, int):
            return 0 <= x < self.n
        elif isinstance(x, np.ndarray):
            return len(x) == self.n
        return False


class QuantumGridWorld(Env):
    """
    Grid world environment with quantum-enhanced observations
    """

    def __init__(self, config: Optional[QuantumEnvConfig] = None):
        super().__init__()
        self.config = config or QuantumEnvConfig()

        # Grid parameters
        self.grid_size = int(np.sqrt(self.config.state_dim))
        self.agent_pos = [0, 0]
        self.goal_pos = [self.grid_size - 1, self.grid_size - 1]
        self.obstacles: List[Tuple[int, int]] = []

        # Episode tracking
        self.steps = 0
        self.total_reward = 0.0

        # Quantum state
        self.quantum_state = np.zeros(self.config.state_dim, dtype=complex)
        self.entangled_pairs: List[Tuple[int, int]] = []

        # Define spaces
        self.observation_space = QuantumObservationSpace(
            (self.config.state_dim,),
            dtype=np.float32
        )
        self.action_space = QuantumActionSpace(
            self.config.action_dim,
            use_superposition=self.config.use_superposition_actions
        )

        # Generate obstacles
        self._generate_obstacles()

        logger.info(f"QuantumGridWorld initialized: {self.grid_size}x{self.grid_size}")

    def _generate_obstacles(self):
        """Generate random obstacles"""
        num_obstacles = self.grid_size // 3
        for _ in range(num_obstacles):
            x = np.random.randint(0, self.grid_size)
            y = np.random.randint(0, self.grid_size)

            # Don't place on start or goal
            if (x, y) != (0, 0) and (x, y) != tuple(self.goal_pos):
                self.obstacles.append((x, y))

        # Create entangled pairs
        for i in range(0, self.config.state_dim - 1, 2):
            self.entangled_pairs.append((i, i + 1))

    def reset(self, seed: Optional[int] = None, **kwargs) -> Tuple[np.ndarray, Dict]:
        """Reset environment"""
        if seed is not None:
            np.random.seed(seed)

        self.agent_pos = [0, 0]
        self.steps = 0
        self.total_reward = 0.0

        # Initialize quantum state
        self.quantum_state = np.zeros(self.config.state_dim, dtype=complex)
        self.quantum_state[0] = 1.0

        observation = self._get_observation()
        info = {"quantum_state": self.quantum_state.copy()}

        return observation, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute action"""
        self.steps += 1

        # Execute movement
        prev_pos = self.agent_pos.copy()

        if action == 0:  # Up
            self.agent_pos[1] = max(0, self.agent_pos[1] - 1)
        elif action == 1:  # Down
            self.agent_pos[1] = min(self.grid_size - 1, self.agent_pos[1] + 1)
        elif action == 2:  # Left
            self.agent_pos[0] = max(0, self.agent_pos[0] - 1)
        elif action == 3:  # Right
            self.agent_pos[0] = min(self.grid_size - 1, self.agent_pos[0] + 1)

        # Check for obstacles
        if tuple(self.agent_pos) in self.obstacles:
            self.agent_pos = prev_pos  # Bounce back

        # Update quantum state
        self._update_quantum_state(action)

        # Calculate reward
        reward = self._calculate_reward(prev_pos)
        self.total_reward += reward

        # Check termination
        terminated = self.agent_pos == self.goal_pos
        truncated = self.steps >= self.config.max_steps

        observation = self._get_observation()
        info = {
            "steps": self.steps,
            "total_reward": self.total_reward,
            "quantum_state": self.quantum_state.copy(),
            "position": self.agent_pos.copy()
        }

        return observation, reward, terminated, truncated, info

    def _update_quantum_state(self, action: int):
        """Update quantum state based on action"""
        # Apply quantum gate based on action
        gate = self._get_action_gate(action)
        self.quantum_state = gate @ self.quantum_state

        # Apply entanglement
        for i, j in self.entangled_pairs:
            self._apply_entanglement(i, j)

        # Add quantum noise
        if self.config.quantum_noise_level > 0:
            noise = (np.random.randn(self.config.state_dim) +
                    1j * np.random.randn(self.config.state_dim))
            self.quantum_state += self.config.quantum_noise_level * noise
            self.quantum_state /= np.linalg.norm(self.quantum_state)

    def _get_action_gate(self, action: int) -> np.ndarray:
        """Get quantum gate for action"""
        dim = self.config.state_dim
        gate = np.eye(dim, dtype=complex)

        # Apply rotation based on action
        angle = np.pi / 4 * (action + 1)
        rotation = np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ], dtype=complex)

        # Embed rotation in full gate
        idx = self._pos_to_idx(self.agent_pos)
        if idx < dim - 1:
            gate[idx:idx+2, idx:idx+2] = rotation

        return gate

    def _apply_entanglement(self, i: int, j: int):
        """Apply entanglement between two qubits"""
        strength = self.config.entanglement_strength

        # Create Bell state-like entanglement
        if i < len(self.quantum_state) and j < len(self.quantum_state):
            # Apply CNOT-like operation
            temp = self.quantum_state[i]
            self.quantum_state[i] = (temp + strength * self.quantum_state[j]) / np.sqrt(1 + strength**2)
            self.quantum_state[j] = (strength * temp + self.quantum_state[j]) / np.sqrt(1 + strength**2)

    def _calculate_reward(self, prev_pos: List[int]) -> float:
        """Calculate reward"""
        reward = -0.01  # Small penalty for each step

        # Reward for reaching goal
        if self.agent_pos == self.goal_pos:
            reward += 10.0

        # Reward for getting closer to goal
        prev_dist = abs(prev_pos[0] - self.goal_pos[0]) + abs(prev_pos[1] - self.goal_pos[1])
        curr_dist = abs(self.agent_pos[0] - self.goal_pos[0]) + abs(self.agent_pos[1] - self.goal_pos[1])

        if curr_dist < prev_dist:
            reward += 0.1
        elif curr_dist > prev_dist:
            reward -= 0.1

        # Quantum reward component
        if self.config.use_quantum_reward:
            coherence = np.abs(np.vdot(self.quantum_state, self.quantum_state))
            reward += 0.01 * coherence

        return reward * self.config.reward_scale

    def _get_observation(self) -> np.ndarray:
        """Get current observation"""
        if self.config.use_quantum_observation:
            # Include quantum state information
            real_part = np.real(self.quantum_state)
            imag_part = np.imag(self.quantum_state)

            # Combine into observation
            obs = np.concatenate([
                real_part[:self.config.state_dim // 2],
                imag_part[:self.config.state_dim // 2]
            ]).astype(np.float32)
        else:
            # Classical observation
            obs = np.zeros(self.config.state_dim, dtype=np.float32)
            idx = self._pos_to_idx(self.agent_pos)
            obs[idx] = 1.0

        return obs

    def _pos_to_idx(self, pos: List[int]) -> int:
        """Convert position to state index"""
        return pos[1] * self.grid_size + pos[0]

    def render(self, mode: str = 'human'):
        """Render environment"""
        if mode == 'human':
            grid = [['.' for _ in range(self.grid_size)] for _ in range(self.grid_size)]

            # Place obstacles
            for ox, oy in self.obstacles:
                grid[oy][ox] = '#'

            # Place goal
            grid[self.goal_pos[1]][self.goal_pos[0]] = 'G'

            # Place agent
            grid[self.agent_pos[1]][self.agent_pos[0]] = 'A'

            print('\n'.join(' '.join(row) for row in grid))
            print()

    def close(self):
        """Close environment"""
        pass


class QuantumContinuousControl(Env):
    """
    Continuous control environment with quantum features
    """

    def __init__(self, config: Optional[QuantumEnvConfig] = None):
        super().__init__()
        self.config = config or QuantumEnvConfig()

        # State variables
        self.position = np.zeros(2)
        self.velocity = np.zeros(2)
        self.target = np.array([5.0, 5.0])

        # Episode tracking
        self.steps = 0
        self.total_reward = 0.0

        # Quantum state
        self.quantum_position = np.zeros(2, dtype=complex)
        self.quantum_momentum = np.zeros(2, dtype=complex)

        # Spaces
        obs_dim = self.config.state_dim
        self.observation_space = QuantumObservationSpace((obs_dim,), dtype=np.float32)

        # Continuous action space
        if gym_module:
            self.action_space = gym_module.spaces.Box(
                low=-1.0, high=1.0, shape=(self.config.action_dim,), dtype=np.float32
            )
        else:
            self.action_space = QuantumObservationSpace(
                (self.config.action_dim,), dtype=np.float32
            )

        logger.info("QuantumContinuousControl initialized")

    def reset(self, seed: Optional[int] = None, **kwargs) -> Tuple[np.ndarray, Dict]:
        """Reset environment"""
        if seed is not None:
            np.random.seed(seed)

        self.position = np.random.randn(2) * 2
        self.velocity = np.zeros(2)
        self.target = np.random.randn(2) * 5
        self.steps = 0
        self.total_reward = 0.0

        # Initialize quantum state
        self.quantum_position = self.position.astype(complex)
        self.quantum_momentum = np.zeros(2, dtype=complex)

        observation = self._get_observation()
        info = {"target": self.target.copy()}

        return observation, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute action"""
        self.steps += 1

        # Apply force
        force = np.clip(action[:2], -1.0, 1.0) * 0.5

        # Update velocity and position
        self.velocity += force * 0.1
        self.velocity *= 0.95  # Damping
        self.position += self.velocity * 0.1

        # Update quantum state
        self._update_quantum_state(force)

        # Calculate reward
        reward = self._calculate_reward()
        self.total_reward += reward

        # Check termination
        distance = np.linalg.norm(self.position - self.target)
        terminated = distance < 0.5
        truncated = self.steps >= self.config.max_steps

        observation = self._get_observation()
        info = {
            "steps": self.steps,
            "total_reward": self.total_reward,
            "distance": distance,
            "position": self.position.copy()
        }

        return observation, reward, terminated, truncated, info

    def _update_quantum_state(self, force: np.ndarray):
        """Update quantum state"""
        # Position-momentum uncertainty relation
        delta_x = 0.1
        delta_p = 0.5 / delta_x  # Heisenberg uncertainty

        # Update quantum position
        self.quantum_position += (force * 0.1).astype(complex)
        self.quantum_position += delta_x * (np.random.randn(2) + 1j * np.random.randn(2))

        # Update quantum momentum
        self.quantum_momentum += (force * 0.5).astype(complex)
        self.quantum_momentum += delta_p * (np.random.randn(2) + 1j * np.random.randn(2))

    def _calculate_reward(self) -> float:
        """Calculate reward"""
        distance = np.linalg.norm(self.position - self.target)

        # Distance-based reward
        reward = -distance * 0.1

        # Bonus for reaching target
        if distance < 0.5:
            reward += 10.0

        # Penalty for high velocity
        reward -= np.linalg.norm(self.velocity) * 0.01

        return reward * self.config.reward_scale

    def _get_observation(self) -> np.ndarray:
        """Get observation"""
        obs = np.zeros(self.config.state_dim, dtype=np.float32)

        # Classical state
        obs[:2] = self.position.astype(np.float32)
        obs[2:4] = self.velocity.astype(np.float32)
        obs[4:6] = (self.target - self.position).astype(np.float32)

        # Quantum state
        if self.config.use_quantum_observation:
            obs[6:8] = np.real(self.quantum_position).astype(np.float32)
            obs[8:10] = np.imag(self.quantum_position).astype(np.float32)

        return obs

    def render(self, mode: str = 'human'):
        """Render environment"""
        if mode == 'human':
            print(f"Position: {self.position}, Target: {self.target}, "
                  f"Distance: {np.linalg.norm(self.position - self.target):.2f}")

    def close(self):
        """Close environment"""
        pass


class QuantumMultiAgentEnv(Env):
    """
    Multi-agent environment with quantum entanglement
    """

    def __init__(
        self,
        num_agents: int = 2,
        config: Optional[QuantumEnvConfig] = None
    ):
        super().__init__()
        self.config = config or QuantumEnvConfig()
        self.num_agents = num_agents

        # Agent states
        self.agent_positions = [np.zeros(2) for _ in range(num_agents)]
        self.agent_velocities = [np.zeros(2) for _ in range(num_agents)]

        # Shared quantum state
        self.shared_quantum_state = np.zeros(num_agents * 2, dtype=complex)
        self.shared_quantum_state[0] = 1.0

        # Episode tracking
        self.steps = 0

        # Spaces
        obs_dim = self.config.state_dim * num_agents
        self.observation_space = QuantumObservationSpace((obs_dim,), dtype=np.float32)
        self.action_space = QuantumActionSpace(
            self.config.action_dim * num_agents,
            use_superposition=self.config.use_superposition_actions
        )

        logger.info(f"QuantumMultiAgentEnv initialized with {num_agents} agents")

    def reset(self, seed: Optional[int] = None, **kwargs) -> Tuple[np.ndarray, Dict]:
        """Reset environment"""
        if seed is not None:
            np.random.seed(seed)

        for i in range(self.num_agents):
            self.agent_positions[i] = np.random.randn(2) * 3
            self.agent_velocities[i] = np.zeros(2)

        self.shared_quantum_state = np.zeros(self.num_agents * 2, dtype=complex)
        self.shared_quantum_state[0] = 1.0
        self.steps = 0

        observation = self._get_observation()
        info = {"num_agents": self.num_agents}

        return observation, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute action for all agents"""
        self.steps += 1

        # Decode actions for each agent
        actions_per_agent = self.config.action_dim
        agent_actions = []

        for i in range(self.num_agents):
            agent_action = (action // (actions_per_agent ** i)) % actions_per_agent
            agent_actions.append(agent_action)

        # Update each agent
        for i, act in enumerate(agent_actions):
            force = np.zeros(2)
            if act == 0:
                force = np.array([0.1, 0])
            elif act == 1:
                force = np.array([-0.1, 0])
            elif act == 2:
                force = np.array([0, 0.1])
            elif act == 3:
                force = np.array([0, -0.1])

            self.agent_velocities[i] += force
            self.agent_velocities[i] *= 0.9
            self.agent_positions[i] += self.agent_velocities[i]

        # Update shared quantum state
        self._update_shared_quantum_state()

        # Calculate reward (cooperative)
        reward = self._calculate_reward()

        # Check termination
        terminated = False
        truncated = self.steps >= self.config.max_steps

        observation = self._get_observation()
        info = {"steps": self.steps, "agent_positions": [p.copy() for p in self.agent_positions]}

        return observation, reward, terminated, truncated, info

    def _update_shared_quantum_state(self):
        """Update shared entangled quantum state"""
        # Apply entangling operation
        for i in range(0, len(self.shared_quantum_state) - 1, 2):
            # CNOT-like operation
            temp = self.shared_quantum_state[i]
            self.shared_quantum_state[i] = (temp + self.shared_quantum_state[i + 1]) / np.sqrt(2)
            self.shared_quantum_state[i + 1] = (temp - self.shared_quantum_state[i + 1]) / np.sqrt(2)

    def _calculate_reward(self) -> float:
        """Calculate cooperative reward"""
        # Reward for agents being close together
        total_distance = 0.0
        for i in range(self.num_agents):
            for j in range(i + 1, self.num_agents):
                dist = np.linalg.norm(self.agent_positions[i] - self.agent_positions[j])
                total_distance += dist

        # Negative reward for distance (want agents to stay together)
        reward = -total_distance * 0.1

        # Bonus for quantum coherence
        coherence = np.abs(np.vdot(self.shared_quantum_state, self.shared_quantum_state))
        reward += 0.01 * coherence

        return reward

    def _get_observation(self) -> np.ndarray:
        """Get observation for all agents"""
        obs_list = []

        for i in range(self.num_agents):
            agent_obs = np.zeros(self.config.state_dim, dtype=np.float32)
            agent_obs[:2] = self.agent_positions[i].astype(np.float32)
            agent_obs[2:4] = self.agent_velocities[i].astype(np.float32)
            obs_list.append(agent_obs)

        # Add shared quantum state
        quantum_obs = np.concatenate([
            np.real(self.shared_quantum_state),
            np.imag(self.shared_quantum_state)
        ]).astype(np.float32)

        return np.concatenate(obs_list + [quantum_obs])

    def render(self, mode: str = 'human'):
        """Render environment"""
        if mode == 'human':
            for i, pos in enumerate(self.agent_positions):
                print(f"Agent {i}: {pos}")
            print()

    def close(self):
        """Close environment"""
        pass


def make_quantum_env(env_name: str, **kwargs) -> Env:
    """
    Factory function to create quantum environments

    Args:
        env_name: Environment name
        **kwargs: Additional arguments

    Returns:
        Quantum environment instance
    """
    config = QuantumEnvConfig(**kwargs)

    if env_name == "QuantumGridWorld":
        return QuantumGridWorld(config)
    elif env_name == "QuantumContinuousControl":
        return QuantumContinuousControl(config)
    elif env_name.startswith("QuantumMultiAgent"):
        num_agents = kwargs.get("num_agents", 2)
        return QuantumMultiAgentEnv(num_agents, config)
    else:
        raise ValueError(f"Unknown environment: {env_name}")


# Register environments
if gym_module:
    try:
        gym_module.register(
            id="QuantumGridWorld-v0",
            entry_point="quantum_env_gym:QuantumGridWorld"
        )
        gym_module.register(
            id="QuantumContinuousControl-v0",
            entry_point="quantum_env_gym:QuantumContinuousControl"
        )
        logger.info("Quantum environments registered with gym")
    except Exception as e:
        logger.warning(f"Could not register environments: {e}")


# Example usage
if __name__ == "__main__":
    print("Testing QuantumGridWorld...")

    env = QuantumGridWorld(QuantumEnvConfig(state_dim=16, max_steps=100))
    obs, info = env.reset(seed=42)

    total_reward = 0.0
    for step in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        if step % 20 == 0:
            print(f"Step {step}: reward={reward:.2f}, total={total_reward:.2f}")

        if terminated or truncated:
            print(f"Episode finished at step {step}")
            break

    env.render()
    env.close()

    print("\n\nTesting QuantumContinuousControl...")

    env = QuantumContinuousControl(QuantumEnvConfig(state_dim=16))
    obs, info = env.reset(seed=42)

    for step in range(50):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        if step % 10 == 0:
            print(f"Step {step}: distance={info['distance']:.2f}, reward={reward:.2f}")

        if terminated or truncated:
            break

    env.close()
