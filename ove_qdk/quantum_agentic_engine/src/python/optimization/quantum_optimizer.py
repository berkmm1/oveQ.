#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Quantum Optimization Algorithms
Variational quantum optimization with classical optimizers
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from scipy.optimize import minimize, differential_evolution, dual_annealing
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizerType(Enum):
    """Types of classical optimizers"""
    COBYLA = auto()
    L_BFGS_B = auto()
    SLSQP = auto()
    POWELL = auto()
    NELDER_MEAD = auto()
    DIFFERENTIAL_EVOLUTION = auto()
    DUAL_ANNEALING = auto()
    ADAM = auto()
    RMSPROP = auto()
    SGD = auto()
    QUANTUM_NATURAL_GRADIENT = auto()


@dataclass
class OptimizationResult:
    """Result of optimization"""
    optimal_parameters: np.ndarray
    optimal_value: float
    num_iterations: int
    num_function_evals: int
    success: bool
    message: str
    runtime: float
    history: List[Tuple[np.ndarray, float]] = field(default_factory=list)
    gradient_history: List[np.ndarray] = field(default_factory=list)


@dataclass
class OptimizerConfig:
    """Configuration for optimizer"""
    optimizer_type: OptimizerType = OptimizerType.COBYLA
    max_iterations: int = 1000
    tolerance: float = 1e-6
    learning_rate: float = 0.01
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8
    use_bounds: bool = False
    bounds: Optional[List[Tuple[float, float]]] = None
    use_gradient: bool = True
    use_quantum_natural_gradient: bool = False
    qng_epsilon: float = 1e-3
    callback_frequency: int = 10


class QuantumObjectiveFunction:
    """
    Wrapper for quantum objective functions
    """

    def __init__(
        self,
        circuit_evaluator: Callable[[np.ndarray], float],
        num_parameters: int,
        use_gradient: bool = True
    ):
        self.circuit_evaluator = circuit_evaluator
        self.num_parameters = num_parameters
        self.use_gradient = use_gradient
        self.eval_count = 0
        self.history: List[Tuple[np.ndarray, float]] = []

    def evaluate(self, parameters: np.ndarray) -> float:
        """Evaluate objective function"""
        self.eval_count += 1
        value = self.circuit_evaluator(parameters)
        self.history.append((parameters.copy(), value))
        return value

    def gradient(self, parameters: np.ndarray, epsilon: float = 1e-5) -> np.ndarray:
        """Compute gradient using finite differences"""
        if not self.use_gradient:
            return np.zeros_like(parameters)

        grad = np.zeros_like(parameters)

        for i in range(len(parameters)):
            params_plus = parameters.copy()
            params_plus[i] += epsilon

            params_minus = parameters.copy()
            params_minus[i] -= epsilon

            grad[i] = (self.evaluate(params_plus) - self.evaluate(params_minus)) / (2 * epsilon)

        return grad

    def quantum_natural_gradient(
        self,
        parameters: np.ndarray,
        epsilon: float = 1e-3
    ) -> np.ndarray:
        """
        Compute quantum natural gradient

        Uses Fubini-Study metric tensor
        """
        # Compute metric tensor (quantum Fisher information)
        metric_tensor = self._compute_metric_tensor(parameters, epsilon)

        # Compute regular gradient
        regular_grad = self.gradient(parameters)

        # Solve for natural gradient: g^{-1} * grad
        try:
            natural_grad = np.linalg.solve(metric_tensor, regular_grad)
        except np.linalg.LinAlgError:
            # If metric tensor is singular, use pseudo-inverse
            natural_grad = np.linalg.lstsq(metric_tensor, regular_grad, rcond=None)[0]

        return natural_grad

    def _compute_metric_tensor(
        self,
        parameters: np.ndarray,
        epsilon: float
    ) -> np.ndarray:
        """Compute quantum Fisher information metric tensor"""
        n = len(parameters)
        metric = np.zeros((n, n))

        # Simplified metric computation
        # In practice, would use quantum circuit to compute overlaps
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    metric[i, i] = 1.0
                else:
                    # Approximate off-diagonal elements
                    metric[i, j] = 0.0
                    metric[j, i] = 0.0

        return metric

    def get_eval_count(self) -> int:
        """Get number of evaluations"""
        return self.eval_count

    def get_history(self) -> List[Tuple[np.ndarray, float]]:
        """Get evaluation history"""
        return self.history

    def reset(self):
        """Reset counters"""
        self.eval_count = 0
        self.history = []


