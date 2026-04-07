#!/usr/bin/env python3
"""
Quantum Agent Manager Module
Manages multiple quantum agents in a multi-agent system
Part of the Quantum Agentic Loop Engine
"""

import asyncio
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
import logging
import json
import time
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()
    TERMINATED = auto()


class AgentRole(Enum):
    """Agent specialization roles"""
    EXPLORER = auto()
    EXPLOITER = auto()
    COORDINATOR = auto()
    LEARNER = auto()
    PLANNER = auto()
    EXECUTOR = auto()
    CRITIC = auto()


@dataclass
class AgentConfig:
    """Configuration for a quantum agent"""
    agent_id: str
    role: AgentRole = AgentRole.EXPLORER
    num_qubits: int = 8
    learning_rate: float = 0.01
    discount_factor: float = 0.99
    epsilon: float = 0.1
    memory_size: int = 10000
    batch_size: int = 32
    update_frequency: int = 100
    use_quantum: bool = True
    use_entanglement: bool = True
    communication_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'role': self.role.name,
            'num_qubits': self.num_qubits,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'epsilon': self.epsilon,
            'memory_size': self.memory_size,
            'batch_size': self.batch_size,
            'update_frequency': self.update_frequency,
            'use_quantum': self.use_quantum,
            'use_entanglement': self.use_entanglement,
            'communication_enabled': self.communication_enabled
        }


@dataclass
class AgentMessage:
    """Message for inter-agent communication"""
    sender_id: str
    receiver_id: Optional[str]  # None for broadcast
    message_type: str
    content: Any
    timestamp: float = field(default_factory=time.time)
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp,
            'priority': self.priority
        }


@dataclass
class AgentState:
    """Current state of an agent"""
    agent_id: str
    status: AgentStatus
    current_task: Optional[str] = None
    current_observation: Optional[np.ndarray] = None
    current_action: Optional[int] = None
    episode_reward: float = 0.0
    total_reward: float = 0.0
    episode_count: int = 0
    step_count: int = 0
    quantum_state: Optional[np.ndarray] = None
    entangled_partners: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'status': self.status.name,
            'current_task': self.current_task,
            'episode_reward': self.episode_reward,
            'total_reward': self.total_reward,
            'episode_count': self.episode_count,
            'step_count': self.step_count,
            'entangled_partners': list(self.entangled_partners)
        }


