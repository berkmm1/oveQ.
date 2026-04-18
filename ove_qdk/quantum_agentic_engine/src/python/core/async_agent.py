#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Async Agent Implementation
Asynchronous quantum agent for concurrent episode execution with worker pool pattern
"""

import asyncio
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from functools import partial
import copy

from core.agent_host import QuantumAgentHost, AgentConfig, AgentState, Experience, AgentMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncExecutionMode(Enum):
    """Async execution modes"""
    THREAD_POOL = auto()
    PROCESS_POOL = auto()
    ASYNCIO_NATIVE = auto()
    HYBRID = auto()


@dataclass
class AsyncAgentConfig:
    """Configuration for async quantum agent"""
    max_concurrent_episodes: int = 8
    execution_mode: AsyncExecutionMode = AsyncExecutionMode.THREAD_POOL
    thread_pool_size: int = 16
    process_pool_size: int = 4
    batch_size: int = 32
    queue_size: int = 100
    timeout_seconds: float = 300.0
    enable_priority_scheduling: bool = True
    enable_work_stealing: bool = True
    checkpoint_interval: int = 100
    enable_dynamic_scaling: bool = True
    min_workers: int = 2
    max_workers: int = 32
    worker_scaling_threshold: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "MaxConcurrentEpisodes": self.max_concurrent_episodes,
            "ExecutionMode": self.execution_mode.name,
            "ThreadPoolSize": self.thread_pool_size,
            "ProcessPoolSize": self.process_pool_size,
            "BatchSize": self.batch_size,
            "QueueSize": self.queue_size,
            "TimeoutSeconds": self.timeout_seconds,
            "EnablePriorityScheduling": self.enable_priority_scheduling,
            "EnableWorkStealing": self.enable_work_stealing,
            "CheckpointInterval": self.checkpoint_interval,
            "EnableDynamicScaling": self.enable_dynamic_scaling,
            "MinWorkers": self.min_workers,
            "MaxWorkers": self.max_workers,
            "WorkerScalingThreshold": self.worker_scaling_threshold
        }


@dataclass
class AsyncTask:
    """Async task representation"""
    task_id: int
    episode_id: int
    priority: int
    state: np.ndarray
    timestamp: float
    future: Optional[asyncio.Future] = None
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[Exception] = None


@dataclass
class AsyncMetrics:
    """Metrics for async execution"""
    tasks_submitted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_timeout: int = 0
    average_latency: float = 0.0
    throughput: float = 0.0
    active_workers: int = 0
    queue_depth: int = 0
    worker_utilization: float = 0.0
    scaling_events: int = 0

    def update_latency(self, new_latency: float):
        """Update average latency with exponential moving average"""
        alpha = 0.1
        self.average_latency = (1 - alpha) * self.average_latency + alpha * new_latency

    def calculate_throughput(self, time_window: float):
        """Calculate throughput over time window"""
        if time_window > 0:
            self.throughput = self.tasks_completed / time_window


class AsyncQuantumAgent:
    """
    Asynchronous Quantum Agent with worker pool pattern
    Supports concurrent episode execution with dynamic scaling
    """

    def __init__(self, agent_config: AgentConfig, async_config: Optional[AsyncAgentConfig] = None):
        self.agent_config = agent_config
        self.async_config = async_config or AsyncAgentConfig()

        # Agent pool for concurrent execution
        self.agent_pool: List[QuantumAgentHost] = []
        self.agent_locks: List[asyncio.Lock] = []
        self.agent_status: List[AgentState] = []

        # Task management
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_tasks: Dict[int, AsyncTask] = {}
        self.task_counter: int = 0
        self.task_lock: asyncio.Lock = asyncio.Lock()

        # Executors
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None

        # Metrics
        self.metrics: AsyncMetrics = AsyncMetrics()
        self.metrics_lock: asyncio.Lock = asyncio.Lock()

        # Control
        self.running: bool = False
        self.worker_tasks: List[asyncio.Task] = []
        self.scaling_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None

        # Results
        self.results_buffer: deque = deque(maxlen=10000)

        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize agent pool with locks"""
        logger.info(f"Initializing agent pool with {self.async_config.max_concurrent_episodes} agents")

        for i in range(self.async_config.max_concurrent_episodes):
            agent = QuantumAgentHost(self.agent_config)
            self.agent_pool.append(agent)
            self.agent_locks.append(asyncio.Lock())
            self.agent_status.append(AgentState.INITIALIZED)

        # Initialize executors based on mode
        if self.async_config.execution_mode in [AsyncExecutionMode.THREAD_POOL, AsyncExecutionMode.HYBRID]:
            self.thread_executor = ThreadPoolExecutor(
                max_workers=self.async_config.thread_pool_size,
                thread_name_prefix="quantum_agent_"
            )

        if self.async_config.execution_mode in [AsyncExecutionMode.PROCESS_POOL, AsyncExecutionMode.HYBRID]:
            self.process_executor = ProcessPoolExecutor(
                max_workers=self.async_config.process_pool_size
            )

        logger.info("Agent pool initialized successfully")

    async def start(self):
        """Start the async agent system"""
        logger.info("Starting async quantum agent system")
        self.running = True

        # Start worker tasks
        num_workers = self.async_config.max_concurrent_episodes
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self.worker_tasks.append(task)

        # Start monitoring and scaling tasks
        if self.async_config.enable_dynamic_scaling:
            self.scaling_task = asyncio.create_task(self._dynamic_scaling_loop())

        self.monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"Started {num_workers} worker tasks")

    async def stop(self):
        """Stop the async agent system"""
        logger.info("Stopping async quantum agent system")
        self.running = False

        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()

        if self.scaling_task:
            self.scaling_task.cancel()

        if self.monitor_task:
            self.monitor_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        # Shutdown executors
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)

        if self.process_executor:
            self.process_executor.shutdown(wait=True)

        logger.info("Async quantum agent system stopped")

    async def _worker_loop(self, worker_id: int):
        """Main worker loop for processing tasks"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get task from queue
                priority, task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )

                # Process task
                start_time = time.time()
                await self._process_task(worker_id, task)
                latency = time.time() - start_time

                # Update metrics
                async with self.metrics_lock:
                    self.metrics.tasks_completed += 1
                    self.metrics.update_latency(latency)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                async with self.metrics_lock:
                    self.metrics.tasks_failed += 1

        logger.info(f"Worker {worker_id} stopped")

    async def _process_task(self, worker_id: int, task: AsyncTask):
        """Process a single task"""
        try:
            task.status = "processing"
            self.agent_status[worker_id] = AgentState.PROCESSING

            # Acquire agent lock
            async with self.agent_locks[worker_id]:
                agent = self.agent_pool[worker_id]

                # Process based on task type
                if task.future:
                    result = await task.future
                    task.result = result
                    task.status = "completed"

            self.agent_status[worker_id] = AgentState.INITIALIZED

        except Exception as e:
            task.error = e
            task.status = "failed"
            self.agent_status[worker_id] = AgentState.ERROR
            logger.error(f"Task {task.task_id} failed: {e}")

    async def _dynamic_scaling_loop(self):
        """Dynamic worker scaling based on load"""
        logger.info("Dynamic scaling loop started")

        while self.running:
            try:
                await asyncio.sleep(10.0)  # Check every 10 seconds

                async with self.metrics_lock:
                    utilization = self.metrics.worker_utilization
                    queue_depth = self.metrics.queue_depth

                # Scale up if utilization is high
                if utilization > self.async_config.worker_scaling_threshold:
                    if len(self.worker_tasks) < self.async_config.max_workers:
                        await self._scale_up()

                # Scale down if underutilized
                elif utilization < 0.3 and len(self.worker_tasks) > self.async_config.min_workers:
                    await self._scale_down()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scaling loop error: {e}")

        logger.info("Dynamic scaling loop stopped")

    async def _scale_up(self):
        """Add more workers to the pool"""
        new_worker_id = len(self.worker_tasks)

        # Add new agent
        agent = QuantumAgentHost(self.agent_config)
        self.agent_pool.append(agent)
        self.agent_locks.append(asyncio.Lock())
        self.agent_status.append(AgentState.INITIALIZED)

        # Start new worker task
        task = asyncio.create_task(self._worker_loop(new_worker_id))
        self.worker_tasks.append(task)

        async with self.metrics_lock:
            self.metrics.scaling_events += 1

        logger.info(f"Scaled up: added worker {new_worker_id}")

    async def _scale_down(self):
        """Remove workers from the pool"""
        if len(self.worker_tasks) <= self.async_config.min_workers:
            return

        # Remove last worker
        worker_id = len(self.worker_tasks) - 1
        task = self.worker_tasks.pop()
        task.cancel()

        # Remove agent
        self.agent_pool.pop()
        self.agent_locks.pop()
        self.agent_status.pop()

        logger.info(f"Scaled down: removed worker {worker_id}")

    async def _monitoring_loop(self):
        """Monitor system metrics"""
        logger.info("Monitoring loop started")

        while self.running:
            try:
                await asyncio.sleep(5.0)  # Update every 5 seconds

                async with self.metrics_lock:
                    active = sum(1 for s in self.agent_status if s != AgentState.INITIALIZED)
                    self.metrics.active_workers = active
                    self.metrics.worker_utilization = active / len(self.agent_pool) if self.agent_pool else 0
                    self.metrics.queue_depth = self.task_queue.qsize()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

        logger.info("Monitoring loop stopped")

    async def submit_task(
        self,
        episode_id: int,
        state: np.ndarray,
        priority: int = 5,
        future: Optional[asyncio.Future] = None
    ) -> int:
        """Submit a new task to the queue"""
        async with self.task_lock:
            self.task_counter += 1
            task_id = self.task_counter

        task = AsyncTask(
            task_id=task_id,
            episode_id=episode_id,
            priority=priority,
            state=state.copy(),
            timestamp=time.time(),
            future=future,
            status="submitted"
        )

        # Add to queue with priority
        await self.task_queue.put((priority, task))
        self.active_tasks[task_id] = task

        async with self.metrics_lock:
            self.metrics.tasks_submitted += 1

        logger.debug(f"Submitted task {task_id} for episode {episode_id}")
        return task_id

    async def get_task_status(self, task_id: int) -> Optional[str]:
        """Get status of a task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].status
        return None

    async def get_task_result(self, task_id: int, timeout: Optional[float] = None) -> Optional[Any]:
        """Get result of a completed task"""
        start_time = time.time()

        while True:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.status == "completed":
                    return task.result
                elif task.status == "failed":
                    raise task.error if task.error else Exception("Task failed")

            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"Task {task_id} timed out")

            await asyncio.sleep(0.1)

    async def run_episode_async(
        self,
        agent_idx: int,
        env_step: Callable[[int], Tuple[np.ndarray, float, bool, Dict]],
        reset_env: Callable[[], np.ndarray],
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """Run a single episode asynchronously"""
        episode_start = time.time()
        state = reset_env()
        total_reward = 0.0
        steps = 0
        experiences = []

        try:
            for step in range(max_steps):
                # Perceive state
                encoded_state = await self.perceive_async(agent_idx, state)

                # Process state
                processed = await self.process_state_async(agent_idx, encoded_state)

                # Decide action
                action, q_values = await self.decide_async(agent_idx, processed)

                # Execute action
                next_state, reward, done, info = env_step(action)

                # Store experience
                exp = Experience(
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                    done=done,
                    priority=1.0
                )
                experiences.append(exp)

                total_reward += reward
                steps += 1
                state = next_state

                if done:
                    break

            # Learn from experiences
            if len(experiences) > 0:
                await self.learn_async(agent_idx, experiences)

            episode_time = time.time() - episode_start

            return {
                "total_reward": total_reward,
                "steps": steps,
                "time": episode_time,
                "experiences": len(experiences),
                "success": True
            }

        except Exception as e:
            logger.error(f"Episode failed on agent {agent_idx}: {e}")
            return {
                "total_reward": total_reward,
                "steps": steps,
                "error": str(e),
                "success": False
            }

    async def perceive_async(
        self,
        agent_idx: int,
        state: np.ndarray
    ) -> np.ndarray:
        """Perceive state asynchronously"""
        async with self.agent_locks[agent_idx]:
            agent = self.agent_pool[agent_idx]
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.thread_executor,
                agent.perceive,
                state
            )

    async def process_state_async(
        self,
        agent_idx: int,
        state: np.ndarray
    ) -> np.ndarray:
        """Process state asynchronously"""
        async with self.agent_locks[agent_idx]:
            agent = self.agent_pool[agent_idx]
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.thread_executor,
                agent.process,
                state
            )

    async def decide_async(
        self,
        agent_idx: int,
        processed_state: np.ndarray
    ) -> Tuple[int, np.ndarray]:
        """Decide action asynchronously"""
        async with self.agent_locks[agent_idx]:
            agent = self.agent_pool[agent_idx]
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.thread_executor,
                agent.decide,
                processed_state
            )

    async def learn_async(
        self,
        agent_idx: int,
        experiences: List[Experience]
    ) -> Dict[str, float]:
        """Learn from experiences asynchronously"""
        async with self.agent_locks[agent_idx]:
            agent = self.agent_pool[agent_idx]
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.thread_executor,
                agent.learn,
                experiences
            )

    async def batch_perceive_async(
        self,
        states: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Process multiple states in parallel"""
        tasks = [
            self.perceive_async(i % len(self.agent_pool), state)
            for i, state in enumerate(states)
        ]
        return await asyncio.gather(*tasks)

    async def batch_decide_async(
        self,
        processed_states: List[np.ndarray]
    ) -> List[Tuple[int, np.ndarray]]:
        """Decide actions for multiple states in parallel"""
        tasks = [
            self.decide_async(i % len(self.agent_pool), state)
            for i, state in enumerate(processed_states)
        ]
        return await asyncio.gather(*tasks)

    async def run_parallel_episodes(
        self,
        num_episodes: int,
        env_factory: Callable[[], Any],
        max_steps: int = 1000
    ) -> List[Dict[str, Any]]:
        """Run multiple episodes in parallel"""

        def create_env_step(env):
            def step(action):
                return env.step(action)
            return step

        def create_reset(env):
            def reset():
                return env.reset()
            return reset

        # Create environments
        envs = [env_factory() for _ in range(num_episodes)]

        # Create episode tasks
        tasks = []
        for i, env in enumerate(envs):
            agent_idx = i % len(self.agent_pool)
            task = self.run_episode_async(
                agent_idx,
                create_env_step(env),
                create_reset(env),
                max_steps
            )
            tasks.append(task)

        # Run all episodes
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "episode": i,
                    "error": str(result),
                    "success": False
                })
            else:
                result["episode"] = i
                processed_results.append(result)

        return processed_results

    async def train_async(
        self,
        num_episodes: int,
        env_factory: Callable[[], Any],
        eval_interval: int = 100,
        save_interval: int = 500,
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """Async training loop"""
        logger.info(f"Starting async training for {num_episodes} episodes")

        training_start = time.time()
        episode_results = []
        eval_results = []

        batch_size = self.async_config.batch_size
        num_batches = (num_episodes + batch_size - 1) // batch_size

        for batch_idx in range(num_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, num_episodes)
            batch_count = batch_end - batch_start

            logger.info(f"Processing batch {batch_idx + 1}/{num_batches} ({batch_count} episodes)")

            # Run batch of episodes
            batch_results = await self.run_parallel_episodes(
                batch_count,
                env_factory,
                max_steps
            )

            episode_results.extend(batch_results)

            # Evaluation
            current_episode = batch_end
            if current_episode % eval_interval == 0:
                eval_result = await self.evaluate_async(env_factory, 10, max_steps)
                eval_results.append({
                    "episode": current_episode,
                    **eval_result
                })
                logger.info(f"Eval at episode {current_episode}: {eval_result}")

            # Checkpoint
            if current_episode % save_interval == 0:
                await self.save_checkpoint_async(f"checkpoint_{current_episode}.pkl")

        training_time = time.time() - training_start

        # Calculate statistics
        successful_episodes = [r for r in episode_results if r.get("success", False)]
        total_rewards = [r["total_reward"] for r in successful_episodes]

        return {
            "total_episodes": num_episodes,
            "successful_episodes": len(successful_episodes),
            "failed_episodes": num_episodes - len(successful_episodes),
            "average_reward": np.mean(total_rewards) if total_rewards else 0,
            "std_reward": np.std(total_rewards) if total_rewards else 0,
            "max_reward": max(total_rewards) if total_rewards else 0,
            "min_reward": min(total_rewards) if total_rewards else 0,
            "training_time": training_time,
            "episodes_per_second": num_episodes / training_time if training_time > 0 else 0,
            "eval_results": eval_results
        }

    async def evaluate_async(
        self,
        env_factory: Callable[[], Any],
        num_eval_episodes: int = 10,
        max_steps: int = 1000
    ) -> Dict[str, float]:
        """Evaluate agent asynchronously"""
        results = await self.run_parallel_episodes(
            num_eval_episodes,
            env_factory,
            max_steps
        )

        successful = [r for r in results if r.get("success", False)]
        rewards = [r["total_reward"] for r in successful]
        steps = [r["steps"] for r in successful]

        return {
            "average_reward": np.mean(rewards) if rewards else 0,
            "std_reward": np.std(rewards) if rewards else 0,
            "average_steps": np.mean(steps) if steps else 0,
            "success_rate": len(successful) / num_eval_episodes
        }

    async def save_checkpoint_async(self, filepath: str):
        """Save checkpoint asynchronously"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.thread_executor,
            self._save_checkpoint_sync,
            filepath
        )

    def _save_checkpoint_sync(self, filepath: str):
        """Synchronous checkpoint save"""
        import pickle

        checkpoint = {
            "agent_configs": [agent.config for agent in self.agent_pool],
            "async_config": self.async_config,
            "metrics": self.metrics,
            "task_counter": self.task_counter
        }

        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)

        logger.info(f"Checkpoint saved to {filepath}")

    async def load_checkpoint_async(self, filepath: str):
        """Load checkpoint asynchronously"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.thread_executor,
            self._load_checkpoint_sync,
            filepath
        )

    def _load_checkpoint_sync(self, filepath: str):
        """Synchronous checkpoint load"""
        import pickle

        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)

        self.async_config = checkpoint["async_config"]
        self.metrics = checkpoint["metrics"]
        self.task_counter = checkpoint["task_counter"]

        logger.info(f"Checkpoint loaded from {filepath}")

    def get_metrics(self) -> AsyncMetrics:
        """Get current metrics"""
        return self.metrics

    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        async with self.metrics_lock:
            return {
                "tasks_submitted": self.metrics.tasks_submitted,
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "tasks_timeout": self.metrics.tasks_timeout,
                "average_latency": self.metrics.average_latency,
                "throughput": self.metrics.throughput,
                "active_workers": self.metrics.active_workers,
                "queue_depth": self.metrics.queue_depth,
                "worker_utilization": self.metrics.worker_utilization,
                "scaling_events": self.metrics.scaling_events,
                "pool_size": len(self.agent_pool),
                "worker_statuses": [s.name for s in self.agent_status]
            }


class DistributedAsyncQuantumAgent(AsyncQuantumAgent):
    """
    Distributed version of AsyncQuantumAgent
    Supports multi-node execution with message passing
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        async_config: Optional[AsyncAgentConfig] = None,
        distributed_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(agent_config, async_config)
        self.distributed_config = distributed_config or {}
        self.node_id = self.distributed_config.get("node_id", 0)
        self.total_nodes = self.distributed_config.get("total_nodes", 1)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.neighbor_nodes: List[int] = []

    async def send_message(self, target_node: int, message: Dict[str, Any]):
        """Send message to another node"""
        msg = {
            "source": self.node_id,
            "target": target_node,
            "timestamp": time.time(),
            "data": message
        }
        # In real implementation, this would use network communication
        await self.message_queue.put(msg)

    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from queue"""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    async def synchronize_parameters(self, parameter_server_node: int = 0):
        """Synchronize parameters with parameter server"""
        # Send local parameters to server
        local_params = {
            "node_id": self.node_id,
            "parameters": self._get_local_parameters()
        }
        await self.send_message(parameter_server_node, local_params)

        # Wait for global parameters
        # In real implementation, this would receive updated parameters
        await asyncio.sleep(0.1)

    def _get_local_parameters(self) -> Dict[str, Any]:
        """Get local agent parameters"""
        return {
            "agent_configs": [agent.config for agent in self.agent_pool],
            "metrics": self.metrics
        }


# Factory function
def create_async_agent(
    agent_config: Optional[AgentConfig] = None,
    async_config: Optional[AsyncAgentConfig] = None,
    distributed: bool = False,
    distributed_config: Optional[Dict[str, Any]] = None
) -> Union[AsyncQuantumAgent, DistributedAsyncQuantumAgent]:
    """Factory function to create async agent"""
    agent_cfg = agent_config or AgentConfig()

    if distributed:
        return DistributedAsyncQuantumAgent(agent_cfg, async_config, distributed_config)
    else:
        return AsyncQuantumAgent(agent_cfg, async_config)


# Example usage and testing
async def main():
    """Main async test function"""
    # Create configs
    agent_config = AgentConfig(
        num_perception_qubits=16,
        num_decision_qubits=8,
        num_action_qubits=8,
        learning_rate=0.001
    )

    async_config = AsyncAgentConfig(
        max_concurrent_episodes=4,
        execution_mode=AsyncExecutionMode.THREAD_POOL,
        thread_pool_size=8,
        enable_dynamic_scaling=True
    )

    # Create agent
    agent = create_async_agent(agent_config, async_config)

    # Start system
    await agent.start()

    # Dummy environment factory
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

    def env_factory():
        return DummyEnv()

    # Run training
    results = await agent.train_async(
        num_episodes=100,
        env_factory=env_factory,
        eval_interval=25,
        max_steps=100
    )

    print(f"Training results: {results}")

    # Get metrics
    metrics = await agent.get_detailed_metrics()
    print(f"Final metrics: {metrics}")

    # Stop system
    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
