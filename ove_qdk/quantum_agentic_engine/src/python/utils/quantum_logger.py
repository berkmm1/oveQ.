"""
Quantum Logger Module
====================

Comprehensive logging system for quantum operations with:
- Structured logging for quantum circuits
- Performance metrics tracking
- Execution history
- Debug and profiling capabilities
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict
from enum import Enum, auto
import threading
from contextlib import contextmanager
import traceback
import os


class LogLevel(Enum):
    """Custom log levels for quantum operations."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    QUANTUM = 15  # Between DEBUG and INFO
    CIRCUIT = 16
    METRIC = 17


class OperationType(Enum):
    """Types of quantum operations."""
    GATE = auto()
    MEASUREMENT = auto()
    CIRCUIT = auto()
    OPTIMIZATION = auto()
    SIMULATION = auto()
    COMPILATION = auto()
    EXECUTION = auto()
    ERROR_CORRECTION = auto()
    COMMUNICATION = auto()


@dataclass
class QuantumLogEntry:
    """Structured log entry for quantum operations."""
    timestamp: str
    level: str
    operation_type: str
    message: str
    circuit_id: Optional[str] = None
    qubits: Optional[List[int]] = None
    gate_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class CircuitMetrics:
    """Metrics for a quantum circuit."""
    circuit_id: str
    num_qubits: int = 0
    num_gates: int = 0
    depth: int = 0
    gate_counts: Dict[str, int] = field(default_factory=dict)
    two_qubit_count: int = 0
    parameter_count: int = 0
    creation_time: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_count: int = 0
    total_execution_time_ms: float = 0.0
    average_fidelity: float = 0.0


