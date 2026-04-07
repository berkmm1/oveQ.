"""
Quantum Benchmark Suite
======================

Comprehensive benchmarking for quantum algorithms and components.
Measures performance, accuracy, and resource usage.
"""

import time
import numpy as np
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
import logging
from contextlib import contextmanager
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a benchmark run."""
    name: str
    duration_ms: float
    iterations: int
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
    memory_mb: float
    success_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBenchmark:
    """Benchmark for quantum circuits."""
    circuit_name: str
    num_qubits: int
    num_gates: int
    depth: int
    compilation_time_ms: float
    simulation_time_ms: float
    memory_usage_mb: float
    fidelity: float


class PerformanceMonitor:
    """Monitor performance metrics during execution."""

    def __init__(self):
        """Initialize performance monitor."""
        self.process = psutil.Process(os.getpid())
        self.measurements: List[Dict] = []

    @contextmanager
    def measure(self, operation: str):
        """Context manager for measuring operation performance."""
        start_time = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            measurement = {
                'operation': operation,
                'duration_ms': (end_time - start_time) * 1000,
                'memory_delta_mb': end_memory - start_memory,
                'timestamp': time.time()
            }
            self.measurements.append(measurement)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all measurements."""
        if not self.measurements:
            return {}

        durations = [m['duration_ms'] for m in self.measurements]
        memory_deltas = [m['memory_delta_mb'] for m in self.measurements]

        return {
            'total_operations': len(self.measurements),
            'total_duration_ms': sum(durations),
            'mean_duration_ms': np.mean(durations),
            'max_duration_ms': max(durations),
            'total_memory_delta_mb': sum(memory_deltas),
            'operations_by_type': self._group_by_operation()
        }

    def _group_by_operation(self) -> Dict[str, Dict]:
        """Group measurements by operation type."""
        groups = defaultdict(list)
        for m in self.measurements:
            groups[m['operation']].append(m['duration_ms'])

        return {
            op: {
                'count': len(times),
                'mean_ms': np.mean(times),
                'total_ms': sum(times)
            }
            for op, times in groups.items()
        }

    def reset(self):
        """Reset all measurements."""
        self.measurements.clear()


