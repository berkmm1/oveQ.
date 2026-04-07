#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - VQE Examples
Demonstrates Variational Quantum Eigensolver for various problems
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from optimization.quantum_optimizer import VQE, QuantumOptimizer, OptimizerConfig, OptimizerType
import time


def example_simple_vqe():
    """Example: Simple VQE for 2-qubit Hamiltonian"""
    print("=" * 60)
    print("EXAMPLE 1: Simple VQE")
    print("=" * 60)

    # Simple Hamiltonian: H = Z ⊗ Z
    hamiltonian = np.array([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ], dtype=complex)

    print(f"\nHamiltonian:")
    print(hamiltonian)

    # Exact ground state energy
    eigenvalues = np.linalg.eigvalsh(hamiltonian)
    exact_energy = eigenvalues[0]
    print(f"\nExact ground state energy: {exact_energy:.6f}")

    # Simple ansatz: RY rotation
    def ansatz(params):
        theta = params[0]
        # Start from |00>
        state = np.array([1, 0, 0, 0], dtype=complex)

        # Apply RY(theta) to first qubit
        ry = np.array([
            [np.cos(theta/2), -np.sin(theta/2)],
            [np.sin(theta/2), np.cos(theta/2)]
        ], dtype=complex)

        # Apply to first qubit
        state = np.kron(ry, np.eye(2)) @ state

        return state

    # Create VQE
    vqe = VQE(
        hamiltonian=hamiltonian,
        ansatz=ansatz,
        num_parameters=1
    )

    # Find ground state
    start_time = time.time()
    result = vqe.find_ground_state()
    elapsed = time.time() - start_time

    print(f"\nVQE Results:")
    print(f"  Estimated energy: {result.optimal_value:.6f}")
    print(f"  Exact energy: {exact_energy:.6f}")
    print(f"  Error: {abs(result.optimal_value - exact_energy):.6f}")
    print(f"  Optimal parameters: {result.optimal_parameters}")
    print(f"  Iterations: {result.num_iterations}")
    print(f"  Runtime: {elapsed:.4f}s")

    return result