class QuantumOptimizer:
    """
    Quantum optimizer with various classical optimizers
    """

    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()

    def optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray
    ) -> OptimizationResult:
        """
        Run optimization

        Args:
            objective_fn: Objective function to minimize
            initial_parameters: Initial parameter values

        Returns:
            OptimizationResult
        """
        start_time = time.time()

        if self.config.optimizer_type == OptimizerType.COBYLA:
            return self._cobyla_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.L_BFGS_B:
            return self._l_bfgs_b_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.SLSQP:
            return self._slsqp_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.POWELL:
            return self._powell_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.NELDER_MEAD:
            return self._nelder_mead_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.DIFFERENTIAL_EVOLUTION:
            return self._differential_evolution_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.DUAL_ANNEALING:
            return self._dual_annealing_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.ADAM:
            return self._adam_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.RMSPROP:
            return self._rmsprop_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.SGD:
            return self._sgd_optimize(objective_fn, initial_parameters, start_time)
        elif self.config.optimizer_type == OptimizerType.QUANTUM_NATURAL_GRADIENT:
            return self._qng_optimize(objective_fn, initial_parameters, start_time)
        else:
            raise ValueError(f"Unknown optimizer type: {self.config.optimizer_type}")

    def _cobyla_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """COBYLA optimization"""
        history = []

        def callback(x):
            if len(history) % self.config.callback_frequency == 0:
                history.append((x.copy(), objective_fn.evaluate(x)))

        result = minimize(
            objective_fn.evaluate,
            initial_parameters,
            method='COBYLA',
            options={
                'maxiter': self.config.max_iterations,
                'tol': self.config.tolerance
            },
            callback=callback
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=result.message,
            runtime=time.time() - start_time,
            history=history
        )

    def _l_bfgs_b_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """L-BFGS-B optimization"""
        history = []

        def callback(x):
            if len(history) % self.config.callback_frequency == 0:
                history.append((x.copy(), objective_fn.evaluate(x)))

        bounds = self.config.bounds if self.config.use_bounds else None

        result = minimize(
            objective_fn.evaluate,
            initial_parameters,
            method='L-BFGS-B',
            jac=objective_fn.gradient if self.config.use_gradient else None,
            bounds=bounds,
            options={
                'maxiter': self.config.max_iterations,
                'ftol': self.config.tolerance
            },
            callback=callback
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=result.message,
            runtime=time.time() - start_time,
            history=history
        )

    def _slsqp_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """SLSQP optimization"""
        history = []

        def callback(x):
            if len(history) % self.config.callback_frequency == 0:
                history.append((x.copy(), objective_fn.evaluate(x)))

        bounds = self.config.bounds if self.config.use_bounds else None

        result = minimize(
            objective_fn.evaluate,
            initial_parameters,
            method='SLSQP',
            jac=objective_fn.gradient if self.config.use_gradient else None,
            bounds=bounds,
            options={
                'maxiter': self.config.max_iterations,
                'ftol': self.config.tolerance
            },
            callback=callback
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=result.message,
            runtime=time.time() - start_time,
            history=history
        )

    def _powell_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Powell optimization"""
        history = []

        def callback(x):
            if len(history) % self.config.callback_frequency == 0:
                history.append((x.copy(), objective_fn.evaluate(x)))

        result = minimize(
            objective_fn.evaluate,
            initial_parameters,
            method='Powell',
            options={
                'maxiter': self.config.max_iterations,
                'ftol': self.config.tolerance
            },
            callback=callback
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=result.message,
            runtime=time.time() - start_time,
            history=history
        )

    def _nelder_mead_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Nelder-Mead optimization"""
        history = []

        def callback(x):
            if len(history) % self.config.callback_frequency == 0:
                history.append((x.copy(), objective_fn.evaluate(x)))

        result = minimize(
            objective_fn.evaluate,
            initial_parameters,
            method='Nelder-Mead',
            options={
                'maxiter': self.config.max_iterations,
                'xatol': self.config.tolerance,
                'fatol': self.config.tolerance
            },
            callback=callback
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=result.message,
            runtime=time.time() - start_time,
            history=history
        )

    def _differential_evolution_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Differential evolution optimization"""
        if not self.config.bounds:
            # Create default bounds
            bounds = [(-np.pi, np.pi) for _ in range(len(initial_parameters))]
        else:
            bounds = self.config.bounds

        result = differential_evolution(
            objective_fn.evaluate,
            bounds,
            maxiter=self.config.max_iterations,
            tol=self.config.tolerance,
            polish=True,
            init=initial_parameters.reshape(1, -1)
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=str(result.message),
            runtime=time.time() - start_time,
            history=[]
        )

    def _dual_annealing_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Dual annealing optimization"""
        if not self.config.bounds:
            bounds = [(-np.pi, np.pi) for _ in range(len(initial_parameters))]
        else:
            bounds = self.config.bounds

        result = dual_annealing(
            objective_fn.evaluate,
            bounds,
            maxiter=self.config.max_iterations
        )

        return OptimizationResult(
            optimal_parameters=result.x,
            optimal_value=result.fun,
            num_iterations=result.nit,
            num_function_evals=objective_fn.get_eval_count(),
            success=result.success,
            message=str(result.message),
            runtime=time.time() - start_time,
            history=[]
        )

    def _adam_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Adam optimization"""
        params = initial_parameters.copy()
        m = np.zeros_like(params)
        v = np.zeros_like(params)
        history = []
        gradient_history = []

        for t in range(1, self.config.max_iterations + 1):
            # Compute gradient
            grad = objective_fn.gradient(params)
            gradient_history.append(grad.copy())

            # Adam update
            m = self.config.beta1 * m + (1 - self.config.beta1) * grad
            v = self.config.beta2 * v + (1 - self.config.beta2) * (grad ** 2)

            m_hat = m / (1 - self.config.beta1 ** t)
            v_hat = v / (1 - self.config.beta2 ** t)

            params -= self.config.learning_rate * m_hat / (np.sqrt(v_hat) + self.config.epsilon)

            # Record history
            if t % self.config.callback_frequency == 0:
                value = objective_fn.evaluate(params)
                history.append((params.copy(), value))

                # Check convergence
                if len(history) > 1:
                    if abs(history[-1][1] - history[-2][1]) < self.config.tolerance:
                        break

        optimal_value = objective_fn.evaluate(params)

        return OptimizationResult(
            optimal_parameters=params,
            optimal_value=optimal_value,
            num_iterations=t,
            num_function_evals=objective_fn.get_eval_count(),
            success=True,
            message="Adam optimization completed",
            runtime=time.time() - start_time,
            history=history,
            gradient_history=gradient_history
        )

    def _rmsprop_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """RMSprop optimization"""
        params = initial_parameters.copy()
        cache = np.zeros_like(params)
        history = []

        for t in range(1, self.config.max_iterations + 1):
            grad = objective_fn.gradient(params)

            # RMSprop update
            cache = self.config.beta2 * cache + (1 - self.config.beta2) * (grad ** 2)
            params -= self.config.learning_rate * grad / (np.sqrt(cache) + self.config.epsilon)

            if t % self.config.callback_frequency == 0:
                value = objective_fn.evaluate(params)
                history.append((params.copy(), value))

                if len(history) > 1:
                    if abs(history[-1][1] - history[-2][1]) < self.config.tolerance:
                        break

        return OptimizationResult(
            optimal_parameters=params,
            optimal_value=objective_fn.evaluate(params),
            num_iterations=t,
            num_function_evals=objective_fn.get_eval_count(),
            success=True,
            message="RMSprop optimization completed",
            runtime=time.time() - start_time,
            history=history
        )

    def _sgd_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Stochastic gradient descent optimization"""
        params = initial_parameters.copy()
        history = []

        for t in range(1, self.config.max_iterations + 1):
            grad = objective_fn.gradient(params)
            params -= self.config.learning_rate * grad

            if t % self.config.callback_frequency == 0:
                value = objective_fn.evaluate(params)
                history.append((params.copy(), value))

                if len(history) > 1:
                    if abs(history[-1][1] - history[-2][1]) < self.config.tolerance:
                        break

        return OptimizationResult(
            optimal_parameters=params,
            optimal_value=objective_fn.evaluate(params),
            num_iterations=t,
            num_function_evals=objective_fn.get_eval_count(),
            success=True,
            message="SGD optimization completed",
            runtime=time.time() - start_time,
            history=history
        )

    def _qng_optimize(
        self,
        objective_fn: QuantumObjectiveFunction,
        initial_parameters: np.ndarray,
        start_time: float
    ) -> OptimizationResult:
        """Quantum natural gradient optimization"""
        params = initial_parameters.copy()
        history = []
        gradient_history = []

        for t in range(1, self.config.max_iterations + 1):
            # Compute quantum natural gradient
            qng = objective_fn.quantum_natural_gradient(params, self.config.qng_epsilon)
            gradient_history.append(qng.copy())

            # Update parameters
            params -= self.config.learning_rate * qng

            if t % self.config.callback_frequency == 0:
                value = objective_fn.evaluate(params)
                history.append((params.copy(), value))

                if len(history) > 1:
                    if abs(history[-1][1] - history[-2][1]) < self.config.tolerance:
                        break

        return OptimizationResult(
            optimal_parameters=params,
            optimal_value=objective_fn.evaluate(params),
            num_iterations=t,
            num_function_evals=objective_fn.get_eval_count(),
            success=True,
            message="QNG optimization completed",
            runtime=time.time() - start_time,
            history=history,
            gradient_history=gradient_history
        )


