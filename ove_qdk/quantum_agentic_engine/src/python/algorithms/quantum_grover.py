#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Grover's Algorithm Implementation
Optimized Grover search with adaptive iterations and multiple oracles
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OracleType(Enum):
    """Types of quantum oracles"""
    SIMPLE = auto()
    PHASE = auto()
    BOOLEAN = auto()
    PATTERN = auto()
    MULTI_TARGET = auto()
    ADAPTIVE = auto()


@dataclass
class GroverConfig:
    """Configuration for Grover's algorithm"""
    num_qubits: int = 8
    num_solutions: int = 1
    max_iterations: int = 100
    use_fixed_iterations: bool = False
    target_probability: float = 0.99
    use_amplitude_amplification: bool = True
    use_partial_diffusion: bool = False
    enable_caching: bool = True
    parallel_oracles: bool = False

    def optimal_iterations(self) -> int:
        """Calculate optimal number of iterations"""
        n = self.num_qubits
        m = self.num_solutions
        N = 2 ** n
        return int(np.round(np.pi / 4 * np.sqrt(N / m)))


@dataclass
class GroverResult:
    """Result of Grover search"""
    solution: int
    probability: float
    iterations: int
    oracle_calls: int
    success: bool
    runtime: float
    amplitude_history: List[float] = field(default_factory=list)
    measured_states: Dict[int, int] = field(default_factory=dict)


class QuantumOracle:
    """Base class for quantum oracles"""

    def __init__(self, target_states: List[int], num_qubits: int):
        self.target_states = set(target_states)
        self.num_qubits = num_qubits
        self.call_count = 0

    def evaluate(self, state: int) -> bool:
        """Evaluate oracle on classical state"""
        self.call_count += 1
        return state in self.target_states

    def apply_phase(self, amplitudes: np.ndarray) -> np.ndarray:
        """Apply phase oracle to amplitude vector"""
        result = amplitudes.copy()
        for target in self.target_states:
            if target < len(result):
                result[target] *= -1
        return result

    def get_call_count(self) -> int:
        """Get number of oracle calls"""
        return self.call_count

    def reset_count(self):
        """Reset oracle call counter"""
        self.call_count = 0


class PatternOracle(QuantumOracle):
    """Oracle that matches patterns"""

    def __init__(self, pattern: str, num_qubits: int):
        # Find all states matching pattern
        target_states = self._find_pattern_matches(pattern, num_qubits)
        super().__init__(target_states, num_qubits)
        self.pattern = pattern

    def _find_pattern_matches(self, pattern: str, num_qubits: int) -> List[int]:
        """Find all states matching the pattern"""
        matches = []
        wildcard = '*'

        for state in range(2 ** num_qubits):
            binary = format(state, f'0{num_qubits}b')
            match = True

            for i, (p_bit, b_bit) in enumerate(zip(pattern, binary)):
                if p_bit != wildcard and p_bit != b_bit:
                    match = False
                    break

            if match:
                matches.append(state)

        return matches


class BooleanOracle(QuantumOracle):
    """Oracle based on boolean function"""

    def __init__(self, boolean_fn: Callable[[int], bool], num_qubits: int):
        # Precompute target states
        target_states = [s for s in range(2 ** num_qubits) if boolean_fn(s)]
        super().__init__(target_states, num_qubits)
        self.boolean_fn = boolean_fn

    def evaluate(self, state: int) -> bool:
        """Evaluate using boolean function"""
        self.call_count += 1
        return self.boolean_fn(state)