class QuantumAgent:
    """Individual quantum agent with learning capabilities"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState(
            agent_id=config.agent_id,
            status=AgentStatus.IDLE
        )

        # Memory for experience replay
        self.memory = deque(maxlen=config.memory_size)

        # Quantum circuit parameters
        self.circuit_parameters = np.random.randn(
            config.num_qubits * 3 * 2  # 3 rotations per qubit, 2 layers
        ) * 0.1

        # Classical neural network weights
        self.weights = {
            'W1': np.random.randn(config.num_qubits, 64) * 0.01,
            'b1': np.zeros(64),
            'W2': np.random.randn(64, 32) * 0.01,
            'b2': np.zeros(32),
            'W3': np.random.randn(32, 16) * 0.01,
            'b3': np.zeros(16)
        }

        # Metrics tracking
        self.metrics = {
            'rewards': [],
            'losses': [],
            'episode_lengths': [],
            'success_rate': []
        }

        # Message inbox
        self.message_queue: deque = deque()

        # Task history
        self.task_history: List[Dict[str, Any]] = []

        logger.info(f"Agent {config.agent_id} initialized with role {config.role.name}")

    def perceive(self, observation: np.ndarray) -> np.ndarray:
        """Process observation through quantum encoding"""
        self.state.current_observation = observation

        if self.config.use_quantum:
            # Quantum feature encoding
            encoded = self._quantum_encode(observation)
        else:
            # Classical encoding
            encoded = self._classical_encode(observation)

        return encoded

    def _quantum_encode(self, observation: np.ndarray) -> np.ndarray:
        """Encode observation into quantum state"""
        # Normalize observation
        normalized = (observation - np.mean(observation)) / (np.std(observation) + 1e-8)

        # Map to rotation angles
        angles = np.arctan(normalized) * np.pi

        # Pad or truncate to match qubit count
        if len(angles) < self.config.num_qubits:
            angles = np.pad(angles, (0, self.config.num_qubits - len(angles)))
        else:
            angles = angles[:self.config.num_qubits]

        self.state.quantum_state = angles
        return angles

    def _classical_encode(self, observation: np.ndarray) -> np.ndarray:
        """Classical feature encoding"""
        return np.tanh(observation[:self.config.num_qubits])

    def decide(self, encoded_state: np.ndarray) -> int:
        """Make decision based on encoded state"""
        # Epsilon-greedy action selection
        if np.random.random() < self.config.epsilon:
            action = np.random.randint(16)  # Assume 16 possible actions
        else:
            # Forward pass through network
            q_values = self._forward(encoded_state)
            action = np.argmax(q_values)

        self.state.current_action = action
        return action

    def _forward(self, state: np.ndarray) -> np.ndarray:
        """Neural network forward pass"""
        # Layer 1
        h1 = np.maximum(0, np.dot(state, self.weights['W1']) + self.weights['b1'])

        # Layer 2
        h2 = np.maximum(0, np.dot(h1, self.weights['W2']) + self.weights['b2'])

        # Output layer
        output = np.dot(h2, self.weights['W3']) + self.weights['b3']

        return output

    def act(self, action: int, environment: Any) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action in environment"""
        next_observation, reward, done, info = environment.step(action)

        self.state.episode_reward += reward
        self.state.step_count += 1

        return next_observation, reward, done, info

    def learn(self, batch_size: Optional[int] = None) -> float:
        """Learn from experience"""
        if batch_size is None:
            batch_size = self.config.batch_size

        if len(self.memory) < batch_size:
            return 0.0

        # Sample batch
        indices = np.random.choice(len(self.memory), batch_size, replace=False)
        batch = [self.memory[i] for i in indices]

        # Compute loss and update
        loss = self._update_networks(batch)

        self.metrics['losses'].append(loss)

        return loss

    def _update_networks(self, batch: List[Tuple]) -> float:
        """Update network weights"""
        total_loss = 0.0

        for experience in batch:
            state, action, reward, next_state, done = experience

            # Compute Q-value update
            current_q = self._forward(state)[action]
            next_q = np.max(self._forward(next_state)) if not done else 0
            target_q = reward + self.config.discount_factor * next_q

            # Simple gradient descent update
            loss = (current_q - target_q) ** 2
            total_loss += loss

            # Update weights (simplified)
            gradient = 2 * (current_q - target_q)
            self.weights['W3'][:, action] -= self.config.learning_rate * gradient * 0.01

        return total_loss / len(batch)

    def store_experience(self, experience: Tuple):
        """Store experience in memory"""
        self.memory.append(experience)

    def receive_message(self, message: AgentMessage):
        """Receive message from another agent"""
        self.message_queue.append(message)
        logger.debug(f"Agent {self.config.agent_id} received message from {message.sender_id}")

    def process_messages(self) -> List[AgentMessage]:
        """Process all pending messages"""
        processed = []

        while self.message_queue:
            message = self.message_queue.popleft()

            # Handle different message types
            if message.message_type == "STATE_SHARE":
                # Update based on shared state
                pass
            elif message.message_type == "ACTION_REQUEST":
                # Respond with action recommendation
                pass
            elif message.message_type == "COORDINATION":
                # Update coordination info
                pass

            processed.append(message)

        return processed

    def entangle_with(self, other_agent_id: str):
        """Establish quantum entanglement with another agent"""
        if self.config.use_entanglement:
            self.state.entangled_partners.add(other_agent_id)
            logger.info(f"Agent {self.config.agent_id} entangled with {other_agent_id}")

    def disentangle_from(self, other_agent_id: str):
        """Remove quantum entanglement"""
        self.state.entangled_partners.discard(other_agent_id)

    def get_entangled_state(self) -> Optional[np.ndarray]:
        """Get quantum state for entanglement"""
        if self.state.quantum_state is not None:
            return self.state.quantum_state.copy()
        return None

    def reset_episode(self):
        """Reset for new episode"""
        self.metrics['rewards'].append(self.state.episode_reward)
        self.state.total_reward += self.state.episode_reward
        self.state.episode_count += 1

        self.task_history.append({
            'episode': self.state.episode_count,
            'reward': self.state.episode_reward,
            'steps': self.state.step_count
        })

        self.state.episode_reward = 0.0
        self.state.step_count = 0
        self.state.current_observation = None
        self.state.current_action = None

    def save(self, filepath: str):
        """Save agent state"""
        data = {
            'config': self.config.to_dict(),
            'weights': {k: v.tolist() for k, v in self.weights.items()},
            'circuit_parameters': self.circuit_parameters.tolist(),
            'metrics': self.metrics,
            'task_history': self.task_history
        }

        with open(filepath, 'w') as f:
            json.dump(data, f)

        logger.info(f"Agent {self.config.agent_id} saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'QuantumAgent':
        """Load agent from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        config = AgentConfig(**data['config'])
        agent = cls(config)

        agent.weights = {k: np.array(v) for k, v in data['weights'].items()}
        agent.circuit_parameters = np.array(data['circuit_parameters'])
        agent.metrics = data['metrics']
        agent.task_history = data['task_history']

        logger.info(f"Agent {config.agent_id} loaded from {filepath}")
        return agent


class QuantumAgentManager:
    """Manager for multiple quantum agents"""

    def __init__(self):
        self.agents: Dict[str, QuantumAgent] = {}
        self.message_bus: List[AgentMessage] = []
        self.global_state: Dict[str, Any] = {}
        self.coordinator: Optional[str] = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.lock = threading.Lock()

        # Metrics
        self.system_metrics = {
            'total_episodes': 0,
            'total_steps': 0,
            'average_reward': 0.0,
            'messages_exchanged': 0
        }

        logger.info("Quantum Agent Manager initialized")

    def create_agent(self, config: AgentConfig) -> QuantumAgent:
        """Create a new agent"""
        agent = QuantumAgent(config)

        with self.lock:
            self.agents[config.agent_id] = agent

        # Set first agent as coordinator
        if self.coordinator is None:
            self.coordinator = config.agent_id

        logger.info(f"Created agent {config.agent_id}")
        return agent

    def remove_agent(self, agent_id: str):
        """Remove an agent"""
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Removed agent {agent_id}")

        # Update coordinator if needed
        if self.coordinator == agent_id and self.agents:
            self.coordinator = next(iter(self.agents.keys()))

    def get_agent(self, agent_id: str) -> Optional[QuantumAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, QuantumAgent]:
        """Get all agents"""
        return self.agents.copy()

    def send_message(self, message: AgentMessage):
        """Send message to agent(s)"""
        self.message_bus.append(message)
        self.system_metrics['messages_exchanged'] += 1

        if message.receiver_id is None:
            # Broadcast to all agents
            for agent_id, agent in self.agents.items():
                if agent_id != message.sender_id:
                    agent.receive_message(message)
        else:
            # Send to specific agent
            if message.receiver_id in self.agents:
                self.agents[message.receiver_id].receive_message(message)

    def establish_entanglement(self, agent_id1: str, agent_id2: str):
        """Establish quantum entanglement between two agents"""
        if agent_id1 in self.agents and agent_id2 in self.agents:
            self.agents[agent_id1].entangle_with(agent_id2)
            self.agents[agent_id2].entangle_with(agent_id1)

            # Share quantum states
            state1 = self.agents[agent_id1].get_entangled_state()
            state2 = self.agents[agent_id2].get_entangled_state()

            logger.info(f"Entanglement established between {agent_id1} and {agent_id2}")

    def break_entanglement(self, agent_id1: str, agent_id2: str):
        """Break quantum entanglement"""
        if agent_id1 in self.agents:
            self.agents[agent_id1].disentangle_from(agent_id2)
        if agent_id2 in self.agents:
            self.agents[agent_id2].disentangle_from(agent_id1)

    def run_agent_episode(self, agent_id: str, environment: Any,
                          max_steps: int = 1000) -> float:
        """Run a single episode for an agent"""
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return 0.0

        agent = self.agents[agent_id]
        agent.state.status = AgentStatus.RUNNING

        observation = environment.reset()
        episode_reward = 0.0

        for step in range(max_steps):
            # Perceive
            encoded_state = agent.perceive(observation)

            # Decide
            action = agent.decide(encoded_state)

            # Act
            next_observation, reward, done, info = agent.act(action, environment)

            # Store experience
            experience = (encoded_state, action, reward,
                         agent.perceive(next_observation), done)
            agent.store_experience(experience)

            episode_reward += reward

            # Learn periodically
            if step % agent.config.update_frequency == 0:
                agent.learn()

            # Process messages
            agent.process_messages()

            observation = next_observation

            if done:
                break

        agent.reset_episode()
        agent.state.status = AgentStatus.IDLE

        # Update system metrics
        self.system_metrics['total_episodes'] += 1
        self.system_metrics['total_steps'] += step + 1

        return episode_reward

    def run_parallel_episodes(self, environment_factory: Callable,
                              num_episodes: int = 100,
                              max_steps: int = 1000) -> List[float]:
        """Run episodes in parallel for all agents"""
        rewards = []

        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            futures = []

            for agent_id in self.agents:
                env = environment_factory()
                future = executor.submit(
                    self.run_agent_episode,
                    agent_id,
                    env,
                    max_steps
                )
                futures.append((agent_id, future))

            for agent_id, future in futures:
                try:
                    reward = future.result(timeout=300)
                    rewards.append(reward)
                    logger.info(f"Agent {agent_id} completed episode with reward {reward:.2f}")
                except Exception as e:
                    logger.error(f"Agent {agent_id} episode failed: {e}")

        return rewards

    def coordinate_agents(self, task: str, shared_data: Dict[str, Any]):
        """Coordinate multiple agents for a shared task"""
        if self.coordinator and self.coordinator in self.agents:
            coordinator_agent = self.agents[self.coordinator]

            # Send coordination message to all agents
            for agent_id in self.agents:
                if agent_id != self.coordinator:
                    message = AgentMessage(
                        sender_id=self.coordinator,
                        receiver_id=agent_id,
                        message_type="COORDINATION",
                        content={'task': task, 'data': shared_data}
                    )
                    self.send_message(message)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        agent_metrics = {
            agent_id: {
                'status': agent.state.status.name,
                'episodes': agent.state.episode_count,
                'total_reward': agent.state.total_reward,
                'entangled_with': list(agent.state.entangled_partners)
            }
            for agent_id, agent in self.agents.items()
        }

        return {
            'system': self.system_metrics,
            'agents': agent_metrics,
            'num_agents': len(self.agents),
            'coordinator': self.coordinator
        }

    def save_all(self, directory: str):
        """Save all agents"""
        Path(directory).mkdir(parents=True, exist_ok=True)

        for agent_id, agent in self.agents.items():
            filepath = Path(directory) / f"{agent_id}.json"
            agent.save(str(filepath))

        # Save system state
        system_data = {
            'global_state': self.global_state,
            'coordinator': self.coordinator,
            'system_metrics': self.system_metrics
        }

        with open(Path(directory) / 'system_state.json', 'w') as f:
            json.dump(system_data, f)

        logger.info(f"All agents saved to {directory}")

    def load_all(self, directory: str):
        """Load all agents"""
        import glob

        agent_files = glob.glob(str(Path(directory) / "*.json"))

        for filepath in agent_files:
            if 'system_state' not in filepath:
                agent = QuantumAgent.load(filepath)
                self.agents[agent.config.agent_id] = agent

        # Load system state
        system_file = Path(directory) / 'system_state.json'
        if system_file.exists():
            with open(system_file, 'r') as f:
                system_data = json.load(f)
                self.global_state = system_data.get('global_state', {})
                self.coordinator = system_data.get('coordinator')
                self.system_metrics = system_data.get('system_metrics', {})

        logger.info(f"Loaded {len(self.agents)} agents from {directory}")

    def shutdown(self):
        """Shutdown the manager and all agents"""
        self.running = False

        for agent in self.agents.values():
            agent.state.status = AgentStatus.TERMINATED

        self.executor.shutdown(wait=True)
        logger.info("Quantum Agent Manager shutdown complete")


# Factory functions
def create_explorer_agent(agent_id: str, num_qubits: int = 8) -> QuantumAgent:
    """Create an exploration-focused agent"""
    config = AgentConfig(
        agent_id=agent_id,
        role=AgentRole.EXPLORER,
        num_qubits=num_qubits,
        epsilon=0.3,  # High exploration
        learning_rate=0.01
    )
    return QuantumAgent(config)


def create_exploiter_agent(agent_id: str, num_qubits: int = 8) -> QuantumAgent:
    """Create an exploitation-focused agent"""
    config = AgentConfig(
        agent_id=agent_id,
        role=AgentRole.EXPLOITER,
        num_qubits=num_qubits,
        epsilon=0.05,  # Low exploration
        learning_rate=0.005
    )
    return QuantumAgent(config)


def create_coordinator_agent(agent_id: str, num_qubits: int = 8) -> QuantumAgent:
    """Create a coordinator agent"""
    config = AgentConfig(
        agent_id=agent_id,
        role=AgentRole.COORDINATOR,
        num_qubits=num_qubits,
        communication_enabled=True,
        use_entanglement=True
    )
    return QuantumAgent(config)


def create_learner_agent(agent_id: str, num_qubits: int = 8) -> QuantumAgent:
    """Create a learning-focused agent"""
    config = AgentConfig(
        agent_id=agent_id,
        role=AgentRole.LEARNER,
        num_qubits=num_qubits,
        learning_rate=0.02,
        memory_size=50000,
        batch_size=64
    )
    return QuantumAgent(config)


if __name__ == "__main__":
    print("Quantum Agent Manager Module")
    print("=" * 40)

    # Create manager
    manager = QuantumAgentManager()

    # Create agents
    explorer = create_explorer_agent("explorer_1", num_qubits=8)
    exploiter = create_exploiter_agent("exploiter_1", num_qubits=8)
    coordinator = create_coordinator_agent("coordinator_1", num_qubits=8)

    manager.create_agent(explorer.config)
    manager.create_agent(exploiter.config)
    manager.create_agent(coordinator.config)

    # Establish entanglement
    manager.establish_entanglement("explorer_1", "exploiter_1")

    # Print metrics
    print("\nSystem Metrics:")
    metrics = manager.get_system_metrics()
    print(json.dumps(metrics, indent=2))