@dataclass
class ExecutionProfile:
    """Profile of quantum execution."""
    execution_id: str
    circuit_id: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    shots: int = 0
    backend: str = ""
    success: bool = True
    results_summary: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class QuantumLogger:
    """
    Comprehensive logger for quantum operations.

    Provides structured logging, metrics tracking, and profiling
    capabilities for quantum computing workflows.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern for global logger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = "quantum_agent",
                 log_level: int = logging.INFO,
                 log_file: Optional[str] = None):
        """
        Initialize quantum logger.

        Args:
            name: Logger name
            log_level: Logging level
            log_file: Optional file path for logging
        """
        if self._initialized:
            return

        self.name = name
        self.log_level = log_level
        self.log_file = log_file

        # Setup Python logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(log_level)

        # Clear existing handlers
        self._logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        # Add custom log levels
        logging.addLevelName(LogLevel.QUANTUM.value, "QUANTUM")
        logging.addLevelName(LogLevel.CIRCUIT.value, "CIRCUIT")
        logging.addLevelName(LogLevel.METRIC.value, "METRIC")

        # Metrics storage
        self._circuit_metrics: Dict[str, CircuitMetrics] = {}
        self._execution_profiles: List[ExecutionProfile] = []
        self._operation_counts: Dict[OperationType, int] = defaultdict(int)
        self._gate_counts: Dict[str, int] = defaultdict(int)

        # Performance tracking
        self._active_timers: Dict[str, float] = {}
        self._performance_history: List[Dict] = []

        # Error tracking
        self._error_count = 0
        self._error_history: List[Dict] = []

        self._initialized = True

        self._logger.info(f"QuantumLogger initialized: {name}")

    def log_quantum(self, message: str, operation_type: OperationType,
                   circuit_id: Optional[str] = None,
                   qubits: Optional[List[int]] = None,
                   gate_type: Optional[str] = None,
                   parameters: Optional[Dict] = None,
                   extra: Optional[Dict] = None) -> None:
        """
        Log a quantum operation.

        Args:
            message: Log message
            operation_type: Type of operation
            circuit_id: Optional circuit identifier
            qubits: Optional list of qubit indices
            gate_type: Optional gate type
            parameters: Optional parameters
            extra: Optional extra metadata
        """
        entry = QuantumLogEntry(
            timestamp=datetime.now().isoformat(),
            level="QUANTUM",
            operation_type=operation_type.name,
            message=message,
            circuit_id=circuit_id,
            qubits=qubits,
            gate_type=gate_type,
            parameters=parameters,
            metadata=extra or {}
        )

        self._logger.log(LogLevel.QUANTUM.value, entry.to_json())
        self._operation_counts[operation_type] += 1

        if gate_type:
            self._gate_counts[gate_type] += 1

    def log_circuit(self, circuit_id: str, num_qubits: int,
                   num_gates: int, depth: int,
                   gate_counts: Optional[Dict[str, int]] = None,
                   metadata: Optional[Dict] = None) -> None:
        """
        Log circuit creation.

        Args:
            circuit_id: Circuit identifier
            num_qubits: Number of qubits
            num_gates: Number of gates
            depth: Circuit depth
            gate_counts: Gate type counts
            metadata: Additional metadata
        """
        metrics = CircuitMetrics(
            circuit_id=circuit_id,
            num_qubits=num_qubits,
            num_gates=num_gates,
            depth=depth,
            gate_counts=gate_counts or {},
            two_qubit_count=sum(1 for g, c in (gate_counts or {}).items()
                              if g in ['CNOT', 'CZ', 'SWAP']) *
                          sum((gate_counts or {}).values()),
            parameter_count=metadata.get('parameter_count', 0) if metadata else 0
        )

        self._circuit_metrics[circuit_id] = metrics

        entry = QuantumLogEntry(
            timestamp=datetime.now().isoformat(),
            level="CIRCUIT",
            operation_type=OperationType.CIRCUIT.name,
            message=f"Circuit {circuit_id} created",
            circuit_id=circuit_id,
            metadata={
                'metrics': metrics.to_dict(),
                'extra': metadata or {}
            }
        )

        self._logger.log(LogLevel.CIRCUIT.value, entry.to_json())

    def log_execution(self, execution_id: str, circuit_id: str,
                     shots: int, backend: str,
                     results: Optional[Dict] = None,
                     success: bool = True,
                     error: Optional[str] = None) -> None:
        """
        Log circuit execution.

        Args:
            execution_id: Execution identifier
            circuit_id: Circuit identifier
            shots: Number of shots
            backend: Backend used
            results: Execution results
            success: Whether execution succeeded
            error: Error message if failed
        """
        profile = ExecutionProfile(
            execution_id=execution_id,
            circuit_id=circuit_id,
            start_time=datetime.now().isoformat(),
            shots=shots,
            backend=backend,
            success=success,
            results_summary=results or {},
            error_message=error
        )

        self._execution_profiles.append(profile)

        # Update circuit metrics
        if circuit_id in self._circuit_metrics:
            self._circuit_metrics[circuit_id].execution_count += 1

        entry = QuantumLogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO" if success else "ERROR",
            operation_type=OperationType.EXECUTION.name,
            message=f"Execution {execution_id} {'succeeded' if success else 'failed'}",
            circuit_id=circuit_id,
            metadata={
                'execution_id': execution_id,
                'shots': shots,
                'backend': backend,
                'results': results
            },
            success=success,
            error=error
        )

        self._logger.info(entry.to_json())

        if not success:
            self._error_count += 1
            self._error_history.append({
                'timestamp': datetime.now().isoformat(),
                'execution_id': execution_id,
                'circuit_id': circuit_id,
                'error': error
            })

    def log_metric(self, metric_name: str, value: float,
                  circuit_id: Optional[str] = None,
                  labels: Optional[Dict[str, str]] = None) -> None:
        """
        Log a metric value.

        Args:
            metric_name: Name of the metric
            value: Metric value
            circuit_id: Optional circuit identifier
            labels: Optional labels for the metric
        """
        entry = QuantumLogEntry(
            timestamp=datetime.now().isoformat(),
            level="METRIC",
            operation_type=OperationType.METRIC.name,
            message=f"Metric: {metric_name} = {value}",
            circuit_id=circuit_id,
            metadata={
                'metric_name': metric_name,
                'value': value,
                'labels': labels or {}
            }
        )

        self._logger.log(LogLevel.METRIC.value, entry.to_json())

    @contextmanager
    def timer(self, operation_name: str, circuit_id: Optional[str] = None):
        """
        Context manager for timing operations.

        Args:
            operation_name: Name of the operation
            circuit_id: Optional circuit identifier

        Usage:
            with logger.timer("optimization", "circuit_1"):
                # operation to time
                pass
        """
        start_time = time.time()
        timer_id = f"{circuit_id}_{operation_name}" if circuit_id else operation_name
        self._active_timers[timer_id] = start_time

        try:
            yield
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            if timer_id in self._active_timers:
                del self._active_timers[timer_id]

            self._performance_history.append({
                'timestamp': datetime.now().isoformat(),
                'operation': operation_name,
                'circuit_id': circuit_id,
                'duration_ms': duration_ms
            })

            self.log_metric(f"timer_{operation_name}", duration_ms, circuit_id)

    def get_circuit_metrics(self, circuit_id: Optional[str] = None) -> Dict:
        """
        Get metrics for circuits.

        Args:
            circuit_id: Optional specific circuit ID

        Returns:
            Circuit metrics dictionary
        """
        if circuit_id:
            if circuit_id in self._circuit_metrics:
                return self._circuit_metrics[circuit_id].to_dict()
            return {}

        return {cid: m.to_dict() for cid, m in self._circuit_metrics.items()}

    def get_execution_summary(self) -> Dict:
        """Get summary of all executions."""
        total_executions = len(self._execution_profiles)
        successful = sum(1 for p in self._execution_profiles if p.success)
        failed = total_executions - successful

        backend_counts = defaultdict(int)
        for profile in self._execution_profiles:
            backend_counts[profile.backend] += 1

        return {
            'total_executions': total_executions,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_executions if total_executions > 0 else 0,
            'backend_distribution': dict(backend_counts),
            'total_shots': sum(p.shots for p in self._execution_profiles),
            'error_count': self._error_count
        }

    def get_operation_summary(self) -> Dict:
        """Get summary of operations."""
        return {
            'operation_counts': {op.name: count for op, count in self._operation_counts.items()},
            'gate_counts': dict(self._gate_counts),
            'total_gates': sum(self._gate_counts.values()),
            'total_operations': sum(self._operation_counts.values())
        }

    def get_performance_report(self) -> Dict:
        """Get performance report."""
        if not self._performance_history:
            return {'message': 'No performance data available'}

        durations = [p['duration_ms'] for p in self._performance_history]

        return {
            'total_timed_operations': len(durations),
            'total_time_ms': sum(durations),
            'average_time_ms': sum(durations) / len(durations),
            'min_time_ms': min(durations),
            'max_time_ms': max(durations),
            'operations_by_type': self._group_by_operation()
        }

    def _group_by_operation(self) -> Dict:
        """Group performance data by operation type."""
        groups = defaultdict(list)
        for entry in self._performance_history:
            groups[entry['operation']].append(entry['duration_ms'])

        return {
            op: {
                'count': len(times),
                'total_ms': sum(times),
                'average_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times)
            }
            for op, times in groups.items()
        }

    def export_logs(self, filepath: str, format: str = 'json') -> None:
        """
        Export logs to file.

        Args:
            filepath: Output file path
            format: Export format ('json' or 'csv')
        """
        data = {
            'circuit_metrics': self.get_circuit_metrics(),
            'execution_summary': self.get_execution_summary(),
            'operation_summary': self.get_operation_summary(),
            'performance_report': self.get_performance_report(),
            'error_history': self._error_history
        }

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            import csv
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                for key, value in data.items():
                    writer.writerow([key, json.dumps(value, default=str)])

        self._logger.info(f"Logs exported to {filepath}")

    def reset(self) -> None:
        """Reset all metrics and logs."""
        self._circuit_metrics.clear()
        self._execution_profiles.clear()
        self._operation_counts.clear()
        self._gate_counts.clear()
        self._performance_history.clear()
        self._error_count = 0
        self._error_history.clear()
        self._active_timers.clear()

        self._logger.info("QuantumLogger reset")

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message."""
        self._logger.error(message, exc_info=exc_info, **kwargs)
        self._error_count += 1
        self._error_history.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'traceback': traceback.format_exc() if exc_info else None
        })

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._logger.critical(message, **kwargs)


