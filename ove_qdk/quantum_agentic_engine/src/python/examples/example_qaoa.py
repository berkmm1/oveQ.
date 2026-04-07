#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - QAOA Examples
Demonstrates Quantum Approximate Optimization Algorithm
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from optimization.quantum_optimizer import QAOA, QuantumOptimizer, OptimizerConfig, OptimizerType
import time


def example_max_cut():
    """Example: Max-Cut problem"""
    print("=" * 60)
    print("EXAMPLE 1: Max-Cut Problem")
    print("=" * 60)

    # Define graph (4-node cycle)
    num_nodes = 4
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

    print(f"\nGraph: {num_nodes} nodes, {len(edges)} edges")
    print(f"Edges: {edges}")

    # Build cost Hamiltonian for Max-Cut
    # H = 0.5 * Σ (1 - Z_i Z_j) for edges (i,j)
    dim = 2 ** num_nodes
    cost_hamiltonian = np.zeros((dim, dim), dtype=complex)

    for i, j in edges:
        # Z_i Z_j term
        zz = np.eye(1)
        for k in range(num_nodes):
            if k == i or k == j:
                zz = np.kron(zz, np.array([[1, 0], [0, -1]]))
            else:
                zz = np.kron(zz, np.eye(2))

        cost_hamiltonian += 0.5 * (np.eye(dim) - zz)

    # Mixer Hamiltonian: Σ X_i
    mixer_hamiltonian = np.zeros((dim, dim), dtype=complex)
    for i in range(num_nodes):
        x_term = np.eye(1)
        for k in range(num_nodes):
            if k == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        mixer_hamiltonian += x_term

    # Create QAOA
    qaoa = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        mixer_hamiltonian=mixer_hamiltonian,
        num_qubits=num_nodes,
        num_layers=2
    )

    # Optimize
    print(f"\nRunning QAOA with {qaoa.num_layers} layers...")
    start = time.time()
    result = qaoa.optimize()
    elapsed = time.time() - start

    # Extract solution
    gammas = result.optimal_parameters[::2]
    betas = result.optimal_parameters[1::2]

    print(f"\nResults:")
    print(f"  Optimal cost: {result.optimal_value:.4f}")
    print(f"  Gammas: {gammas}")
    print(f"  Betas: {betas}")
    print(f"  Iterations: {result.num_iterations}")
    print(f"  Runtime: {elapsed:.4f}s")

    # Find best cut
    best_cut_value = 0
    best_partition = None

    for partition in range(2 ** num_nodes):
        cut_value = 0
        for i, j in edges:
            bit_i = (partition >> i) & 1
            bit_j = (partition >> j) & 1
            if bit_i != bit_j:
                cut_value += 1

        if cut_value > best_cut_value:
            best_cut_value = cut_value
            best_partition = partition

    print(f"\nBest classical solution:")
    print(f"  Partition: {format(best_partition, f'0{num_nodes}b')}")
    print(f"  Cut value: {best_cut_value}")
    print(f"  Approximation ratio: {-result.optimal_value / best_cut_value:.4f}")

    return result


