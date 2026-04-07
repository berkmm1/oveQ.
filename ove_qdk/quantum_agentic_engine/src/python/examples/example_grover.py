#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Grover Search Example
Demonstrates Grover's quantum search algorithm
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from algorithms.quantum_grover import GroverSearch, GroverConfig, GroverOptimizer
import time


def example_simple_search():
    """Example: Simple search for a target value"""
    print("=" * 60)
    print("EXAMPLE 1: Simple Grover Search")
    print("=" * 60)

    # Configuration
    num_qubits = 8
    target = 42

    print(f"\nSearching for target: {target}")
    print(f"Search space size: {2 ** num_qubits}")
    print(f"Classical queries needed (average): {(2 ** num_qubits) / 2}")
    print(f"Quantum queries needed (optimal): {int(np.pi / 4 * np.sqrt(2 ** num_qubits))}")

    # Create Grover search
    config = GroverConfig(num_qubits=num_qubits)
    searcher = GroverSearch(config)

    # Create oracle for target
    searcher.set_oracle(searcher.create_simple_oracle(target))

    # Search
    start_time = time.time()
    result = searcher.search(num_shots=100)
    elapsed = time.time() - start_time

    print(f"\nResults:")
    print(f"  Solution found: {result.solution}")
    print(f"  Success: {result.success}")
    print(f"  Probability: {result.probability:.2%}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Oracle calls: {result.oracle_calls}")
    print(f"  Runtime: {elapsed:.4f}s")

    # Show amplitude history
    print(f"\nAmplitude evolution:")
    for i, amp in enumerate(result.amplitude_history[:5]):
        print(f"  Iteration {i}: {amp:.4f}")

    return result


def example_pattern_search():
    """Example: Search for pattern in database"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Pattern Search")
    print("=" * 60)

    num_qubits = 8
    pattern = "1*01*"  # Pattern with wildcards

    print(f"\nSearching for pattern: {pattern}")
    print("  * = any bit")

    config = GroverConfig(num_qubits=num_qubits)
    searcher = GroverSearch(config)

    # Create pattern oracle
    searcher.set_oracle(searcher.create_pattern_oracle(pattern))

    # Search
    result = searcher.search(num_shots=100)

    print(f"\nResults:")
    print(f"  Solution found: {result.solution} (binary: {format(result.solution, f'0{num_qubits}b')})")
    print(f"  Success: {result.success}")
    print(f"  Measured states: {len(result.measured_states)}")

    # Show top measurements
    print(f"\nTop measurements:")
    sorted_states = sorted(result.measured_states.items(), key=lambda x: x[1], reverse=True)
    for state, count in sorted_states[:5]:
        print(f"  State {state}: {count} shots")

    return result


def example_multi_target_search():
    """Example: Search for multiple targets"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Multi-Target Search")
    print("=" * 60)

    num_qubits = 8
    targets = [10, 20, 30, 40, 50]

    print(f"\nSearching for {len(targets)} targets: {targets}")

    config = GroverConfig(num_qubits=num_qubits)
    searcher = GroverSearch(config)

    # Multi-target search
    results = searcher.multi_target_search(targets)

    print(f"\nResults:")
    print(f"  Targets found: {len(results)}/{len(targets)}")

    for i, result in enumerate(results):
        print(f"\n  Target {i+1}:")
        print(f"    Solution: {result.solution}")
        print(f"    Probability: {result.probability:.2%}")
        print(f"    Success: {result.success}")

    return results


def example_database_search():
    """Example: Search in a database"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Database Search")
    print("=" * 60)

    # Create database
    database = [
        {"id": 0, "name": "Alice", "age": 30},
        {"id": 1, "name": "Bob", "age": 25},
        {"id": 2, "name": "Charlie", "age": 35},
        {"id": 3, "name": "Diana", "age": 28},
        {"id": 4, "name": "Eve", "age": 32},
    ]

    print(f"\nDatabase ({len(database)} entries):")
    for item in database:
        print(f"  {item}")

    # Search predicate
    def predicate(item):
        return item["age"] > 30

    print(f"\nSearching for: age > 30")

    config = GroverConfig(num_qubits=8)
    searcher = GroverSearch(config)

    # Database search
    result = searcher.database_search(database, predicate)

    if result:
        index, item = result
        print(f"\nResult found:")
        print(f"  Index: {index}")
        print(f"  Item: {item}")
    else:
        print("\nNo result found")

    return result


def example_sat_solver():
    """Example: Solve SAT problem using Grover"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: SAT Solver")
    print("=" * 60)

    num_variables = 3

    # Define CNF formula: (x1 OR x2) AND (NOT x1 OR x3) AND (x2 OR NOT x3)
    clauses = [
        (1, 2),      # x1 OR x2
        (-1, 3),     # NOT x1 OR x3
        (2, -3),     # x2 OR NOT x3
    ]

    print(f"\nCNF Formula:")
    for i, clause in enumerate(clauses):
        clause_str = " OR ".join([
            f"{'NOT ' if lit < 0 else ''}x{abs(lit)}"
            for lit in clause
        ])
        print(f"  Clause {i+1}: {clause_str}")

    config = GroverConfig(num_qubits=num_variables)
    searcher = GroverSearch(config)

    # Solve SAT
    solution = searcher.solve_sat(num_variables, clauses)

    if solution:
        print(f"\nSolution found:")
        for i, val in enumerate(solution):
            print(f"  x{i+1} = {int(val)}")

        # Verify solution
        print(f"\nVerification:")
        for i, clause in enumerate(clauses):
            satisfied = False
            for lit in clause:
                var_idx = abs(lit) - 1
                var_val = solution[var_idx]
                if lit < 0:
                    var_val = not var_val
                if var_val:
                    satisfied = True
                    break
            status = "✓" if satisfied else "✗"
            print(f"  Clause {i+1}: {status}")
    else:
        print("\nNo solution found (formula is unsatisfiable)")

    return solution


