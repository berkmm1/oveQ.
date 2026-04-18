"""
Distributed Quantum Computing
============================

Distributed quantum computing capabilities for:
- Parallel circuit execution
- Distributed training
- Quantum task scheduling
- Result aggregation
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue, Empty
import threading
import time
import uuid
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of distributed task."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class DistributionStrategy(Enum):
    """Strategies for distributing quantum tasks."""
    ROUND_ROBIN = auto()
    LEAST_LOADED = auto()
    DATA_LOCALITY = auto()
    PRIORITY_BASED = auto()


@dataclass
class QuantumTask:
    """Represents a quantum computing task."""
    task_id: str
    circuit: Any
    parameters: Dict[str, Any]
    shots: int = 1024
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    backend: str = "simulator"
    estimated_runtime: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class WorkerNode:
    """Represents a worker node in distributed system."""
    node_id: str
    host: str
    port: int
    num_qubits: int
    max_concurrent: int = 4
    current_load: int = 0
    total_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    is_active: bool = True
    capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DistributedResult:
    """Result from distributed execution."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    execution_time: float = 0.0
    worker_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class QuantumTaskScheduler:
    """
    Scheduler for distributed quantum tasks.

    Manages task queue, worker assignment, and result collection.
    """

    def __init__(self, strategy: DistributionStrategy = DistributionStrategy.LEAST_LOADED):
        """
        Initialize task scheduler.

        Args:
            strategy: Task distribution strategy
        """
        self.strategy = strategy
        self._task_queue: Queue = Queue()
        self._pending_tasks: Dict[str, QuantumTask] = {}
        self._running_tasks: Dict[str, QuantumTask] = {}
        self._completed_tasks: Dict[str, QuantumTask] = {}
        self._workers: Dict[str, WorkerNode] = {}
        self._lock = threading.Lock()
        self._shutdown = False

        # Statistics
        self._total_submitted = 0
        self._total_completed = 0
        self._total_failed = 0

    def register_worker(self, worker: WorkerNode) -> None:
        """Register a worker node."""
        with self._lock:
            self._workers[worker.node_id] = worker
        logger.info(f"Registered worker: {worker.node_id}")

    def unregister_worker(self, node_id: str) -> None:
        """Unregister a worker node."""
        with self._lock:
            if node_id in self._workers:
                del self._workers[node_id]
        logger.info(f"Unregistered worker: {node_id}")

    def submit_task(self, task: QuantumTask) -> str:
        """
        Submit a task for execution.

        Args:
            task: Task to execute

        Returns:
            Task ID
        """
        if not task.task_id:
            task.task_id = str(uuid.uuid4())

        with self._lock:
            self._pending_tasks[task.task_id] = task
            self._task_queue.put(task)
            self._total_submitted += 1

        logger.debug(f"Submitted task: {task.task_id}")
        return task.task_id

    def submit_batch(self, tasks: List[QuantumTask]) -> List[str]:
        """Submit multiple tasks."""
        return [self.submit_task(task) for task in tasks]

    def get_next_task(self) -> Optional[QuantumTask]:
        """Get next task for execution."""
        try:
            return self._task_queue.get(timeout=1.0)
        except Empty:
            return None

    def assign_task(self, task: QuantumTask) -> Optional[str]:
        """
        Assign task to a worker.

        Args:
            task: Task to assign

        Returns:
            Worker ID or None if no worker available
        """
        with self._lock:
            available_workers = [w for w in self._workers.values()
                               if w.is_active and w.current_load < w.max_concurrent]

            if not available_workers:
                return None

            if self.strategy == DistributionStrategy.ROUND_ROBIN:
                worker = available_workers[self._total_submitted % len(available_workers)]
            elif self.strategy == DistributionStrategy.LEAST_LOADED:
                worker = min(available_workers, key=lambda w: w.current_load)
            elif self.strategy == DistributionStrategy.DATA_LOCALITY:
                # Simplified: just use first available
                worker = available_workers[0]
            else:  # PRIORITY_BASED
                worker = max(available_workers, key=lambda w: w.capabilities.get('priority', 0))

            worker.current_load += 1
            return worker.node_id

    def complete_task(self, task_id: str, result: Any,
                     worker_id: str, execution_time: float) -> None:
        """Mark task as completed."""
        with self._lock:
            if task_id in self._running_tasks:
                task = self._running_tasks.pop(task_id)
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = time.time()

                self._completed_tasks[task_id] = task
                self._total_completed += 1

                # Update worker stats
                if worker_id in self._workers:
                    worker = self._workers[worker_id]
                    worker.current_load -= 1
                    worker.total_executions += 1
                    # Update average execution time
                    n = worker.total_executions
                    worker.average_execution_time = (
                        (worker.average_execution_time * (n - 1) + execution_time) / n
                    )

        logger.debug(f"Completed task: {task_id}")

    def fail_task(self, task_id: str, error: str, worker_id: str) -> None:
        """Mark task as failed."""
        with self._lock:
            if task_id in self._running_tasks:
                task = self._running_tasks.pop(task_id)
                task.status = TaskStatus.FAILED
                task.error = error
                task.completed_at = time.time()

                self._completed_tasks[task_id] = task
                self._total_failed += 1

                if worker_id in self._workers:
                    worker = self._workers[worker_id]
                    worker.current_load -= 1
                    worker.failed_executions += 1

        logger.error(f"Failed task: {task_id}, error: {error}")

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a task."""
        with self._lock:
            if task_id in self._pending_tasks:
                return TaskStatus.PENDING
            elif task_id in self._running_tasks:
                return TaskStatus.RUNNING
            elif task_id in self._completed_tasks:
                return self._completed_tasks[task_id].status
        return None

    def get_result(self, task_id: str) -> Optional[Any]:
        """Get result of a completed task."""
        with self._lock:
            if task_id in self._completed_tasks:
                return self._completed_tasks[task_id].result
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        with self._lock:
            return {
                'total_submitted': self._total_submitted,
                'total_completed': self._total_completed,
                'total_failed': self._total_failed,
                'pending': len(self._pending_tasks),
                'running': len(self._running_tasks),
                'completed': len(self._completed_tasks),
                'workers': len(self._workers),
                'active_workers': sum(1 for w in self._workers.values() if w.is_active)
            }


class DistributedQuantumExecutor:
    """
    Executor for distributed quantum computing.

    Manages parallel execution of quantum circuits across multiple workers.
    """

    def __init__(self, max_workers: int = None,
                 scheduler: Optional[QuantumTaskScheduler] = None):
        """
        Initialize distributed executor.

        Args:
            max_workers: Maximum number of worker processes
            scheduler: Optional task scheduler
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.scheduler = scheduler or QuantumTaskScheduler()
        self._executor: Optional[ProcessPoolExecutor] = None
        self._futures: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        """Start the executor."""
        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self._running = True
        logger.info(f"Distributed executor started with {self.max_workers} workers")

    def stop(self) -> None:
        """Stop the executor."""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=True)
        logger.info("Distributed executor stopped")

    def execute(self, circuit: Any, shots: int = 1024,
                parameters: Optional[Dict] = None) -> DistributedResult:
        """
        Execute a circuit.

        Args:
            circuit: Quantum circuit
            shots: Number of shots
            parameters: Circuit parameters

        Returns:
            Execution result
        """
        task = QuantumTask(
            task_id=str(uuid.uuid4()),
            circuit=circuit,
            parameters=parameters or {},
            shots=shots
        )

        return self.execute_task(task)

    def execute_task(self, task: QuantumTask) -> DistributedResult:
        """Execute a task."""
        if not self._running:
            self.start()

        # Submit to scheduler
        self.scheduler.submit_task(task)

        # Execute
        start_time = time.time()

        try:
            # Simplified: directly execute
            result = self._execute_circuit(task.circuit, task.parameters, task.shots)

            execution_time = time.time() - start_time

            return DistributedResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            return DistributedResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )

    def execute_batch(self, circuits: List[Any], shots: int = 1024,
                     parameters: Optional[List[Dict]] = None) -> List[DistributedResult]:
        """
        Execute multiple circuits in parallel.

        Args:
            circuits: List of circuits
            shots: Number of shots per circuit
            parameters: List of parameters for each circuit

        Returns:
            List of execution results
        """
        if not self._running:
            self.start()

        # Create tasks
        tasks = []
        for i, circuit in enumerate(circuits):
            params = parameters[i] if parameters and i < len(parameters) else {}
            task = QuantumTask(
                task_id=str(uuid.uuid4()),
                circuit=circuit,
                parameters=params,
                shots=shots
            )
            tasks.append(task)

        # Submit all tasks
        task_ids = self.scheduler.submit_batch(tasks)

        # Execute in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.execute_task, task): task.task_id
                for task in tasks
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        return results

    def _execute_circuit(self, circuit: Any, parameters: Dict, shots: int) -> Any:
        """Execute a single circuit."""
        from core.quantum_backend import get_backend_manager
        backend = get_backend_manager().get_backend()

        # Resolve parameters if needed
        # Actual execution using the backend
        result = backend.execute(circuit, parameters)

        return {
            'counts': result.counts,
            'probabilities': result.probabilities,
            'shots': shots,
            'execution_time': result.execution_time
        }

    def map_reduce(self, circuits: List[Any],
                   map_func: Callable[[Any], Any],
                   reduce_func: Callable[[List[Any]], Any]) -> Any:
        """
        Map-reduce pattern for quantum circuits.

        Args:
            circuits: List of circuits to process
            map_func: Function to apply to each circuit
            reduce_func: Function to reduce results

        Returns:
            Reduced result
        """
        # Map phase
        map_results = []
        for circuit in circuits:
            result = map_func(circuit)
            map_results.append(result)

        # Reduce phase
        return reduce_func(map_results)


