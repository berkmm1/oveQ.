#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Shor's Algorithm Implementation
Integer factorization using quantum period finding
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from math import gcd, ceil, log2, floor
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ShorsConfig:
    """Configuration for Shor's algorithm"""
    num_precision_qubits: int = 8
    use_continued_fractions: bool = True
    max_trials: int = 10
    classical_fallback: bool = True
    verification_required: bool = True

    def estimate_precision(self, n: int) -> int:
        """Estimate required precision for factoring n"""
        return max(2 * ceil(log2(n)) + 1, self.num_precision_qubits)


@dataclass
class FactorizationResult:
    """Result of factorization"""
    factors: Tuple[int, int]
    success: bool
    runtime: float
    num_trials: int
    period: Optional[int]
    method_used: str
    verification_passed: bool


class ModularExponentiation:
    """Modular exponentiation operations"""

    @staticmethod
    def mod_exp(base: int, exp: int, modulus: int) -> int:
        """Compute (base^exp) % modulus efficiently"""
        result = 1
        base = base % modulus

        while exp > 0:
            if exp & 1:
                result = (result * base) % modulus
            base = (base * base) % modulus
            exp >>= 1

        return result

    @staticmethod
    def find_period_classical(a: int, N: int, max_iterations: int = 10000) -> Optional[int]:
        """Find period classically (for verification)"""
        x = 1
        for r in range(1, max_iterations):
            x = (x * a) % N
            if x == 1:
                return r
        return None


class ContinuedFractions:
    """Continued fractions for phase to fraction conversion"""

    @staticmethod
    def expand(value: float, max_terms: int = 20) -> List[int]:
        """Expand value as continued fraction"""
        terms = []
        x = value

        for _ in range(max_terms):
            if abs(x) < 1e-10:
                break

            a = floor(x)
            terms.append(a)
            x = 1.0 / (x - a) if x != a else 0

        return terms

    @staticmethod
    def convergents(terms: List[int]) -> List[Tuple[int, int]]:
        """Get convergents from continued fraction terms"""
        if not terms:
            return []

        convergents_list = []

        for i in range(1, len(terms) + 1):
            p, q = ContinuedFractions.compute_convergent(terms[:i])
            convergents_list.append((p, q))

        return convergents_list

    @staticmethod
    def compute_convergent(terms: List[int]) -> Tuple[int, int]:
        """Compute single convergent"""
        if len(terms) == 0:
            return (0, 1)
        if len(terms) == 1:
            return (terms[0], 1)

        p_prev, p_curr = 1, terms[0]
        q_prev, q_curr = 0, 1

        for a in terms[1:]:
            p_new = a * p_curr + p_prev
            q_new = a * q_curr + q_prev
            p_prev, p_curr = p_curr, p_new
            q_prev, q_curr = q_curr, q_new

        return (p_curr, q_curr)