def example_minimum_finding():
    """Example: Find minimum value"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Minimum Finding")
    print("=" * 60)

    # Values to minimize
    values = [5.2, 3.1, 8.7, 1.4, 6.9, 2.8, 9.3, 4.5]

    print(f"\nValues: {values}")
    print(f"Classical minimum: {min(values)} at index {np.argmin(values)}")

    config = GroverConfig(num_qubits=8)
    searcher = GroverSearch(config)

    # Find minimum
    min_index, min_value = searcher.minimum_finding(values, num_iterations=10)

    print(f"\nQuantum search result:")
    print(f"  Minimum index: {min_index}")
    print(f"  Minimum value: {min_value}")

    return min_index, min_value


def example_collision_finding():
    """Example: Find collision in hash function"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Collision Finding")
    print("=" * 60)

    # Simple hash function
    def hash_function(x):
        return (x * 7 + 3) % 16

    num_elements = 16

    print(f"\nHash function: h(x) = (7x + 3) mod 16")
    print(f"Searching space: 0 to {num_elements-1}")

    # Show hash values
    print(f"\nHash values:")
    for x in range(num_elements):
        print(f"  h({x}) = {hash_function(x)}")

    config = GroverConfig(num_qubits=8)
    searcher = GroverSearch(config)

    # Find collision
    collision = searcher.find_collision(hash_function, num_elements)

    if collision:
        x, y = collision
        print(f"\nCollision found:")
        print(f"  h({x}) = h({y}) = {hash_function(x)}")
    else:
        print("\nNo collision found")

    return collision


def example_optimization():
    """Example: Optimization using Grover"""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Optimization")
    print("=" * 60)

    num_qubits = 6

    # Objective function: f(x) = -(x - 20)^2 + 100
    def objective(x):
        return -((x - 20) ** 2) + 100

    print(f"\nObjective: maximize f(x) = -(x - 20)^2 + 100")
    print(f"Search space: 0 to {2**num_qubits - 1}")
    print(f"Known maximum: f(20) = {objective(20)}")

    # Create optimizer
    optimizer = GroverOptimizer(num_qubits=num_qubits)

    # Maximize
    max_x, max_val = optimizer.maximize(objective)

    print(f"\nOptimization result:")
    print(f"  Optimal x: {max_x}")
    print(f"  Optimal value: {max_val}")

    return max_x, max_val


def example_adaptive_iterations():
    """Example: Adaptive iteration count"""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Adaptive Iterations")
    print("=" * 60)

    num_qubits = 8
    target = 100

    print(f"\nTarget: {target}")
    print(f"Optimal iterations: {int(np.pi / 4 * np.sqrt(2 ** num_qubits))}")

    config = GroverConfig(num_qubits=num_qubits)
    searcher = GroverSearch(config)
    searcher.set_oracle(searcher.create_simple_oracle(target))

    # Search with adaptive iterations
    result = searcher.search_with_adaptive_iterations(max_trials=10)

    print(f"\nResults:")
    print(f"  Solution: {result.solution}")
    print(f"  Probability: {result.probability:.2%}")
    print(f"  Iterations: {result.iterations}")

    return result


def example_benchmark():
    """Example: Benchmark Grover search"""
    print("\n" + "=" * 60)
    print("EXAMPLE 10: Benchmark")
    print("=" * 60)

    from algorithms.quantum_grover import benchmark_grover

    print(f"\nBenchmarking Grover search...")

    results = benchmark_grover([4, 6, 8], num_trials=5)

    print(f"\nResults:")
    for n, metrics in results.items():
        print(f"\n  n = {n} qubits:")
        print(f"    Success rate: {metrics['success_rate']:.2%}")
        print(f"    Avg runtime: {metrics['avg_runtime']:.4f}s")
        print(f"    Avg iterations: {metrics['avg_iterations']:.1f}")
        print(f"    Theoretical optimal: {metrics['theoretical_optimal']}")

    return results


def run_all_examples():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("GROVER SEARCH EXAMPLES")
    print("=" * 60)

    examples = [
        ("Simple Search", example_simple_search),
        ("Pattern Search", example_pattern_search),
        ("Multi-Target Search", example_multi_target_search),
        ("Database Search", example_database_search),
        ("SAT Solver", example_sat_solver),
        ("Minimum Finding", example_minimum_finding),
        ("Collision Finding", example_collision_finding),
        ("Optimization", example_optimization),
        ("Adaptive Iterations", example_adaptive_iterations),
        ("Benchmark", example_benchmark),
    ]

    results = []

    for name, example_func in examples:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print(f"{'='*60}")

            result = example_func()
            results.append((name, True, result))

        except Exception as e:
            print(f"Error in {name}: {e}")
            results.append((name, False, None))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, success, _ in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    successful = sum(1 for _, success, _ in results if success)
    print(f"\nTotal: {successful}/{len(results)} examples successful")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Grover Search Examples")
    parser.add_argument(
        "--example",
        type=int,
        choices=range(1, 11),
        help="Run specific example (1-10)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all examples"
    )

    args = parser.parse_args()

    if args.all:
        run_all_examples()
    elif args.example:
        examples = [
            example_simple_search,
            example_pattern_search,
            example_multi_target_search,
            example_database_search,
            example_sat_solver,
            example_minimum_finding,
            example_collision_finding,
            example_optimization,
            example_adaptive_iterations,
            example_benchmark,
        ]
        examples[args.example - 1]()
    else:
        # Run simple example by default
        example_simple_search()