class VQE:
    """
    Variational Quantum Eigensolver
    """

    def __init__(
        self,
        hamiltonian: np.ndarray,
        ansatz: Callable[[np.ndarray], np.ndarray],
        num_parameters: int,
        optimizer_config: Optional[OptimizerConfig] = None
    ):
        self.hamiltonian = hamiltonian
        self.ansatz = ansatz
        self.num_parameters = num_parameters
        self.optimizer = QuantumOptimizer(optimizer_config or OptimizerConfig())

    def expectation_value(self, parameters: np.ndarray) -> float:
        """Compute expectation value of Hamiltonian"""
        state = self.ansatz(parameters)
        return np.real(np.vdot(state, self.hamiltonian @ state))

    def find_ground_state(
        self,
        initial_parameters: Optional[np.ndarray] = None
    ) -> OptimizationResult:
        """Find ground state energy"""
        if initial_parameters is None:
            initial_parameters = np.random.randn(self.num_parameters) * 0.1

        objective_fn = QuantumObjectiveFunction(
            self.expectation_value,
            self.num_parameters,
            use_gradient=True
        )

        return self.optimizer.optimize(objective_fn, initial_parameters)


class QAOA:
    """
    Quantum Approximate Optimization Algorithm
    """

    def __init__(
        self,
        cost_hamiltonian: np.ndarray,
        mixer_hamiltonian: np.ndarray,
        num_qubits: int,
        num_layers: int = 2,
        optimizer_config: Optional[OptimizerConfig] = None
    ):
        self.cost_hamiltonian = cost_hamiltonian
        self.mixer_hamiltonian = mixer_hamiltonian
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self.optimizer = QuantumOptimizer(optimizer_config or OptimizerConfig())

    def cost_function(self, parameters: np.ndarray) -> float:
        """Compute QAOA cost function"""
        # Parameters alternate between gamma and beta
        gammas = parameters[::2]
        betas = parameters[1::2]

        # Apply QAOA circuit (simplified)
        # In practice, would use actual quantum circuit
        state = np.ones(2 ** self.num_qubits) / np.sqrt(2 ** self.num_qubits)

        for gamma, beta in zip(gammas, betas):
            # Apply cost Hamiltonian
            cost_unitary = self._unitary_from_hamiltonian(self.cost_hamiltonian, gamma)
            state = cost_unitary @ state

            # Apply mixer Hamiltonian
            mixer_unitary = self._unitary_from_hamiltonian(self.mixer_hamiltonian, beta)
            state = mixer_unitary @ state

        # Compute expectation value
        return np.real(np.vdot(state, self.cost_hamiltonian @ state))

    def _unitary_from_hamiltonian(self, hamiltonian: np.ndarray, time: float) -> np.ndarray:
        """Compute unitary from Hamiltonian"""
        eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
        return eigenvectors @ np.diag(np.exp(-1j * eigenvalues * time)) @ eigenvectors.conj().T

    def optimize(self, initial_parameters: Optional[np.ndarray] = None) -> OptimizationResult:
        """Run QAOA optimization"""
        if initial_parameters is None:
            initial_parameters = np.random.uniform(0, 2*np.pi, 2 * self.num_layers)

        objective_fn = QuantumObjectiveFunction(
            self.cost_function,
            len(initial_parameters),
            use_gradient=True
        )

        return self.optimizer.optimize(objective_fn, initial_parameters)