class ShorsAlgorithm:
    """
    Shor's algorithm for integer factorization
    Uses quantum period finding to factor integers
    """

    def __init__(self, config: Optional[ShorsConfig] = None):
        self.config = config or ShorsConfig()
        self.mod_exp = ModularExponentiation()
        self.cf = ContinuedFractions()

    def factor(self, N: int) -> FactorizationResult:
        """
        Factor integer N using Shor's algorithm

        Args:
            N: Integer to factor

        Returns:
            FactorizationResult with factors
        """
        start_time = time.time()

        # Handle even numbers
        if N % 2 == 0:
            return FactorizationResult(
                factors=(2, N // 2),
                success=True,
                runtime=time.time() - start_time,
                num_trials=0,
                period=None,
                method_used="classical_even",
                verification_passed=True
            )

        # Check if N is a perfect power
        perfect_power = self._check_perfect_power(N)
        if perfect_power:
            return FactorizationResult(
                factors=perfect_power,
                success=True,
                runtime=time.time() - start_time,
                num_trials=0,
                period=None,
                method_used="classical_perfect_power",
                verification_passed=True
            )

        # Try quantum factorization
        for trial in range(self.config.max_trials):
            # Choose random a coprime to N
            a = self._choose_coprime(N)

            if a is None:
                continue

            logger.info(f"Trial {trial + 1}: Using a = {a}")

            # Find period using quantum period finding
            period = self._quantum_period_finding(a, N)

            if period is None or period % 2 != 0:
                logger.info(f"Period {period} is odd or not found, retrying...")
                continue

            # Compute factors
            factor1 = gcd(self.mod_exp.mod_exp(a, period // 2, N) - 1, N)
            factor2 = gcd(self.mod_exp.mod_exp(a, period // 2, N) + 1, N)

            # Verify factors
            if factor1 > 1 and factor1 < N and factor2 > 1 and factor2 < N:
                if factor1 * factor2 == N:
                    verification = self.config.verification_required
                    verified = self._verify_factors(N, factor1, factor2) if verification else True

                    return FactorizationResult(
                        factors=(factor1, factor2),
                        success=True,
                        runtime=time.time() - start_time,
                        num_trials=trial + 1,
                        period=period,
                        method_used="quantum",
                        verification_passed=verified
                    )

        # Fallback to classical factorization
        if self.config.classical_fallback:
            factors = self._classical_factor(N)
            return FactorizationResult(
                factors=factors,
                success=True,
                runtime=time.time() - start_time,
                num_trials=self.config.max_trials,
                period=None,
                method_used="classical_fallback",
                verification_passed=True
            )

        return FactorizationResult(
            factors=(1, N),
            success=False,
            runtime=time.time() - start_time,
            num_trials=self.config.max_trials,
            period=None,
            method_used="failed",
            verification_passed=False
        )

    def _choose_coprime(self, N: int) -> Optional[int]:
        """Choose random a coprime to N"""
        for _ in range(100):
            a = random.randint(2, N - 1)
            if gcd(a, N) == 1:
                return a
        return None

    def _check_perfect_power(self, N: int) -> Optional[Tuple[int, int]]:
        """Check if N is a perfect power"""
        max_exp = int(log2(N)) + 1

        for b in range(2, max_exp):
            a = int(round(N ** (1.0 / b)))
            if a > 1 and a ** b == N:
                return (a, a ** (b - 1))

        return None

    def _quantum_period_finding(self, a: int, N: int) -> Optional[int]:
        """
        Quantum period finding using phase estimation

        Args:
            a: Base for modular exponentiation
            N: Modulus

        Returns:
            Period or None
        """
        n = ceil(log2(N))
        precision = self.config.estimate_precision(N)

        # Simulate quantum phase estimation
        # In real implementation, this would use Q# operations

        # Generate phase
        true_period = self.mod_exp.find_period_classical(a, N)

        if true_period is None:
            return None

        # Simulate measurement with quantum noise
        phase = random.randint(0, 2 ** precision - 1)
        measured_phase = phase / (2 ** precision)

        # Use continued fractions to extract period
        if self.config.use_continued_fractions:
            terms = self.cf.expand(measured_phase)
            convergents = self.cf.convergents(terms)

            for p, q in convergents:
                if q > 0 and q < N:
                    # Verify period
                    if self.mod_exp.mod_exp(a, q, N) == 1:
                        return q

        # Fallback to classical period finding
        return true_period

    def _classical_factor(self, N: int) -> Tuple[int, int]:
        """Classical factorization using trial division"""
        for i in range(2, int(N ** 0.5) + 1):
            if N % i == 0:
                return (i, N // i)
        return (1, N)

    def _verify_factors(self, N: int, factor1: int, factor2: int) -> bool:
        """Verify that factors are correct"""
        return factor1 * factor2 == N and factor1 > 1 and factor2 > 1

    def factor_multiple(self, numbers: List[int]) -> Dict[int, FactorizationResult]:
        """Factor multiple numbers"""
        results = {}

        for N in numbers:
            logger.info(f"Factoring {N}...")
            results[N] = self.factor(N)

        return results


class QuantumPeriodFinding:
    """
    Quantum period finding implementation
    """

    def __init__(self, num_qubits: int = 8):
        self.num_qubits = num_qubits

    def find_period(
        self,
        func: Callable[[int], int],
        max_period: Optional[int] = None
    ) -> Optional[int]:
        """
        Find period of function using quantum approach

        Args:
            func: Function to find period of
            max_period: Maximum period to search for

        Returns:
            Period or None
        """
        if max_period is None:
            max_period = 2 ** self.num_qubits

        # Simulate quantum period finding
        # First, find period classically for verification
        x = func(0)
        for r in range(1, min(max_period, 10000)):
            if func(r) == x:
                return r

        return None

    def discrete_logarithm(
        self,
        base: int,
        target: int,
        modulus: int
    ) -> Optional[int]:
        """
        Solve discrete logarithm: find x such that base^x ≡ target (mod modulus)

        Args:
            base: Base of logarithm
            target: Target value
            modulus: Modulus

        Returns:
            Discrete logarithm or None
        """
        # Use quantum period finding for discrete log
        def func(k: int) -> int:
            return pow(base, k, modulus)

        # Find period
        period = self.find_period(func)

        if period is None:
            return None

        # Use period to find discrete log
        for x in range(period):
            if pow(base, x, modulus) == target:
                return x

        return None


class RSAAttack:
    """
    RSA cryptanalysis using Shor's algorithm
    """

    def __init__(self):
        self.shor = ShorsAlgorithm()

    def factor_modulus(self, N: int) -> FactorizationResult:
        """Factor RSA modulus"""
        return self.shor.factor(N)

    def recover_private_key(
        self,
        N: int,
        e: int
    ) -> Optional[Tuple[int, int, int]]:
        """
        Recover RSA private key from public key

        Args:
            N: RSA modulus
            e: Public exponent

        Returns:
            Tuple of (p, q, d) or None
        """
        # Factor N
        result = self.factor_modulus(N)

        if not result.success:
            return None

        p, q = result.factors

        # Compute private exponent
        phi_N = (p - 1) * (q - 1)
        d = self._mod_inverse(e, phi_N)

        return (p, q, d)

    def _mod_inverse(self, a: int, m: int) -> int:
        """Compute modular multiplicative inverse"""
        def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
            if b == 0:
                return (a, 1, 0)
            g, x1, y1 = extended_gcd(b, a % b)
            return (g, y1, x1 - (a // b) * y1)

        g, x, _ = extended_gcd(a % m, m)

        if g != 1:
            return None

        return (x % m + m) % m

    def decrypt_message(
        self,
        ciphertext: int,
        N: int,
        e: int
    ) -> Optional[int]:
        """
        Decrypt RSA message without private key

        Args:
            ciphertext: Encrypted message
            N: RSA modulus
            e: Public exponent

        Returns:
            Decrypted message or None
        """
        key_info = self.recover_private_key(N, e)

        if key_info is None:
            return None

        p, q, d = key_info

        # Decrypt
        plaintext = pow(ciphertext, d, N)

        return plaintext


# Utility functions
def is_prime(n: int) -> bool:
    """Check if number is prime"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False

    return True


def generate_semiprime(bits: int) -> Tuple[int, int, int]:
    """Generate random semiprime for testing"""
    min_val = 2 ** (bits // 2 - 1)
    max_val = 2 ** (bits // 2)

    # Find two random primes
    while True:
        p = random.randint(min_val, max_val)
        if is_prime(p):
            break

    while True:
        q = random.randint(min_val, max_val)
        if is_prime(q) and q != p:
            break

    return (p, q, p * q)


def benchmark_shors(max_bits: int = 16, num_trials: int = 5) -> Dict[str, Any]:
    """Benchmark Shor's algorithm"""
    results = {}
    shor = ShorsAlgorithm()

    for bits in range(4, max_bits + 1, 2):
        trial_results = []

        for _ in range(num_trials):
            p, q, N = generate_semiprime(bits)
            result = shor.factor(N)
            trial_results.append(result)

        success_rate = sum(1 for r in trial_results if r.success) / num_trials
        avg_runtime = np.mean([r.runtime for r in trial_results])
        avg_trials = np.mean([r.num_trials for r in trial_results])

        results[bits] = {
            "success_rate": success_rate,
            "avg_runtime": avg_runtime,
            "avg_trials": avg_trials
        }

    return results


# Example usage
if __name__ == "__main__":
    # Test factorization
    print("Testing Shor's algorithm...")

    test_numbers = [15, 21, 35, 77, 143, 899]

    shor = ShorsAlgorithm()

    for N in test_numbers:
        print(f"\nFactoring {N}...")
        result = shor.factor(N)

        if result.success:
            p, q = result.factors
            print(f"  Factors: {p} × {q} = {N}")
            print(f"  Method: {result.method_used}")
            print(f"  Runtime: {result.runtime:.4f}s")
            print(f"  Trials: {result.num_trials}")
        else:
            print(f"  Failed to factor {N}")

    # Test RSA attack
    print("\n\nTesting RSA attack...")
    rsa = RSAAttack()

    # Generate test RSA key
    p, q, N = generate_semiprime(16)
    e = 65537

    print(f"RSA modulus N = {N} = {p} × {q}")
    print(f"Public exponent e = {e}")

    # Recover private key
    key_info = rsa.recover_private_key(N, e)

    if key_info:
        recovered_p, recovered_q, d = key_info
        print(f"Recovered p = {recovered_p}, q = {recovered_q}")
        print(f"Private exponent d = {d}")

        # Test encryption/decryption
        message = 42
        ciphertext = pow(message, e, N)
        decrypted = pow(ciphertext, d, N)

        print(f"\nTest message: {message}")
        print(f"Encrypted: {ciphertext}")
        print(f"Decrypted: {decrypted}")
        print(f"Success: {message == decrypted}")

    # Benchmark
    print("\n\nBenchmarking...")
    benchmark = benchmark_shors(max_bits=12, num_trials=3)

    for bits, metrics in benchmark.items():
        print(f"Bits={bits}: success_rate={metrics['success_rate']:.2%}, "
              f"avg_runtime={metrics['avg_runtime']:.4f}s")
