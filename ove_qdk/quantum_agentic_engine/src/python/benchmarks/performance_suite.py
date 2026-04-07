#!/usr/bin/env python3
"""
Performance Benchmarking Suite
Comprehensive performance testing for quantum components
Part of the Quantum Agentic Loop Engine
"""

import time
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import json
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of benchmarks"""
    LATENCY = auto()
    THROUGHPUT = auto()
    ACCURACY = auto()
    SCALABILITY = auto()
    MEMORY = auto()
    ENERGY = auto()


@dataclass
class BenchmarkResult:
    """Result of a benchmark"""
    name: str
    benchmark_type: BenchmarkType
    value: float
    unit: str
    iterations: int
    total_time: float
    mean: float
    std: float
    min: float
    max: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.benchmark_type.name,
            'value': self.value,
            'unit': self.unit,
            'iterations': self.iterations,
            'total_time': self.total_time,
            'mean': self.mean,
            'std': self.std,
            'min': self.min,
            'max': self.max,
            'metadata': self.metadata
        }


class PerformanceBenchmark:
    """Base class for performance benchmarks"""

    def __init__(self, name: str, benchmark_type: BenchmarkType):
        self.name = name
        self.benchmark_type = benchmark_type
        self.results: List[float] = []

    def run(self, func: Callable, *args, iterations: int = 100, **kwargs) -> BenchmarkResult:
        """Run benchmark"""
        self.results = []

        # Warmup
        for _ in range(min(10, iterations // 10)):
            func(*args, **kwargs)

        # Actual benchmark
        start_time = time.time()

        for _ in range(iterations):
            iter_start = time.perf_counter()
            func(*args, **kwargs)
            iter_end = time.perf_counter()
            self.results.append(iter_end - iter_start)

        total_time = time.time() - start_time

        return self._create_result(iterations, total_time)

    def _create_result(self, iterations: int, total_time: float) -> BenchmarkResult:
        """Create benchmark result"""
        results_array = np.array(self.results)

        return BenchmarkResult(
            name=self.name,
            benchmark_type=self.benchmark_type,
            value=np.mean(results_array),
            unit='seconds',
            iterations=iterations,
            total_time=total_time,
            mean=np.mean(results_array),
            std=np.std(results_array),
            min=np.min(results_array),
            max=np.max(results_array)
        )


class LatencyBenchmark(PerformanceBenchmark):
    """Measure operation latency"""

    def __init__(self, name: str):
        super().__init__(name, BenchmarkType.LATENCY)

    def run(self, func: Callable, *args, iterations: int = 1000, **kwargs) -> BenchmarkResult:
        """Measure latency in milliseconds"""
        result = super().run(func, *args, iterations=iterations, **kwargs)

        # Convert to milliseconds
        result.value *= 1000
        result.mean *= 1000
        result.std *= 1000
        result.min *= 1000
        result.max *= 1000
        result.unit = 'milliseconds'

        return result


class ThroughputBenchmark(PerformanceBenchmark):
    """Measure operation throughput"""

    def __init__(self, name: str):
        super().__init__(name, BenchmarkType.THROUGHPUT)

    def run(self, func: Callable, *args, duration: float = 10.0, **kwargs) -> BenchmarkResult:
        """Measure throughput (operations per second)"""
        iterations = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            func(*args, **kwargs)
            iterations += 1

        total_time = time.time() - start_time
        throughput = iterations / total_time

        return BenchmarkResult(
            name=self.name,
            benchmark_type=self.benchmark_type,
            value=throughput,
            unit='ops/sec',
            iterations=iterations,
            total_time=total_time,
            mean=throughput,
            std=0.0,
            min=throughput,
            max=throughput
        )


class AccuracyBenchmark(PerformanceBenchmark):
    """Measure computational accuracy"""

    def __init__(self, name: str):
        super().__init__(name, BenchmarkType.ACCURACY)

    def run(self, func: Callable, expected: Any, *args,
            iterations: int = 100, tolerance: float = 1e-6, **kwargs) -> BenchmarkResult:
        """Measure accuracy against expected result"""
        errors = []

        for _ in range(iterations):
            result = func(*args, **kwargs)

            if isinstance(expected, np.ndarray):
                error = np.mean(np.abs(result - expected))
            else:
                error = abs(result - expected)

            errors.append(error)

        errors_array = np.array(errors)

        return BenchmarkResult(
            name=self.name,
            benchmark_type=self.benchmark_type,
            value=np.mean(errors_array <= tolerance),
            unit='accuracy_ratio',
            iterations=iterations,
            total_time=0.0,
            mean=np.mean(errors_array),
            std=np.std(errors_array),
            min=np.min(errors_array),
            max=np.max(errors_array),
            metadata={'tolerance': tolerance}
        )


class ScalabilityBenchmark(PerformanceBenchmark):
    """Measure scalability with problem size"""

    def __init__(self, name: str):
        super().__init__(name, BenchmarkType.SCALABILITY)

    def run(self, func: Callable, sizes: List[int], *args,
            iterations: int = 10, **kwargs) -> List[BenchmarkResult]:
        """Measure performance across different problem sizes"""
        results = []

        for size in sizes:
            self.results = []

            for _ in range(iterations):
                start = time.perf_counter()
                func(size, *args, **kwargs)
                end = time.perf_counter()
                self.results.append(end - start)

            results_array = np.array(self.results)

            result = BenchmarkResult(
                name=f"{self.name}_size_{size}",
                benchmark_type=self.benchmark_type,
                value=np.mean(results_array),
                unit='seconds',
                iterations=iterations,
                total_time=np.sum(results_array),
                mean=np.mean(results_array),
                std=np.std(results_array),
                min=np.min(results_array),
                max=np.max(results_array),
                metadata={'problem_size': size}
            )
            results.append(result)

        return results


class MemoryBenchmark(PerformanceBenchmark):
    """Measure memory usage"""

    def __init__(self, name: str):
        super().__init__(name, BenchmarkType.MEMORY)

    def run(self, func: Callable, *args, iterations: int = 10, **kwargs) -> BenchmarkResult:
        """Measure peak memory usage"""
        import tracemalloc

        peak_memories = []

        for _ in range(iterations):
            tracemalloc.start()

            func(*args, **kwargs)

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            peak_memories.append(peak / (1024 * 1024))  # Convert to MB

        memories_array = np.array(peak_memories)

        return BenchmarkResult(
            name=self.name,
            benchmark_type=self.benchmark_type,
            value=np.mean(memories_array),
            unit='MB',
            iterations=iterations,
            total_time=0.0,
            mean=np.mean(memories_array),
            std=np.std(memories_array),
            min=np.min(memories_array),
            max=np.max(memories_array)
        )


class QuantumBenchmarkSuite:
    """Comprehensive benchmark suite for quantum components"""

    def __init__(self):
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        self.results: Dict[str, Any] = {}

    def add_benchmark(self, name: str, benchmark: PerformanceBenchmark):
        """Add a benchmark to the suite"""
        self.benchmarks[name] = benchmark

    def run_all(self) -> Dict[str, Any]:
        """Run all benchmarks"""
        logger.info("Running benchmark suite...")

        for name, benchmark in self.benchmarks.items():
            logger.info(f"Running benchmark: {name}")
            # Note: Actual benchmark functions would be passed here

        return self.results

    def run_benchmark(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """Run a specific benchmark"""
        if name not in self.benchmarks:
            raise ValueError(f"Benchmark {name} not found")

        benchmark = self.benchmarks[name]
        result = benchmark.run(func, *args, **kwargs)

        self.results[name] = result

        logger.info(f"Benchmark {name} completed: {result.value:.4f} {result.unit}")

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all results"""
        summary = {
            'total_benchmarks': len(self.results),
            'benchmarks': {}
        }

        for name, result in self.results.items():
            if isinstance(result, BenchmarkResult):
                summary['benchmarks'][name] = result.to_dict()
            elif isinstance(result, list):
                summary['benchmarks'][name] = [r.to_dict() for r in result]

        return summary

    def save_results(self, filepath: str):
        """Save results to file"""
        summary = self.get_summary()

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Results saved to {filepath}")

    def compare_with_baseline(self, baseline_file: str) -> Dict[str, Any]:
        """Compare current results with baseline"""
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)

        comparison = {}

        for name, result in self.results.items():
            if name in baseline['benchmarks']:
                baseline_result = baseline['benchmarks'][name]

                if isinstance(result, BenchmarkResult):
                    change = (result.value - baseline_result['value']) / baseline_result['value'] * 100
                    comparison[name] = {
                        'current': result.value,
                        'baseline': baseline_result['value'],
                        'change_percent': change,
                        'improved': change < 0 if result.benchmark_type == BenchmarkType.LATENCY else change > 0
                    }

        return comparison