def example_tsp():
    """Example: Traveling Salesman Problem"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Traveling Salesman Problem")
    print("=" * 60)

    # 3-city TSP
    num_cities = 3

    # Distance matrix
    distances = np.array([
        [0, 2, 3],
        [2, 0, 4],
        [3, 4, 0]
    ])

    print(f"\nTSP with {num_cities} cities")
    print(f"Distance matrix:\n{distances}")

    # For TSP, we need n^2 qubits (n cities, n positions)
    num_qubits = num_cities ** 2
    dim = 2 ** num_qubits

    # Build cost Hamiltonian (simplified)
    cost_hamiltonian = np.zeros((dim, dim), dtype=complex)

    # Distance terms
    for i in range(num_cities):
        for j in range(num_cities):
            if i != j:
                for pos in range(num_cities):
                    next_pos = (pos + 1) % num_cities

                    # Add distance contribution
                    # (simplified representation)
                    cost_hamiltonian += distances[i, j] * 0.1 * np.eye(dim)

    # Mixer Hamiltonian
    mixer_hamiltonian = np.zeros((dim, dim), dtype=complex)
    for i in range(num_qubits):
        x_term = np.eye(1)
        for k in range(num_qubits):
            if k == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        mixer_hamiltonian += x_term

    # Create QAOA
    qaoa = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        mixer_hamiltonian=mixer_hamiltonian,
        num_qubits=num_qubits,
        num_layers=1
    )

    # Optimize
    print(f"\nRunning QAOA...")
    result = qaoa.optimize()

    print(f"\nResults:")
    print(f"  Optimal cost: {result.optimal_value:.4f}")

    # Known optimal solution
    optimal_tour = [0, 1, 2, 0]
    optimal_cost = distances[0, 1] + distances[1, 2] + distances[2, 0]

    print(f"\nOptimal TSP solution:")
    print(f"  Tour: {optimal_tour}")
    print(f"  Cost: {optimal_cost}")

    return result


def example_vertex_cover():
    """Example: Minimum Vertex Cover"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Minimum Vertex Cover")
    print("=" * 60)

    # Define graph
    num_nodes = 4
    edges = [(0, 1), (1, 2), (2, 3)]

    print(f"\nGraph: {num_nodes} nodes, {len(edges)} edges")
    print(f"Edges: {edges}")

    dim = 2 ** num_nodes

    # Cost Hamiltonian: minimize Σ x_i + penalty for uncovered edges
    penalty = 10.0

    cost_hamiltonian = np.zeros((dim, dim), dtype=complex)

    # Vertex costs
    for i in range(num_nodes):
        z_term = np.eye(1)
        for k in range(num_nodes):
            if k == i:
                z_term = np.kron(z_term, np.array([[0, 0], [0, 1]]))
            else:
                z_term = np.kron(z_term, np.eye(2))
        cost_hamiltonian += z_term

    # Edge constraints
    for i, j in edges:
        # Penalty if neither endpoint is in cover
        constraint = np.eye(1)
        for k in range(num_nodes):
            if k == i or k == j:
                # (1 - Z)/2 = projector onto |0>
                proj = np.array([[1, 0], [0, 0]])
                constraint = np.kron(constraint, proj)
            else:
                constraint = np.kron(constraint, np.eye(2))

        cost_hamiltonian += penalty * constraint

    # Mixer
    mixer_hamiltonian = np.zeros((dim, dim), dtype=complex)
    for i in range(num_nodes):
        x_term = np.eye(1)
        for k in range(num_nodes):
            if k == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        mixer_hamiltonian += x_term

    # QAOA
    qaoa = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        mixer_hamiltonian=mixer_hamiltonian,
        num_qubits=num_nodes,
        num_layers=2
    )

    result = qaoa.optimize()

    print(f"\nResults:")
    print(f"  Optimal cost: {result.optimal_value:.4f}")

    # Find optimal vertex cover
    min_cover_size = num_nodes
    for cover in range(2 ** num_nodes):
        # Check if valid cover
        valid = True
        for i, j in edges:
            in_cover_i = (cover >> i) & 1
            in_cover_j = (cover >> j) & 1
            if not in_cover_i and not in_cover_j:
                valid = False
                break

        if valid:
            cover_size = bin(cover).count('1')
            if cover_size < min_cover_size:
                min_cover_size = cover_size

    print(f"\nOptimal vertex cover size: {min_cover_size}")

    return result