class QuantumBenchmarkSuite:
    """
    Comprehensive benchmark suite for quantum computing components.
    """

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: List[BenchmarkResult] = []
        self.circuit_benchmarks: List[CircuitBenchmark] = []
        self.monitor = PerformanceMonitor()

    def benchmark_function(self, func: Callable, *args,
                          name: str = None,
                          iterations: int = 100,
                          warmup: int = 10,
                          **kwargs) -> BenchmarkResult:
        """
        Benchmark a function.

        Args:
            func: Function to benchmark
            args: Function arguments
            name: Benchmark name
            iterations: Number of iterations
            warmup: Number of warmup iterations
            kwargs: Function keyword arguments

        Returns:
            Benchmark result
        """
        name = name or func.__name__

        # Warmup
        for _ in range(warmup):
            try:
                func(*args, **kwargs)
            except Exception:
                pass

        # Measure memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        # Benchmark
        times = []
        successes = 0

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
                successes += 1
            except Exception as e:
                logger.debug(f"Benchmark iteration failed: {e}")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Measure memory after
        mem_after = process.memory_info().rss / 1024 / 1024

        result = BenchmarkResult(
            name=name,
            duration_ms=sum(times),
            iterations=iterations,
            mean_ms=np.mean(times),
            std_ms=np.std(times),
            min_ms=min(times),
            max_ms=max(times),
            memory_mb=mem_after - mem_before,
            success_rate=successes / iterations
        )

        self.results.append(result)
        return result

    def benchmark_circuit(self, circuit: Any,
                         circuit_name: str,
                         shots: int = 1024) -> CircuitBenchmark:
        """
        Benchmark a quantum circuit.

        Args:
            circuit: Circuit to benchmark
            circuit_name: Name of circuit
            shots: Number of shots

        Returns:
            Circuit benchmark result
        """
        # Get circuit metrics
        num_qubits = getattr(circuit, 'num_qubits', 0)
        num_gates = getattr(circuit, 'num_gates', 0)
        depth = getattr(circuit, 'depth', 0)

        # Benchmark compilation
        with self.monitor.measure('compilation'):
            compiled = self._compile_circuit(circuit)

        compilation_time = self.monitor.measurements[-1]['duration_ms'] if self.monitor.measurements else 0

        # Benchmark simulation
        with self.monitor.measure('simulation'):
            result = self._simulate_circuit(compiled, shots)

        simulation_time = self.monitor.measurements[-1]['duration_ms'] if self.monitor.measurements else 0

        # Memory usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Estimate fidelity
        fidelity = self._estimate_fidelity(circuit)

        benchmark = CircuitBenchmark(
            circuit_name=circuit_name,
            num_qubits=num_qubits,
            num_gates=num_gates,
            depth=depth,
            compilation_time_ms=compilation_time,
            simulation_time_ms=simulation_time,
            memory_usage_mb=memory_mb,
            fidelity=fidelity
        )

        self.circuit_benchmarks.append(benchmark)
        return benchmark

    def _compile_circuit(self, circuit: Any) -> Any:
        """Compile circuit."""
        # Mock compilation
        return circuit

    def _simulate_circuit(self, circuit: Any, shots: int) -> Dict:
        """Simulate circuit."""
        # Mock simulation
        return {'counts': {'0': shots}}

    def _estimate_fidelity(self, circuit: Any) -> float:
        """Estimate circuit fidelity."""
        # Mock fidelity estimation
        return 0.95

    def benchmark_algorithm(self, algorithm: str,
                           problem_size: int,
                           iterations: int = 10) -> BenchmarkResult:
        """
        Benchmark a quantum algorithm.

        Args:
            algorithm: Algorithm name
            problem_size: Problem size
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        def run_algorithm():
            if algorithm == 'grover':
                self._run_grover(problem_size)
            elif algorithm == 'shor':
                self._run_shor(problem_size)
            elif algorithm == 'vqe':
                self._run_vqe(problem_size)
            elif algorithm == 'qaoa':
                self._run_qaoa(problem_size)

        return self.benchmark_function(
            run_algorithm,
            name=f"{algorithm}_{problem_size}",
            iterations=iterations
        )

    def _run_grover(self, n: int):
        """Run Grover's algorithm."""
        # Mock execution
        time.sleep(0.001 * n)

    def _run_shor(self, n: int):
        """Run Shor's algorithm."""
        time.sleep(0.002 * n)

    def _run_vqe(self, n: int):
        """Run VQE."""
        time.sleep(0.001 * n)

    def _run_qaoa(self, n: int):
        """Run QAOA."""
        time.sleep(0.001 * n)

    def benchmark_scaling(self, func: Callable,
                         sizes: List[int],
                         **kwargs) -> Dict[int, BenchmarkResult]:
        """
        Benchmark function scaling with problem size.

        Args:
            func: Function to benchmark
            sizes: List of problem sizes
            kwargs: Additional arguments for benchmark_function

        Returns:
            Dictionary mapping size to benchmark result
        """
        results = {}
        for size in sizes:
            result = self.benchmark_function(
                func, size,
                name=f"{func.__name__}_{size}",
                **kwargs
            )
            results[size] = result

        return results

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        return {
            'summary': {
                'total_benchmarks': len(self.results),
                'total_circuit_benchmarks': len(self.circuit_benchmarks),
                'total_duration_ms': sum(r.duration_ms for r in self.results),
                'total_memory_mb': sum(r.memory_mb for r in self.results)
            },
            'function_benchmarks': [
                {
                    'name': r.name,
                    'mean_ms': r.mean_ms,
                    'std_ms': r.std_ms,
                    'min_ms': r.min_ms,
                    'max_ms': r.max_ms,
                    'memory_mb': r.memory_mb,
                    'success_rate': r.success_rate
                }
                for r in self.results
            ],
            'circuit_benchmarks': [
                {
                    'name': b.circuit_name,
                    'num_qubits': b.num_qubits,
                    'num_gates': b.num_gates,
                    'depth': b.depth,
                    'compilation_time_ms': b.compilation_time_ms,
                    'simulation_time_ms': b.simulation_time_ms,
                    'memory_mb': b.memory_usage_mb,
                    'fidelity': b.fidelity
                }
                for b in self.circuit_benchmarks
            ],
            'performance_summary': self.monitor.get_summary()
        }

    def save_report(self, filepath: str):
        """Save benchmark report to file."""
        report = self.generate_report()

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Benchmark report saved to {filepath}")

    def compare_results(self, baseline: BenchmarkResult,
                       current: BenchmarkResult) -> Dict[str, Any]:
        """
        Compare two benchmark results.

        Args:
            baseline: Baseline result
            current: Current result

        Returns:
            Comparison dictionary
        """
        return {
            'name': current.name,
            'mean_change': (current.mean_ms - baseline.mean_ms) / baseline.mean_ms * 100,
            'memory_change': (current.memory_mb - baseline.memory_mb) / baseline.memory_mb * 100 if baseline.memory_mb > 0 else 0,
            'speedup': baseline.mean_ms / current.mean_ms if current.mean_ms > 0 else 1,
            'baseline_mean_ms': baseline.mean_ms,
            'current_mean_ms': current.mean_ms
        }

    def reset(self):
        """Reset all benchmark results."""
        self.results.clear()
        self.circuit_benchmarks.clear()
        self.monitor.reset()