# Specific quantum benchmarks
class QuantumCircuitBenchmark:
    """Benchmark quantum circuit operations"""

    def __init__(self, num_qubits: int = 8):
        self.num_qubits = num_qubits

    def benchmark_state_preparation(self) -> BenchmarkResult:
        """Benchmark state preparation"""
        def prepare_state():
            # Simulate state preparation
            state = np.random.randn(2 ** self.num_qubits)
            state = state / np.linalg.norm(state)
            return state

        benchmark = LatencyBenchmark("state_preparation")
        return benchmark.run(prepare_state, iterations=1000)

    def benchmark_gate_application(self) -> BenchmarkResult:
        """Benchmark single gate application"""
        state = np.random.randn(2 ** self.num_qubits)
        state = state / np.linalg.norm(state)

        def apply_gate():
            # Simulate gate application
            gate = np.random.randn(2, 2)
            gate = gate / np.linalg.norm(gate)

            # Apply to first qubit
            new_state = state.copy()
            for i in range(0, len(state), 2):
                if i + 1 < len(state):
                    vec = np.array([state[i], state[i+1]])
                    result = gate @ vec
                    new_state[i] = result[0]
                    new_state[i+1] = result[1]

            return new_state

        benchmark = LatencyBenchmark("gate_application")
        return benchmark.run(apply_gate, iterations=10000)

    def benchmark_measurement(self) -> BenchmarkResult:
        """Benchmark measurement operation"""
        state = np.random.randn(2 ** self.num_qubits)
        state = state / np.linalg.norm(state)

        def measure():
            # Simulate measurement
            probabilities = np.abs(state) ** 2
            outcome = np.random.choice(len(state), p=probabilities)
            return outcome

        benchmark = LatencyBenchmark("measurement")
        return benchmark.run(measure, iterations=10000)

    def benchmark_entanglement_generation(self) -> BenchmarkResult:
        """Benchmark entanglement generation"""
        def generate_entanglement():
            # Create Bell state
            state = np.zeros(2 ** self.num_qubits)
            state[0] = 1/np.sqrt(2)
            state[-1] = 1/np.sqrt(2)
            return state

        benchmark = LatencyBenchmark("entanglement_generation")
        return benchmark.run(generate_entanglement, iterations=1000)

    def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all circuit benchmarks"""
        results = {}

        results['state_preparation'] = self.benchmark_state_preparation()
        results['gate_application'] = self.benchmark_gate_application()
        results['measurement'] = self.benchmark_measurement()
        results['entanglement_generation'] = self.benchmark_entanglement_generation()

        return results


class QuantumAlgorithmBenchmark:
    """Benchmark quantum algorithms"""

    def __init__(self):
        pass

    def benchmark_grover_search(self, num_qubits: int = 8) -> BenchmarkResult:
        """Benchmark Grover's search algorithm"""
        def grover_search():
            # Simulate Grover's algorithm
            n = 2 ** num_qubits
            state = np.ones(n) / np.sqrt(n)

            # Oracle
            target = np.random.randint(n)

            # Grover iterations
            num_iterations = int(np.pi / 4 * np.sqrt(n))

            for _ in range(max(1, num_iterations)):
                # Oracle application
                state[target] *= -1

                # Diffusion
                mean = np.mean(state)
                state = 2 * mean - state

            return state

        benchmark = LatencyBenchmark(f"grover_search_{num_qubits}q")
        return benchmark.run(grover_search, iterations=100)

    def benchmark_qft(self, num_qubits: int = 8) -> BenchmarkResult:
        """Benchmark Quantum Fourier Transform"""
        def qft():
            # Simulate QFT
            n = 2 ** num_qubits
            state = np.random.randn(n) + 1j * np.random.randn(n)
            state = state / np.linalg.norm(state)

            # Apply QFT (simplified)
            output = np.fft.fft(state) / np.sqrt(n)

            return output

        benchmark = LatencyBenchmark(f"qft_{num_qubits}q")
        return benchmark.run(qft, iterations=1000)

    def benchmark_vqe(self, num_qubits: int = 4) -> BenchmarkResult:
        """Benchmark Variational Quantum Eigensolver"""
        def vqe_step():
            # Simulate one VQE iteration
            params = np.random.randn(num_qubits * 3)

            # Prepare ansatz
            state = np.ones(2 ** num_qubits) / np.sqrt(2 ** num_qubits)

            # Measure energy (simplified)
            energy = np.random.randn()

            # Update parameters
            params -= 0.01 * np.random.randn(len(params))

            return energy

        benchmark = LatencyBenchmark(f"vqe_{num_qubits}q")
        return benchmark.run(vqe_step, iterations=1000)

    def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all algorithm benchmarks"""
        results = {}

        for num_qubits in [4, 6, 8]:
            results[f'grover_{num_qubits}q'] = self.benchmark_grover_search(num_qubits)
            results[f'qft_{num_qubits}q'] = self.benchmark_qft(num_qubits)

        for num_qubits in [2, 4]:
            results[f'vqe_{num_qubits}q'] = self.benchmark_vqe(num_qubits)

        return results


class QuantumMLBenchmark:
    """Benchmark quantum machine learning operations"""

    def __init__(self):
        pass

    def benchmark_feature_map(self, feature_dim: int = 8, num_qubits: int = 8) -> BenchmarkResult:
        """Benchmark quantum feature mapping"""
        def feature_map():
            features = np.random.randn(feature_dim)

            # Angle encoding
            angles = np.arctan(features) * np.pi

            # Pad to qubit count
            if len(angles) < num_qubits:
                angles = np.pad(angles, (0, num_qubits - len(angles)))
            else:
                angles = angles[:num_qubits]

            return angles

        benchmark = LatencyBenchmark("feature_map")
        return benchmark.run(feature_map, iterations=10000)

    def benchmark_kernel_evaluation(self, dim: int = 8) -> BenchmarkResult:
        """Benchmark quantum kernel evaluation"""
        x1 = np.random.randn(dim)
        x2 = np.random.randn(dim)

        def kernel():
            # ZZ kernel
            diff = x1 - x2
            similarity = np.exp(-np.sum(diff ** 2) / (2 * len(diff)))
            return similarity

        benchmark = LatencyBenchmark("kernel_evaluation")
        return benchmark.run(kernel, iterations=10000)

    def benchmark_gradient_computation(self, num_params: int = 32) -> BenchmarkResult:
        """Benchmark gradient computation"""
        params = np.random.randn(num_params)

        def compute_gradients():
            # Parameter shift rule
            gradients = np.zeros(num_params)

            for i in range(num_params):
                shift = np.pi / 2

                # Forward evaluation
                params_plus = params.copy()
                params_plus[i] += shift

                # Backward evaluation
                params_minus = params.copy()
                params_minus[i] -= shift

                # Gradient
                gradients[i] = (np.sin(params_plus[i]) - np.sin(params_minus[i])) / (2 * np.sin(shift))

            return gradients

        benchmark = LatencyBenchmark("gradient_computation")
        return benchmark.run(compute_gradients, iterations=1000)

    def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all ML benchmarks"""
        results = {}

        results['feature_map'] = self.benchmark_feature_map()
        results['kernel_evaluation'] = self.benchmark_kernel_evaluation()
        results['gradient_computation'] = self.benchmark_gradient_computation()

        return results