class ParameterServer:
    """
    Parameter server for distributed quantum training.

    Manages shared parameters across multiple workers.
    """

    def __init__(self, initial_params: Optional[np.ndarray] = None):
        """
        Initialize parameter server.

        Args:
            initial_params: Initial parameter values
        """
        self._params = initial_params
        self._gradients: Dict[str, np.ndarray] = {}
        self._update_count = 0
        self._lock = threading.Lock()

    def get_params(self) -> Optional[np.ndarray]:
        """Get current parameters."""
        with self._lock:
            return self._params.copy() if self._params is not None else None

    def set_params(self, params: np.ndarray) -> None:
        """Set parameters."""
        with self._lock:
            self._params = params.copy()

    def submit_gradient(self, worker_id: str, gradient: np.ndarray) -> None:
        """
        Submit gradient from a worker.

        Args:
            worker_id: Worker identifier
            gradient: Computed gradient
        """
        with self._lock:
            self._gradients[worker_id] = gradient

    def aggregate_gradients(self, method: str = 'mean') -> Optional[np.ndarray]:
        """
        Aggregate gradients from all workers.

        Args:
            method: Aggregation method ('mean', 'sum')

        Returns:
            Aggregated gradient
        """
        with self._lock:
            if not self._gradients:
                return None

            gradients = list(self._gradients.values())

            if method == 'mean':
                return np.mean(gradients, axis=0)
            elif method == 'sum':
                return np.sum(gradients, axis=0)
            else:
                raise ValueError(f"Unknown aggregation method: {method}")

    def update_params(self, learning_rate: float,
                     aggregated_gradient: np.ndarray) -> None:
        """
        Update parameters using aggregated gradient.

        Args:
            learning_rate: Learning rate
            aggregated_gradient: Aggregated gradient
        """
        with self._lock:
            if self._params is not None:
                self._params -= learning_rate * aggregated_gradient
                self._update_count += 1

    def clear_gradients(self) -> None:
        """Clear all submitted gradients."""
        with self._lock:
            self._gradients.clear()

    def get_update_count(self) -> int:
        """Get number of parameter updates."""
        with self._lock:
            return self._update_count