def example_number_partitioning():
    """Example: Number Partitioning Problem"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Number Partitioning")
    print("=" * 60)

    # Numbers to partition
    numbers = [3, 1, 4, 2, 2]

    print(f"\nNumbers: {numbers}")
    print(f"Total sum: {sum(numbers)}")
    print(f"Target per subset: {sum(numbers) / 2}")

    num_numbers = len(numbers)
    dim = 2 ** num_numbers

    # Cost Hamiltonian: minimize (Σ s_i * n_i)^2
    # where s_i = ±1
    cost_hamiltonian = np.zeros((dim, dim), dtype=complex)

    # Expand (Σ s_i n_i)^2 = Σ s_i^2 n_i^2 + 2 Σ_{i<j} s_i s_j n_i n_j
    # s_i^2 = 1, so first term is constant

    # Interaction terms
    for i in range(num_numbers):
        for j in range(i + 1, num_numbers):
            # Z_i Z_j term (since Z|0> = |0>, Z|1> = -|1>)
            zz = np.eye(1)
            for k in range(num_numbers):
                if k == i or k == j:
                    zz = np.kron(zz, np.array([[1, 0], [0, -1]]))
                else:
                    zz = np.kron(zz, np.eye(2))

            cost_hamiltonian += 2 * numbers[i] * numbers[j] * zz

    # Mixer
    mixer_hamiltonian = np.zeros((dim, dim), dtype=complex)
    for i in range(num_numbers):
        x_term = np.eye(1)
        for k in range(num_numbers):
            if k == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        mixer_hamiltonian += x_term

    # QAOA
    qaoa = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        mixer_hamiltonian=mixer_hamiltonian,
        num_qubits=num_numbers,
        num_layers=2
    )

    result = qaoa.optimize()

    print(f"\nResults:")
    print(f"  Optimal cost: {result.optimal_value:.4f}")

    # Find best partition
    best_diff = sum(numbers)
    best_partition = None

    for partition in range(2 ** num_numbers):
        sum_a = sum(numbers[i] for i in range(num_numbers) if (partition >> i) & 1)
        sum_b = sum(numbers) - sum_a
        diff = abs(sum_a - sum_b)

        if diff < best_diff:
            best_diff = diff
            best_partition = partition

    subset_a = [numbers[i] for i in range(num_numbers) if (best_partition >> i) & 1]
    subset_b = [numbers[i] for i in range(num_numbers) if not (best_partition >> i) & 1]

    print(f"\nBest partition:")
    print(f"  Subset A: {subset_a} (sum = {sum(subset_a)})")
    print(f"  Subset B: {subset_b} (sum = {sum(subset_b)})")
    print(f"  Difference: {best_diff}")

    return result


def example_portfolio_optimization():
    """Example: Portfolio Optimization"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Portfolio Optimization")
    print("=" * 60)

    # Assets
    num_assets = 3

    # Expected returns
    returns = np.array([0.1, 0.15, 0.12])

    # Covariance matrix
    covariance = np.array([
        [0.1, 0.02, 0.01],
        [0.02, 0.15, 0.03],
        [0.01, 0.03, 0.12]
    ])

    # Risk tolerance
    risk_tolerance = 0.5

    print(f"\nAssets: {num_assets}")
    print(f"Returns: {returns}")
    print(f"Risk tolerance: {risk_tolerance}")

    # Build QUBO
    # Maximize: return - risk_tolerance * risk
    # = Σ r_i x_i - risk_tolerance * Σ Σ σ_{ij} x_i x_j

    dim = 2 ** num_assets
    cost_hamiltonian = np.zeros((dim, dim), dtype=complex)

    # Linear terms (returns)
    for i in range(num_assets):
        z_term = np.eye(1)
        for k in range(num_assets):
            if k == i:
                # (1 - Z)/2 maps to {0, 1}
                z_term = np.kron(z_term, np.array([[0, 0], [0, 1]]))
            else:
                z_term = np.kron(z_term, np.eye(2))
        cost_hamiltonian -= returns[i] * z_term

    # Quadratic terms (risk)
    for i in range(num_assets):
        for j in range(num_assets):
            zz = np.eye(1)
            for k in range(num_assets):
                if k == i or k == j:
                    zz = np.kron(zz, np.array([[1, 0], [0, -1]]))
                else:
                    zz = np.kron(zz, np.eye(2))

            cost_hamiltonian += risk_tolerance * covariance[i, j] * zz

    # Mixer
    mixer_hamiltonian = np.zeros((dim, dim), dtype=complex)
    for i in range(num_assets):
        x_term = np.eye(1)
        for k in range(num_assets):
            if k == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        mixer_hamiltonian += x_term

    # QAOA
    qaoa = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        mixer_hamiltonian=mixer_hamiltonian,
        num_qubits=num_assets,
        num_layers=2
    )

    result = qaoa.optimize()

    print(f"\nResults:")
    print(f"  Optimal cost: {result.optimal_value:.4f}")

    return result