def example_h2_molecule():
    """Example: H2 molecule ground state"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: H2 Molecule Ground State")
    print("=" * 60)

    # H2 Hamiltonian at bond length 0.74 Angstrom
    # Simplified STO-3G basis

    # Hamiltonian coefficients
    h0 = -0.4696
    h1 = 0.2427
    h2 = 0.2427
    h3 = -0.4696

    # Two-electron terms
    h11 = 0.3312
    h22 = 0.3312
    h12 = 0.3312

    # Build Hamiltonian
    hamiltonian = np.zeros((4, 4), dtype=complex)

    # One-body terms
    hamiltonian[0, 0] = h0
    hamiltonian[1, 1] = h1
    hamiltonian[2, 2] = h2
    hamiltonian[3, 3] = h3

    # Two-body terms (simplified)
    hamiltonian[0, 0] += h11
    hamiltonian[1, 1] += h22
    hamiltonian[2, 2] += h12

    print(f"\nH2 Hamiltonian (simplified):")
    print(hamiltonian)

    # Exact solution
    eigenvalues = np.linalg.eigvalsh(hamiltonian)
    exact_energy = eigenvalues[0]
    print(f"\nExact ground state energy: {exact_energy:.6f} Hartree")

    # UCCSD-inspired ansatz
    def uccsd_ansatz(params):
        theta = params[0]
        phi = params[1]

        # Hartree-Fock reference: |1100>
        state = np.zeros(4, dtype=complex)
        state[3] = 1.0  # |11> in two-qubit basis

        # Excitation operator (simplified)
        # e^{i(theta * X1 X2 + phi * Y1 Y2)} |11>

        # Apply rotation
        rotation = np.array([
            [np.cos(theta), -1j*np.sin(theta)],
            [-1j*np.sin(theta), np.cos(theta)]
        ], dtype=complex)

        state = np.kron(rotation, np.eye(2)) @ state

        return state

    # Create VQE
    vqe = VQE(
        hamiltonian=hamiltonian,
        ansatz=uccsd_ansatz,
        num_parameters=2
    )

    # Optimize
    result = vqe.find_ground_state()

    print(f"\nVQE Results:")
    print(f"  Estimated energy: {result.optimal_value:.6f} Hartree")
    print(f"  Exact energy: {exact_energy:.6f} Hartree")
    print(f"  Error: {abs(result.optimal_value - exact_energy) * 1000:.3f} mHartree")

    return result


def example_ising_model():
    """Example: Ising model ground state"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Ising Model Ground State")
    print("=" * 60)

    num_spins = 4
    j_coupling = 1.0  # Interaction strength
    h_field = 0.5     # Transverse field

    print(f"\nIsing Model:")
    print(f"  Number of spins: {num_spins}")
    print(f"  J (coupling): {j_coupling}")
    print(f"  h (field): {h_field}")

    # Build Hamiltonian
    dim = 2 ** num_spins
    hamiltonian = np.zeros((dim, dim), dtype=complex)

    # Transverse field terms: -h * Σ X_i
    for i in range(num_spins):
        x_term = np.eye(1)
        for j in range(num_spins):
            if j == i:
                x_term = np.kron(x_term, np.array([[0, 1], [1, 0]]))
            else:
                x_term = np.kron(x_term, np.eye(2))
        hamiltonian -= h_field * x_term

    # Coupling terms: -J * Σ Z_i Z_{i+1}
    for i in range(num_spins - 1):
        zz_term = np.eye(1)
        for j in range(num_spins):
            if j == i or j == i + 1:
                zz_term = np.kron(zz_term, np.array([[1, 0], [0, -1]]))
            else:
                zz_term = np.kron(zz_term, np.eye(2))
        hamiltonian -= j_coupling * zz_term

    # Exact solution
    eigenvalues = np.linalg.eigvalsh(hamiltonian)
    exact_energy = eigenvalues[0]
    print(f"\nExact ground state energy: {exact_energy:.6f}")

    # Hardware-efficient ansatz
    def hea_ansatz(params):
        num_layers = 2
        params_per_layer = num_spins * 2  # RY and RZ for each qubit

        state = np.zeros(dim, dtype=complex)
        state[0] = 1.0  # |00...0>

        param_idx = 0

        for layer in range(num_layers):
            # Single-qubit rotations
            for i in range(num_spins):
                theta = params[param_idx]
                phi = params[param_idx + 1]
                param_idx += 2

                # Apply RY(theta) RZ(phi) to qubit i
                single_qubit = np.array([
                    [np.cos(theta/2), -np.sin(theta/2)],
                    [np.sin(theta/2), np.cos(theta/2)]
                ]) @ np.array([
                    [np.exp(-1j*phi/2), 0],
                    [0, np.exp(1j*phi/2)]
                ])

                # Build full operator
                op = np.eye(1)
                for j in range(num_spins):
                    if j == i:
                        op = np.kron(op, single_qubit)
                    else:
                        op = np.kron(op, np.eye(2))

                state = op @ state

            # Entangling layer: CNOT chain
            for i in range(num_spins - 1):
                cnot = np.array([
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                    [0, 0, 1, 0]
                ])

                op = np.eye(1)
                for j in range(num_spins):
                    if j == i:
                        op = np.kron(op, cnot)
                    elif j != i + 1:
                        op = np.kron(op, np.eye(2))

                state = op @ state

        return state

    # Create VQE
    num_params = num_spins * 2 * 2  # 2 layers
    vqe = VQE(
        hamiltonian=hamiltonian,
        ansatz=hea_ansatz,
        num_parameters=num_params
    )

    # Optimize with different optimizers
    print(f"\nTesting different optimizers:")

    optimizers = [
        ("COBYLA", OptimizerType.COBYLA),
        ("Adam", OptimizerType.ADAM),
    ]

    results = []

    for name, opt_type in optimizers:
        vqe.optimizer = QuantumOptimizer(OptimizerConfig(
            optimizer_type=opt_type,
            max_iterations=100,
            learning_rate=0.01
        ))

        result = vqe.find_ground_state()
        error = abs(result.optimal_value - exact_energy)

        print(f"  {name}:")
        print(f"    Energy: {result.optimal_value:.6f}")
        print(f"    Error: {error:.6f}")
        print(f"    Iterations: {result.num_iterations}")

        results.append((name, result))

    return results