class GroverSearch:
    """
    Optimized Grover's search algorithm implementation
    Supports multiple oracle types and adaptive iteration
    """

    def __init__(self, config: Optional[GroverConfig] = None):
        self.config = config or GroverConfig()
        self.oracle: Optional[QuantumOracle] = None
        self.iteration_history: List[Dict[str, Any]] = []

    def set_oracle(self, oracle: QuantumOracle):
        """Set the quantum oracle"""
        self.oracle = oracle
        self.config.num_solutions = len(oracle.target_states)

    def create_simple_oracle(self, target_state: int) -> QuantumOracle:
        """Create a simple single-target oracle"""
        return QuantumOracle([target_state], self.config.num_qubits)

    def create_pattern_oracle(self, pattern: str) -> PatternOracle:
        """Create a pattern-matching oracle"""
        return PatternOracle(pattern, self.config.num_qubits)

    def create_boolean_oracle(self, boolean_fn: Callable[[int], bool]) -> BooleanOracle:
        """Create a boolean function oracle"""
        return BooleanOracle(boolean_fn, self.config.num_qubits)

    def _initialize_state(self) -> np.ndarray:
        """Initialize uniform superposition"""
        n = self.config.num_qubits
        N = 2 ** n
        return np.ones(N) / np.sqrt(N)

    def _apply_oracle(self, amplitudes: np.ndarray) -> np.ndarray:
        """Apply oracle (phase inversion)"""
        if self.oracle is None:
            raise ValueError("Oracle not set")
        return self.oracle.apply_phase(amplitudes)

    def _apply_diffusion(self, amplitudes: np.ndarray) -> np.ndarray:
        """Apply diffusion operator (inversion about average)"""
        n = self.config.num_qubits
        N = 2 ** n

        # Inversion about average
        mean = np.mean(amplitudes)
        return 2 * mean - amplitudes

    def _apply_partial_diffusion(self, amplitudes: np.ndarray, fraction: float) -> np.ndarray:
        """Apply partial diffusion for amplitude amplification"""
        mean = np.mean(amplitudes)
        return amplitudes + fraction * (2 * mean - amplitudes)

    def _get_target_probability(self, amplitudes: np.ndarray) -> float:
        """Get probability of measuring a target state"""
        if self.oracle is None:
            return 0.0

        probability = 0.0
        for target in self.oracle.target_states:
            if target < len(amplitudes):
                probability += np.abs(amplitudes[target]) ** 2

        return probability

    def _measure_state(self, amplitudes: np.ndarray) -> int:
        """Measure state according to amplitude probabilities"""
        probabilities = np.abs(amplitudes) ** 2
        probabilities /= np.sum(probabilities)
        return np.random.choice(len(amplitudes), p=probabilities)

    def search(self, num_shots: int = 1) -> GroverResult:
        """
        Execute Grover search

        Args:
            num_shots: Number of measurement shots

        Returns:
            GroverResult with solution and statistics
        """
        if self.oracle is None:
            raise ValueError("Oracle must be set before search")

        start_time = time.time()

        # Determine number of iterations
        if self.config.use_fixed_iterations:
            num_iterations = self.config.max_iterations
        else:
            num_iterations = self.config.optimal_iterations()

        logger.info(f"Running Grover search with {num_iterations} iterations")

        # Initialize
        amplitudes = self._initialize_state()
        amplitude_history = [self._get_target_probability(amplitudes)]

        # Grover iterations
        for iteration in range(num_iterations):
            # Apply oracle
            amplitudes = self._apply_oracle(amplitudes)

            # Apply diffusion
            if self.config.use_partial_diffusion:
                fraction = 1.0 - (iteration / num_iterations) * 0.5
                amplitudes = self._apply_partial_diffusion(amplitudes, fraction)
            else:
                amplitudes = self._apply_diffusion(amplitudes)

            # Record amplitude
            target_prob = self._get_target_probability(amplitudes)
            amplitude_history.append(target_prob)

            # Check if target probability reached
            if target_prob >= self.config.target_probability:
                logger.info(f"Target probability reached at iteration {iteration}")
                break

        # Measure
        measured_states: Dict[int, int] = {}
        for _ in range(num_shots):
            measured_state = self._measure_state(amplitudes)
            measured_states[measured_state] = measured_states.get(measured_state, 0) + 1

        # Find most frequent solution
        if measured_states:
            solution = max(measured_states, key=measured_states.get)
            probability = measured_states[solution] / num_shots
        else:
            solution = -1
            probability = 0.0

        # Verify solution
        success = self.oracle.evaluate(solution) if solution >= 0 else False

        runtime = time.time() - start_time

        result = GroverResult(
            solution=solution,
            probability=probability,
            iterations=len(amplitude_history) - 1,
            oracle_calls=self.oracle.get_call_count(),
            success=success,
            runtime=runtime,
            amplitude_history=amplitude_history,
            measured_states=measured_states
        )

        self.iteration_history.append({
            "result": result,
            "config": self.config
        })

        return result

    def search_with_adaptive_iterations(self, max_trials: int = 10) -> GroverResult:
        """
        Search with adaptive iteration count
        Tries different iteration counts to find optimal
        """
        best_result = None
        best_probability = 0.0

        n = self.config.num_qubits
        N = 2 ** n

        for trial in range(max_trials):
            # Try different iteration counts around optimal
            offset = (trial - max_trials // 2) * 2
            self.config.max_iterations = max(1, self.config.optimal_iterations() + offset)

            result = self.search(num_shots=100)

            if result.probability > best_probability:
                best_probability = result.probability
                best_result = result

            if result.probability >= self.config.target_probability:
                break

        return best_result or result

    def multi_target_search(self, target_states: List[int]) -> List[GroverResult]:
        """Search for multiple targets simultaneously"""
        self.set_oracle(QuantumOracle(target_states, self.config.num_qubits))

        results = []
        measured_solutions: Set[int] = set()

        # Run multiple searches to find all targets
        for _ in range(len(target_states) * 3):  # Extra attempts for robustness
            result = self.search(num_shots=50)

            if result.success and result.solution not in measured_solutions:
                results.append(result)
                measured_solutions.add(result.solution)

                # Remove found target from oracle
                remaining = self.oracle.target_states - {result.solution}
                self.set_oracle(QuantumOracle(list(remaining), self.config.num_qubits))

            if len(measured_solutions) >= len(target_states):
                break

        return results

    def amplitude_amplification_search(
        self,
        state_preparation: Callable[[], np.ndarray],
        num_iterations: int
    ) -> GroverResult:
        """
        Amplitude amplification with custom state preparation

        Args:
            state_preparation: Function that prepares initial state
            num_iterations: Number of amplification iterations

        Returns:
            GroverResult
        """
        start_time = time.time()

        # Prepare initial state
        amplitudes = state_preparation()
        amplitude_history = [self._get_target_probability(amplitudes)]

        # Amplitude amplification iterations
        for _ in range(num_iterations):
            amplitudes = self._apply_oracle(amplitudes)
            amplitudes = self._apply_diffusion(amplitudes)
            amplitude_history.append(self._get_target_probability(amplitudes))

        # Measure
        measured_state = self._measure_state(amplitudes)
        success = self.oracle.evaluate(measured_state)

        return GroverResult(
            solution=measured_state,
            probability=amplitude_history[-1],
            iterations=num_iterations,
            oracle_calls=self.oracle.get_call_count(),
            success=success,
            runtime=time.time() - start_time,
            amplitude_history=amplitude_history,
            measured_states={measured_state: 1}
        )

    def quantum_counting(self, precision: int = 8) -> Tuple[int, float]:
        """
        Estimate number of solutions using quantum counting

        Args:
            precision: Number of precision qubits

        Returns:
            Tuple of (estimated_count, confidence)
        """
        # Phase estimation to count solutions
        n = self.config.num_qubits
        N = 2 ** n

        # Simulate phase estimation
        theta = np.arcsin(np.sqrt(len(self.oracle.target_states) / N))

        # Add noise based on precision
        noise = np.random.normal(0, 1.0 / (2 ** precision))
        estimated_theta = theta + noise

        # Convert to count
        estimated_count = int(np.round(N * np.sin(estimated_theta) ** 2))
        confidence = 1.0 - 1.0 / (2 ** precision)

        return estimated_count, confidence

    def find_collision(
        self,
        hash_function: Callable[[int], int],
        num_elements: int
    ) -> Optional[Tuple[int, int]]:
        """
        Find collision in hash function using Grover

        Args:
            hash_function: Hash function to find collision for
            num_elements: Number of elements to search

        Returns:
            Tuple of colliding elements or None
        """
        # Create oracle that marks collisions
        def collision_oracle(state: int) -> bool:
            x = state // num_elements
            y = state % num_elements
            return x < y and hash_function(x) == hash_function(y)

        self.set_oracle(self.create_boolean_oracle(collision_oracle))

        # Search for collision
        result = self.search(num_shots=100)

        if result.success:
            x = result.solution // num_elements
            y = result.solution % num_elements
            return (x, y)

        return None

    def solve_sat(
        self,
        num_variables: int,
        clauses: List[Tuple[int, ...]]
    ) -> Optional[List[bool]]:
        """
        Solve SAT problem using Grover

        Args:
            num_variables: Number of boolean variables
            clauses: List of clauses (each clause is tuple of literals)

        Returns:
            Satisfying assignment or None
        """
        self.config.num_qubits = num_variables

        # Create SAT oracle
        def sat_oracle(assignment: int) -> bool:
            for clause in clauses:
                clause_satisfied = False
                for literal in clause:
                    var = abs(literal) - 1
                    is_negated = literal < 0
                    var_value = (assignment >> var) & 1

                    if is_negated:
                        var_value = not var_value

                    if var_value:
                        clause_satisfied = True
                        break

                if not clause_satisfied:
                    return False

            return True

        self.set_oracle(self.create_boolean_oracle(sat_oracle))

        # Search for solution
        result = self.search(num_shots=100)

        if result.success:
            # Convert to boolean assignment
            assignment = []
            for i in range(num_variables):
                assignment.append(bool((result.solution >> i) & 1))
            return assignment

        return None

    def database_search(
        self,
        database: List[Any],
        predicate: Callable[[Any], bool]
    ) -> Optional[Tuple[int, Any]]:
        """
        Search database using Grover

        Args:
            database: List of items to search
            predicate: Function to test if item matches

        Returns:
            Tuple of (index, item) or None
        """
        # Determine number of qubits needed
        self.config.num_qubits = int(np.ceil(np.log2(len(database))))

        # Create oracle
        def db_oracle(index: int) -> bool:
            if index < len(database):
                return predicate(database[index])
            return False

        self.set_oracle(self.create_boolean_oracle(db_oracle))

        # Search
        result = self.search(num_shots=100)

        if result.success and result.solution < len(database):
            return (result.solution, database[result.solution])

        return None

    def minimum_finding(
        self,
        values: List[float],
        num_iterations: int = 10
    ) -> Tuple[int, float]:
        """
        Find minimum value using Grover-based approach

        Args:
            values: List of values to find minimum of
            num_iterations: Number of iterations

        Returns:
            Tuple of (min_index, min_value)
        """
        n = int(np.ceil(np.log2(len(values))))
        self.config.num_qubits = n

        current_threshold = np.median(values)

        for iteration in range(num_iterations):
            # Create oracle for values below threshold
            def min_oracle(index: int) -> bool:
                if index < len(values):
                    return values[index] < current_threshold
                return False

            self.set_oracle(self.create_boolean_oracle(min_oracle))

            # Search
            result = self.search(num_shots=50)

            if result.success:
                # Update threshold
                current_threshold = values[result.solution]
            else:
                # No values below threshold, we're done
                break

        # Find actual minimum
        min_index = min(range(len(values)), key=lambda i: values[i])
        return min_index, values[min_index]

    def get_iteration_history(self) -> List[Dict[str, Any]]:
        """Get history of all searches"""
        return self.iteration_history

    def reset(self):
        """Reset search state"""
        self.oracle = None
        self.iteration_history = []
        if self.oracle:
            self.oracle.reset_count()


class GroverOptimizer:
    """
    Optimization using Grover's algorithm
    """

    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.searcher = GroverSearch(GroverConfig(num_qubits=num_qubits))

    def minimize(
        self,
        objective_fn: Callable[[int], float],
        bounds: Optional[Tuple[int, int]] = None
    ) -> Tuple[int, float]:
        """
        Minimize objective function using Grover

        Args:
            objective_fn: Function to minimize
            bounds: Optional (min, max) bounds

        Returns:
            Tuple of (minimizer, minimum_value)
        """
        N = 2 ** self.num_qubits

        if bounds:
            search_space = range(bounds[0], min(bounds[1] + 1, N))
        else:
            search_space = range(N)

        # Evaluate all points (for small problems)
        if N <= 256:
            values = {x: objective_fn(x) for x in search_space}
            min_x = min(values, key=values.get)
            return min_x, values[min_x]

        # For larger problems, use threshold-based search
        best_value = float('inf')
        best_x = 0

        for threshold in np.linspace(0, 100, 20):
            def threshold_oracle(x: int) -> bool:
                return x in search_space and objective_fn(x) < threshold

            self.searcher.set_oracle(
                self.searcher.create_boolean_oracle(threshold_oracle)
            )

            result = self.searcher.search(num_shots=50)

            if result.success:
                value = objective_fn(result.solution)
                if value < best_value:
                    best_value = value
                    best_x = result.solution

        return best_x, best_value

    def maximize(
        self,
        objective_fn: Callable[[int], float],
        bounds: Optional[Tuple[int, int]] = None
    ) -> Tuple[int, float]:
        """Maximize objective function"""
        def neg_objective(x: int) -> float:
            return -objective_fn(x)

        return self.minimize(neg_objective, bounds)


# Utility functions
def grover_search_simple(
    target: int,
    num_qubits: int,
    num_shots: int = 100
) -> GroverResult:
    """Simple Grover search for single target"""
    config = GroverConfig(num_qubits=num_qubits)
    searcher = GroverSearch(config)
    searcher.set_oracle(searcher.create_simple_oracle(target))
    return searcher.search(num_shots=num_shots)


def grover_pattern_search(
    pattern: str,
    num_qubits: int,
    num_shots: int = 100
) -> GroverResult:
    """Search for pattern in quantum states"""
    config = GroverConfig(num_qubits=num_qubits)
    searcher = GroverSearch(config)
    searcher.set_oracle(searcher.create_pattern_oracle(pattern))
    return searcher.search(num_shots=num_shots)


def benchmark_grover(num_qubits_list: List[int], num_trials: int = 10) -> Dict[str, Any]:
    """Benchmark Grover search on different problem sizes"""
    results = {}

    for n in num_qubits_list:
        trial_results = []

        for _ in range(num_trials):
            target = np.random.randint(0, 2 ** n)
            result = grover_search_simple(target, n, num_shots=100)
            trial_results.append(result)

        success_rate = sum(1 for r in trial_results if r.success) / num_trials
        avg_runtime = np.mean([r.runtime for r in trial_results])
        avg_iterations = np.mean([r.iterations for r in trial_results])

        results[n] = {
            "success_rate": success_rate,
            "avg_runtime": avg_runtime,
            "avg_iterations": avg_iterations,
            "theoretical_optimal": int(np.round(np.pi / 4 * np.sqrt(2 ** n)))
        }

    return results


# Example usage
if __name__ == "__main__":
    # Test simple search
    print("Testing simple Grover search...")
    result = grover_search_simple(target=42, num_qubits=8)
    print(f"Solution: {result.solution}, Success: {result.success}")
    print(f"Probability: {result.probability:.4f}, Iterations: {result.iterations}")

    # Test pattern search
    print("\nTesting pattern search...")
    pattern_result = grover_pattern_search(pattern="1*01*", num_qubits=8)
    print(f"Pattern matches found: {len(pattern_result.measured_states)}")

    # Test SAT solving
    print("\nTesting SAT solving...")
    searcher = GroverSearch(GroverConfig(num_qubits=3))
    clauses = [(1, 2), (-1, 3), (2, -3)]
    sat_solution = searcher.solve_sat(num_variables=3, clauses=clauses)
    print(f"SAT solution: {sat_solution}")

    # Benchmark
    print("\nBenchmarking...")
    benchmark = benchmark_grover([4, 6, 8], num_trials=5)
    for n, metrics in benchmark.items():
        print(f"n={n}: success_rate={metrics['success_rate']:.2%}, "
              f"avg_runtime={metrics['avg_runtime']:.4f}s")