def example_different_layers():
    """Example: Compare different numbers of QAOA layers"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Layer Comparison")
    print("=" * 60)

    # Simple Max-Cut on 4-node graph
    num_nodes = 4
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

    dim = 2 ** num_nodes
    cost_hamiltonian = np.zeros((dim, dim), dtype=complex)

    for i, j in edges:
        zz = np.eye(1)
        for k in range(num_nodes):
            if k == i or k == j:
                zz = np.kron(zz, np.array([[1, 0], [0, -1]]))
            else:
                zz = np.kron(zz, np.eye(2))
        cost_hamiltonian += 0.5 * (np.eye(dim) - zz)

    mixer_hamiltonian = np.zeros((dim, dim), dtype=complex)
    for i in range(num_nodes):
        x_term = np.eye(1)
        for k in range(num_nodes):
            if k == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        mixer_hamiltonian += x_term

    # Test different layer counts
    layer_counts = [1, 2, 3, 4]

    print(f"\nComparing QAOA with different layer counts:")
    print(f"Graph: {num_nodes} nodes, {len(edges)} edges")

    results = []

    for num_layers in layer_counts:
        print(f"\n  Testing {num_layers} layer(s)...")

        qaoa = QAOA(
            cost_hamiltonian=cost_hamiltonian,
            mixer_hamiltonian=mixer_hamiltonian,
            num_qubits=num_nodes,
            num_layers=num_layers
        )

        start = time.time()
        result = qaoa.optimize()
        elapsed = time.time() - start

        print(f"    Cost: {result.optimal_value:.4f}")
        print(f"    Iterations: {result.num_iterations}")
        print(f"    Runtime: {elapsed:.4f}s")

        results.append((num_layers, result, elapsed))

    # Summary
    print(f"\nSummary:")
    for num_layers, result, elapsed in results:
        print(f"  {num_layers} layer(s): cost = {result.optimal_value:.4f}, "
              f"time = {elapsed:.4f}s")

    return results


def run_all_examples():
    """Run all QAOA examples"""
    print("\n" + "=" * 60)
    print("QUANTUM APPROXIMATE OPTIMIZATION ALGORITHM EXAMPLES")
    print("=" * 60)

    examples = [
        ("Max-Cut", example_max_cut),
        ("TSP", example_tsp),
        ("Vertex Cover", example_vertex_cover),
        ("Number Partitioning", example_number_partitioning),
        ("Portfolio Optimization", example_portfolio_optimization),
        ("Layer Comparison", example_different_layers),
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
            import traceback
            traceback.print_exc()
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

    parser = argparse.ArgumentParser(description="QAOA Examples")
    parser.add_argument(
        "--example",
        type=int,
        choices=range(1, 7),
        help="Run specific example (1-6)"
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
            example_max_cut,
            example_tsp,
            example_vertex_cover,
            example_number_partitioning,
            example_portfolio_optimization,
            example_different_layers,
        ]
        examples[args.example - 1]()
    else:
        # Run Max-Cut by default
        example_max_cut()