class DistributedTrainer:
    """
    Distributed trainer for quantum machine learning.

    Coordinates training across multiple workers using parameter server.
    """

    def __init__(self, parameter_server: ParameterServer,
                 num_workers: int = 4,
                 batch_size: int = 32):
        """
        Initialize distributed trainer.

        Args:
            parameter_server: Parameter server instance
            num_workers: Number of training workers
            batch_size: Batch size per worker
        """
        self.parameter_server = parameter_server
        self.num_workers = num_workers
        self.batch_size = batch_size
        self._executor = DistributedQuantumExecutor(max_workers=num_workers)

    def train_epoch(self, data: List[Any], labels: List[Any],
                   learning_rate: float) -> Dict[str, Any]:
        """
        Train for one epoch.

        Args:
            data: Training data
            labels: Training labels
            learning_rate: Learning rate

        Returns:
            Training metrics
        """
        # Split data among workers
        chunk_size = len(data) // self.num_workers
        data_chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
        label_chunks = [labels[i:i+chunk_size] for i in range(0, len(labels), chunk_size)]

        # Each worker computes gradient
        worker_gradients = []

        for worker_id, (data_chunk, label_chunk) in enumerate(zip(data_chunks, label_chunks)):
            gradient = self._compute_gradient(worker_id, data_chunk, label_chunk)
            worker_gradients.append(gradient)

        # Submit gradients to parameter server
        for worker_id, gradient in enumerate(worker_gradients):
            self.parameter_server.submit_gradient(str(worker_id), gradient)

        # Aggregate and update
        aggregated = self.parameter_server.aggregate_gradients('mean')
        self.parameter_server.update_params(learning_rate, aggregated)
        self.parameter_server.clear_gradients()

        return {
            'epoch_complete': True,
            'num_workers': self.num_workers,
            'update_count': self.parameter_server.get_update_count()
        }

    def _compute_gradient(self, worker_id: int, data: List, labels: List) -> np.ndarray:
        """Compute gradient for a worker."""
        # Get current parameters
        params = self.parameter_server.get_params()

        # Compute gradient (simplified)
        if params is not None:
            # Placeholder: random gradient
            return np.random.randn(*params.shape) * 0.01

        return np.array([])