def example_optimization_comparison():
    """Example: Compare optimization algorithms"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Optimization Algorithm Comparison")
    print("=" * 60)

    # Simple Hamiltonian
    hamiltonian = np.diag([1.0, -0.5, 0.3, -1.0])

    exact_energy = np.min(np.diag(hamiltonian))
    print(f"\nExact ground state energy: {exact_energy:.6f}")

    # Simple ansatz
    def ansatz(params):
        theta = params[0]
        state = np.array([np.cos(theta), np.sin(theta), 0, 0], dtype=complex)
        return state / np.linalg.norm(state)

    vqe = VQE(hamiltonian, ansatz, num_parameters=1)

    optimizers = [
        OptimizerType.COBYLA,
        OptimizerType.L_BFGS_B,
        OptimizerType.ADAM,
        OptimizerType.SGD,
    ]

    print(f"\nComparing optimizers:")

    for opt_type in optimizers:
        vqe.optimizer = QuantumOptimizer(OptimizerConfig(
            optimizer_type=opt_type,
            max_iterations=50,
            learning_rate=0.1
        ))

        start = time.time()
        result = vqe.find_ground_state()
        elapsed = time.time() - start

        error = abs(result.optimal_value - exact_energy)

        print(f"\n  {opt_type.name}:")
        print(f"    Energy: {result.optimal_value:.6f}")
        print(f"    Error: {error:.6e}")
        print(f"    Iterations: {result.num_iterations}")
        print(f"    Runtime: {elapsed:.4f}s")


def example_excited_states():
    """Example: Finding excited states with VQE"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Excited States")
    print("=" * 60)

    # Hamiltonian with multiple eigenvalues
    hamiltonian = np.diag([2.0, 1.0, 0.0, -1.0])

    eigenvalues = np.linalg.eigvalsh(hamiltonian)
    print(f"\nExact eigenvalues: {eigenvalues}")

    # Find ground state
    def ansatz(params):
        state = np.zeros(4, dtype=complex)
        state[0] = np.cos(params[0])
        state[1] = np.sin(params[0])
        return state

    vqe = VQE(hamiltonian, ansatz, num_parameters=1)
    ground_result = vqe.find_ground_state()

    print(f"\nGround state:")
    print(f"  Energy: {ground_result.optimal_value:.6f}")
    print(f"  Exact: {eigenvalues[0]:.6f}")

    # Find first excited state using orthogonality constraint
    # (simplified: use different initial parameters)
    def excited_ansatz(params):
        state = np.zeros(4, dtype=complex)
        state[2] = np.cos(params[0])
        state[3] = np.sin(params[0])
        return state

    vqe_excited = VQE(hamiltonian, excited_ansatz, num_parameters=1)
    excited_result = vqe_excited.find_ground_state()

    print(f"\nFirst excited state:")
    print(f"  Energy: {excited_result.optimal_value:.6f}")
    print(f"  Exact: {eigenvalues[1]:.6f}")


def example_noise_robustness():
    """Example: VQE with noisy simulation"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Noise Robustness")
    print("=" * 60)

    from simulation.quantum_simulator import DensityMatrixSimulator

    # Simple Hamiltonian
    hamiltonian = np.diag([1.0, -1.0])
    exact_energy = -1.0

    print(f"\nExact ground state energy: {exact_energy:.6f}")

    # Test different noise levels
    noise_levels = [0.0, 0.01, 0.05, 0.1]

    print(f"\nTesting noise robustness:")

    for noise in noise_levels:
        # Simulate with noise
        sim = DensityMatrixSimulator(num_qubits=1)

        # Simple state preparation
        state = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)
        rho = np.outer(state, state.conj())

        # Apply depolarizing noise
        rho_noisy = (1 - noise) * rho + noise * np.eye(2) / 2

        # Compute energy
        energy = np.real(np.trace(rho_noisy @ hamiltonian))
        error = abs(energy - exact_energy)

        print(f"  Noise level {noise:.2f}: Energy = {energy:.6f}, Error = {error:.6f}")


def run_all_examples():
    """Run all VQE examples"""
    print("\n" + "=" * 60)
    print("VARIATIONAL QUANTUM EIGENSOLVER EXAMPLES")
    print("=" * 60)

    examples = [
        ("Simple VQE", example_simple_vqe),
        ("H2 Molecule", example_h2_molecule),
        ("Ising Model", example_ising_model),
        ("Optimization Comparison", example_optimization_comparison),
        ("Excited States", example_excited_states),
        ("Noise Robustness", example_noise_robustness),
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

    parser = argparse.ArgumentParser(description="VQE Examples")
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
            example_simple_vqe,
            example_h2_molecule,
            example_ising_model,
            example_optimization_comparison,
            example_excited_states,
            example_noise_robustness,
        ]
        examples[args.example - 1]()
    else:
        # Run simple example by default
        example_simple_vqe()