# Example usage
if __name__ == "__main__":
    print("Testing Quantum Optimizer...")

    # Create simple test function
    def test_function(params: np.ndarray) -> float:
        """Simple quadratic function"""
        return np.sum(params ** 2)

    # Test different optimizers
    optimizers = [
        OptimizerType.COBYLA,
        OptimizerType.ADAM,
        OptimizerType.SGD
    ]

    initial_params = np.array([1.0, 2.0, 3.0])

    for opt_type in optimizers:
        print(f"\n=== {opt_type.name} ===")

        config = OptimizerConfig(
            optimizer_type=opt_type,
            max_iterations=100,
            learning_rate=0.1
        )

        optimizer = QuantumOptimizer(config)
        objective_fn = QuantumObjectiveFunction(test_function, len(initial_params))

        result = optimizer.optimize(objective_fn, initial_params.copy())

        print(f"Optimal value: {result.optimal_value:.6f}")
        print(f"Optimal parameters: {result.optimal_parameters}")
        print(f"Iterations: {result.num_iterations}")
        print(f"Runtime: {result.runtime:.4f}s")

    # Test VQE
    print("\n=== VQE Test ===")

    # Simple Hamiltonian: Z ⊗ Z
    hamiltonian = np.diag([1, -1, -1, 1])

    def ansatz(params: np.ndarray) -> np.ndarray:
        """Simple ansatz"""
        state = np.array([1, 0, 0, 0], dtype=complex)
        # Apply rotation
        rotation = np.array([
            [np.cos(params[0]), -np.sin(params[0])],
            [np.sin(params[0]), np.cos(params[0])]
        ])
        return state

    vqe = VQE(hamiltonian, ansatz, num_parameters=1)
    result = vqe.find_ground_state()

    print(f"Ground state energy: {result.optimal_value:.4f}")
    print(f"Optimal parameters: {result.optimal_parameters}")