class RegressionDetector:
    """Detect performance regressions."""

    def __init__(self, threshold_percent: float = 10.0):
        """
        Initialize regression detector.

        Args:
            threshold_percent: Threshold for regression detection (%)
        """
        self.threshold_percent = threshold_percent
        self.baseline_results: Dict[str, BenchmarkResult] = {}

    def set_baseline(self, results: List[BenchmarkResult]):
        """Set baseline results."""
        self.baseline_results = {r.name: r for r in results}

    def check_regression(self, current: BenchmarkResult) -> Optional[Dict]:
        """
        Check for regression in current result.

        Args:
            current: Current benchmark result

        Returns:
            Regression info if detected, None otherwise
        """
        if current.name not in self.baseline_results:
            return None

        baseline = self.baseline_results[current.name]

        # Check for performance regression
        if current.mean_ms > baseline.mean_ms * (1 + self.threshold_percent / 100):
            return {
                'type': 'performance_regression',
                'benchmark': current.name,
                'baseline_ms': baseline.mean_ms,
                'current_ms': current.mean_ms,
                'increase_percent': (current.mean_ms - baseline.mean_ms) / baseline.mean_ms * 100
            }

        # Check for memory regression
        if current.memory_mb > baseline.memory_mb * (1 + self.threshold_percent / 100):
            return {
                'type': 'memory_regression',
                'benchmark': current.name,
                'baseline_mb': baseline.memory_mb,
                'current_mb': current.memory_mb,
                'increase_percent': (current.memory_mb - baseline.memory_mb) / baseline.memory_mb * 100
            }

        return None

    def check_all(self, current_results: List[BenchmarkResult]) -> List[Dict]:
        """Check all results for regressions."""
        regressions = []
        for result in current_results:
            regression = self.check_regression(result)
            if regression:
                regressions.append(regression)
        return regressions


# Benchmark functions for common operations
def benchmark_gates(num_qubits: int = 10, num_gates: int = 100):
    """Benchmark gate operations."""
    suite = QuantumBenchmarkSuite()

    def apply_gates():
        # Mock gate application
        for _ in range(num_gates):
            pass

    return suite.benchmark_function(
        apply_gates,
        name=f"gates_{num_qubits}q_{num_gates}g",
        iterations=100
    )


def benchmark_circuit_depth(depth: int = 100):
    """Benchmark circuit with given depth."""
    suite = QuantumBenchmarkSuite()

    def create_deep_circuit():
        # Mock circuit creation
        gates = []
        for _ in range(depth):
            gates.append('H')
        return gates

    return suite.benchmark_function(
        create_deep_circuit,
        name=f"depth_{depth}",
        iterations=50
    )


def benchmark_parameterized_circuit(num_parameters: int = 10):
    """Benchmark parameterized circuit."""
    suite = QuantumBenchmarkSuite()

    params = np.random.randn(num_parameters)

    def evaluate_circuit():
        # Mock evaluation
        return np.sum(params ** 2)

    return suite.benchmark_function(
        evaluate_circuit,
        name=f"parameterized_{num_parameters}",
        iterations=100
    )


if __name__ == "__main__":
    # Run benchmarks
    suite = QuantumBenchmarkSuite()

    # Benchmark algorithms
    for algorithm in ['grover', 'vqe', 'qaoa']:
        for size in [4, 6, 8]:
            result = suite.benchmark_algorithm(algorithm, size, iterations=5)
            print(f"{algorithm} (n={size}): {result.mean_ms:.2f} ms")

    # Generate report
    report = suite.generate_report()
    print("\nBenchmark Summary:")
    print(json.dumps(report['summary'], indent=2))