class ResultAggregator:
    """
    Aggregator for distributed quantum results.

    Combines results from multiple circuit executions.
    """

    @staticmethod
    def aggregate_counts(results: List[Dict[str, int]]) -> Dict[str, int]:
        """
        Aggregate measurement counts from multiple runs.

        Args:
            results: List of count dictionaries

        Returns:
            Aggregated counts
        """
        aggregated = defaultdict(int)

        for result in results:
            for bitstring, count in result.items():
                aggregated[bitstring] += count

        return dict(aggregated)

    @staticmethod
    def aggregate_expectation_values(results: List[float],
                                     method: str = 'mean') -> float:
        """
        Aggregate expectation values.

        Args:
            results: List of expectation values
            method: Aggregation method

        Returns:
            Aggregated value
        """
        if method == 'mean':
            return np.mean(results)
        elif method == 'median':
            return np.median(results)
        elif method == 'weighted_mean':
            # Weight by inverse variance
            weights = [1.0 / (r ** 2 + 1e-10) for r in results]
            return np.average(results, weights=weights)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

    @staticmethod
    def aggregate_probabilities(results: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Aggregate probabilities from multiple runs.

        Args:
            results: List of probability dictionaries

        Returns:
            Aggregated probabilities
        """
        aggregated = defaultdict(float)

        for result in results:
            for bitstring, prob in result.items():
                aggregated[bitstring] += prob

        # Normalize
        total = sum(aggregated.values())
        if total > 0:
            return {k: v / total for k, v in aggregated.items()}

        return dict(aggregated)

    @staticmethod
    def bootstrap_statistics(results: List[float],
                            num_bootstrap: int = 1000) -> Dict[str, float]:
        """
        Compute bootstrap statistics.

        Args:
            results: List of values
            num_bootstrap: Number of bootstrap samples

        Returns:
            Statistics dictionary
        """
        results_array = np.array(results)
        bootstrap_means = []

        for _ in range(num_bootstrap):
            sample = np.random.choice(results_array, size=len(results_array), replace=True)
            bootstrap_means.append(np.mean(sample))

        bootstrap_means = np.array(bootstrap_means)

        return {
            'mean': np.mean(results_array),
            'std': np.std(results_array),
            'bootstrap_mean': np.mean(bootstrap_means),
            'bootstrap_std': np.std(bootstrap_means),
            'ci_lower': np.percentile(bootstrap_means, 2.5),
            'ci_upper': np.percentile(bootstrap_means, 97.5)
        }


def parallel_execute(circuits: List[Any],
                    shots: int = 1024,
                    max_workers: int = None) -> List[DistributedResult]:
    """
    Execute circuits in parallel.

    Args:
        circuits: List of circuits
        shots: Number of shots per circuit
        max_workers: Maximum number of workers

    Returns:
        List of execution results
    """
    executor = DistributedQuantumExecutor(max_workers=max_workers)
    return executor.execute_batch(circuits, shots)


def distributed_vqe(hamiltonian: Any,
                   ansatz: Any,
                   num_workers: int = 4,
                   iterations: int = 100) -> Dict[str, Any]:
    """
    Distributed VQE optimization.

    Args:
        hamiltonian: Hamiltonian operator
        ansatz: Variational ansatz
        num_workers: Number of workers
        iterations: Number of optimization iterations

    Returns:
        Optimization results
    """
    # Initialize parameter server
    param_server = ParameterServer()

    # Create trainer
    trainer = DistributedTrainer(param_server, num_workers)

    # Training loop (simplified)
    for iteration in range(iterations):
        # Mock data
        data = [1] * 100
        labels = [0] * 100

        metrics = trainer.train_epoch(data, labels, learning_rate=0.01)

        if iteration % 10 == 0:
            logger.info(f"Iteration {iteration}: {metrics}")

    return {
        'final_params': param_server.get_params(),
        'iterations': iterations,
        'num_workers': num_workers
    }


if __name__ == "__main__":
    # Test distributed components

    # Test scheduler
    scheduler = QuantumTaskScheduler()

    worker1 = WorkerNode("worker1", "localhost", 8001, 20)
    worker2 = WorkerNode("worker2", "localhost", 8002, 20)

    scheduler.register_worker(worker1)
    scheduler.register_worker(worker2)

    # Test task submission
    task = QuantumTask(
        task_id="test_task",
        circuit="test_circuit",
        parameters={},
        shots=1024
    )

    task_id = scheduler.submit_task(task)
    print(f"Submitted task: {task_id}")
    print(f"Scheduler stats: {scheduler.get_statistics()}")

    # Test executor
    executor = DistributedQuantumExecutor(max_workers=2)

    circuits = [f"circuit_{i}" for i in range(4)]
    results = executor.execute_batch(circuits, shots=100)

    print(f"Executed {len(results)} circuits")

    # Test result aggregation
    counts_list = [
        {'00': 256, '11': 256},
        {'00': 300, '11': 212},
        {'00': 280, '11': 232}
    ]

    aggregated = ResultAggregator.aggregate_counts(counts_list)
    print(f"Aggregated counts: {aggregated}")