# Decorator for logging function calls
def log_operation(operation_type: OperationType,
                  circuit_id_arg: Optional[str] = None):
    """
    Decorator to log function execution.

    Args:
        operation_type: Type of operation
        circuit_id_arg: Name of argument containing circuit_id
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            logger = QuantumLogger()

            # Extract circuit_id if specified
            cid = None
            if circuit_id_arg:
                if circuit_id_arg in kwargs:
                    cid = kwargs[circuit_id_arg]
                elif len(args) > 0:
                    # Try to get from positional args
                    import inspect
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    if circuit_id_arg in params:
                        idx = params.index(circuit_id_arg)
                        if idx < len(args):
                            cid = args[idx]

            with logger.timer(func.__name__, cid):
                try:
                    result = func(*args, **kwargs)
                    logger.log_quantum(
                        f"{func.__name__} completed successfully",
                        operation_type,
                        circuit_id=cid
                    )
                    return result
                except Exception as e:
                    logger.error(f"{func.__name__} failed: {e}", exc_info=True)
                    raise

        return wrapper
    return decorator


# Global logger instance
def get_logger(name: str = "quantum_agent",
               log_level: int = logging.INFO,
               log_file: Optional[str] = None) -> QuantumLogger:
    """Get global quantum logger instance."""
    return QuantumLogger(name, log_level, log_file)


if __name__ == "__main__":
    # Test logger
    logger = get_logger("test", log_level=logging.DEBUG)

    # Log some operations
    logger.log_quantum("Applying Hadamard gate", OperationType.GATE,
                      circuit_id="test_circuit", qubits=[0], gate_type="H")

    logger.log_circuit("test_circuit", 5, 10, 5,
                      gate_counts={'H': 3, 'CNOT': 4, 'Rx': 3})

    with logger.timer("test_operation", "test_circuit"):
        time.sleep(0.1)

    logger.log_execution("exec_1", "test_circuit", 1024, "simulator",
                        results={'counts': {'00000': 512, '11111': 512}})

    # Print summaries
    print("Circuit Metrics:", logger.get_circuit_metrics())
    print("Execution Summary:", logger.get_execution_summary())
    print("Performance Report:", logger.get_performance_report())