# Main benchmark runner
def run_full_benchmark_suite(output_file: str = "benchmark_results.json"):
    """Run complete benchmark suite"""
    logger.info("Starting full benchmark suite...")

    all_results = {}

    # Circuit benchmarks
    logger.info("Running circuit benchmarks...")
    circuit_benchmark = QuantumCircuitBenchmark(num_qubits=8)
    all_results['circuits'] = {
        k: v.to_dict() for k, v in circuit_benchmark.run_all().items()
    }

    # Algorithm benchmarks
    logger.info("Running algorithm benchmarks...")
    algorithm_benchmark = QuantumAlgorithmBenchmark()
    all_results['algorithms'] = {
        k: v.to_dict() for k, v in algorithm_benchmark.run_all().items()
    }

    # ML benchmarks
    logger.info("Running ML benchmarks...")
    ml_benchmark = QuantumMLBenchmark()
    all_results['ml'] = {
        k: v.to_dict() for k, v in ml_benchmark.run_all().items()
    }

    # Save results
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Benchmark results saved to {output_file}")

    return all_results


if __name__ == "__main__":
    print("Performance Benchmark Suite")
    print("=" * 40)

    # Run benchmarks
    results = run_full_benchmark_suite()

    # Print summary
    print("\nBenchmark Summary:")
    print("-" * 40)

    for category, benchmarks in results.items():
        print(f"\n{category.upper()}:")
        for name, result in benchmarks.items():
            print(f"  {name}: {result['mean']:.4f} {result['unit']}")
