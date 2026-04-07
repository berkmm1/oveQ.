#!/usr/bin/env python3
"""
Quantum Agentic Loop Engine - Quantum Visualization
Visualization tools for quantum states, circuits, and results
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumStateVisualizer:
    """Visualize quantum states"""

    @staticmethod
    def state_to_string(state: np.ndarray, precision: int = 4) -> str:
        """Convert state vector to readable string"""
        if state.ndim == 1:
            n_qubits = int(np.log2(len(state)))
            terms = []

            for i, amplitude in enumerate(state):
                if np.abs(amplitude) > 1e-10:
                    binary = format(i, f'0{n_qubits}b')
                    amp_str = f"{amplitude:.{precision}f}"
                    terms.append(f"{amp_str}|{binary}⟩")

            return " + ".join(terms) if terms else "0"
        else:
            return f"Density matrix {state.shape}"

    @staticmethod
    def bloch_vector(state: np.ndarray) -> Tuple[float, float, float]:
        """Compute Bloch vector for single qubit state"""
        if len(state) != 2:
            raise ValueError("Bloch vector only defined for single qubit")

        # Density matrix
        if state.ndim == 1:
            rho = np.outer(state, state.conj())
        else:
            rho = state

        # Pauli matrices
        sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

        # Expectation values
        x = np.real(np.trace(rho @ sigma_x))
        y = np.real(np.trace(rho @ sigma_y))
        z = np.real(np.trace(rho @ sigma_z))

        return (x, y, z)

    @staticmethod
    def bloch_coordinates_to_string(coords: Tuple[float, float, float], precision: int = 4) -> str:
        """Convert Bloch coordinates to string"""
        x, y, z = coords
        return f"(x={x:.{precision}f}, y={y:.{precision}f}, z={z:.{precision}f})"

    @staticmethod
    def probability_distribution(state: np.ndarray) -> Dict[str, float]:
        """Get probability distribution over computational basis"""
        if state.ndim == 1:
            probs = np.abs(state) ** 2
        else:
            probs = np.real(np.diag(state))

        n_qubits = int(np.log2(len(probs)))

        distribution = {}
        for i, prob in enumerate(probs):
            if prob > 1e-10:
                binary = format(i, f'0{n_qubits}b')
                distribution[binary] = prob

        return distribution

    @staticmethod
    def format_probability_distribution(
        distribution: Dict[str, float],
        top_k: Optional[int] = None
    ) -> str:
        """Format probability distribution as string"""
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)

        if top_k:
            sorted_items = sorted_items[:top_k]

        lines = []
        for state, prob in sorted_items:
            bar = "█" * int(prob * 50)
            lines.append(f"|{state}⟩: {prob:.4f} {bar}")

        return "\n".join(lines)


class CircuitVisualizer:
    """Visualize quantum circuits"""

    GATE_SYMBOLS = {
        'X': 'X',
        'Y': 'Y',
        'Z': 'Z',
        'H': 'H',
        'S': 'S',
        'T': 'T',
        'RX': 'Rx',
        'RY': 'Ry',
        'RZ': 'Rz',
        'CNOT': '●─⊕',
        'CZ': '●─Z',
        'SWAP': '×─×',
        'MEASURE': 'M'
    }

    @staticmethod
    def circuit_to_ascii(circuit: List[Dict[str, Any]], num_qubits: int) -> str:
        """Convert circuit to ASCII art"""
        lines = [f"q{i}: ─" for i in range(num_qubits)]

        for gate in circuit:
            gate_type = gate.get('type', 'UNKNOWN')
            targets = gate.get('targets', [])
            controls = gate.get('controls', [])

            # Find positions
            max_pos = max(targets + controls) if targets or controls else 0

            # Add gate symbols
            if controls:
                # Controlled gate
                for c in controls:
                    lines[c] += "●─"
                for t in targets:
                    symbol = CircuitVisualizer.GATE_SYMBOLS.get(gate_type, '?')
                    lines[t] += symbol[-1] + '─'
            else:
                # Single qubit gate
                for t in targets:
                    symbol = CircuitVisualizer.GATE_SYMBOLS.get(gate_type, '?')
                    lines[t] += symbol + '─'

            # Extend other lines
            for i in range(num_qubits):
                if i not in targets and i not in controls:
                    lines[i] += '──'

        return "\n".join(line + '─' for line in lines)

    @staticmethod
    def circuit_statistics(circuit: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get circuit statistics"""
        stats = {
            'total_gates': len(circuit),
            'single_qubit_gates': 0,
            'two_qubit_gates': 0,
            'multi_qubit_gates': 0,
            'gate_types': {}
        }

        for gate in circuit:
            gate_type = gate.get('type', 'UNKNOWN')
            targets = gate.get('targets', [])
            controls = gate.get('controls', [])

            # Count gate types
            stats['gate_types'][gate_type] = stats['gate_types'].get(gate_type, 0) + 1

            # Count by number of qubits
            num_qubits = len(targets) + len(controls)
            if num_qubits == 1:
                stats['single_qubit_gates'] += 1
            elif num_qubits == 2:
                stats['two_qubit_gates'] += 1
            else:
                stats['multi_qubit_gates'] += 1

        return stats

    @staticmethod
    def format_circuit_statistics(stats: Dict[str, Any]) -> str:
        """Format circuit statistics as string"""
        lines = [
            "Circuit Statistics:",
            f"  Total gates: {stats['total_gates']}",
            f"  Single-qubit gates: {stats['single_qubit_gates']}",
            f"  Two-qubit gates: {stats['two_qubit_gates']}",
            f"  Multi-qubit gates: {stats['multi_qubit_gates']}",
            "",
            "Gate types:"
        ]

        for gate_type, count in sorted(stats['gate_types'].items()):
            lines.append(f"  {gate_type}: {count}")

        return "\n".join(lines)


class MetricsVisualizer:
    """Visualize quantum metrics"""

    @staticmethod
    def convergence_history(history: List[Tuple[int, float]], width: int = 60, height: int = 10) -> str:
        """Plot convergence history as ASCII"""
        if not history:
            return "No history data"

        iterations = [h[0] for h in history]
        values = [h[1] for h in history]

        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val if max_val != min_val else 1

        # Create grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]

        # Plot points
        for i, (iter_num, val) in enumerate(history):
            x = int((iter_num - iterations[0]) / (iterations[-1] - iterations[0]) * (width - 1))
            y = height - 1 - int((val - min_val) / val_range * (height - 1))

            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = '*'

        # Add axes
        lines = []
        for row in grid:
            lines.append('│' + ''.join(row))

        lines.append('└' + '─' * width)
        lines.append(f"  Iterations: {iterations[0]} to {iterations[-1]}")
        lines.append(f"  Values: {min_val:.4f} to {max_val:.4f}")

        return "\n".join(lines)

    @staticmethod
    def bar_chart(data: Dict[str, float], width: int = 50) -> str:
        """Create ASCII bar chart"""
        if not data:
            return "No data"

        max_val = max(data.values())
        max_label_len = max(len(str(k)) for k in data.keys())

        lines = []
        for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            bar_len = int(value / max_val * width) if max_val > 0 else 0
            bar = '█' * bar_len
            lines.append(f"{str(label):>{max_label_len}}: {bar} {value:.4f}")

        return "\n".join(lines)

    @staticmethod
    def heatmap(matrix: np.ndarray, width: int = 40, height: int = 20) -> str:
        """Create ASCII heatmap"""
        if matrix.size == 0:
            return "Empty matrix"

        # Normalize to 0-1
        min_val = np.min(matrix)
        max_val = np.max(matrix)
        normalized = (matrix - min_val) / (max_val - min_val) if max_val != min_val else matrix

        # Resize if needed
        if matrix.shape[0] > height or matrix.shape[1] > width:
            # Simple downsampling
            row_step = max(1, matrix.shape[0] // height)
            col_step = max(1, matrix.shape[1] // width)
            normalized = normalized[::row_step, ::col_step]

        # Characters for different intensities
        chars = ' ░▒▓█'

        lines = []
        for row in normalized:
            line = ''
            for val in row:
                idx = int(val * (len(chars) - 1))
                line += chars[idx]
            lines.append(line)

        lines.append(f"\nRange: [{min_val:.4f}, {max_val:.4f}]")

        return "\n".join(lines)


class ResultVisualizer:
    """Visualize quantum computation results"""

    @staticmethod
    def measurement_histogram(counts: Dict[str, int], width: int = 50) -> str:
        """Create histogram of measurement results"""
        if not counts:
            return "No measurement data"

        total = sum(counts.values())
        max_count = max(counts.values())
        max_label_len = max(len(str(k)) for k in counts.keys())

        lines = ["Measurement Results:", f"Total shots: {total}", ""]

        for state, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            prob = count / total
            bar_len = int(count / max_count * width)
            bar = '█' * bar_len
            lines.append(f"|{state:>{max_label_len}}⟩: {bar} {count} ({prob:.2%})")

        return "\n".join(lines)

    @staticmethod
    def comparison_table(
        results: Dict[str, Dict[str, float]],
        metrics: List[str]
    ) -> str:
        """Create comparison table"""
        if not results:
            return "No results"

        # Find column widths
        name_width = max(len(str(k)) for k in results.keys())
        metric_widths = {m: max(len(m), max(len(f"{r.get(m, 0):.4f}") for r in results.values())) for m in metrics}

        # Header
        header = f"{'Method':>{name_width}}"
        for m in metrics:
            header += f" | {m:^{metric_widths[m]}}"

        separator = "-" * len(header)

        lines = [header, separator]

        # Data rows
        for name, data in results.items():
            row = f"{name:>{name_width}}"
            for m in metrics:
                val = data.get(m, 0)
                row += f" | {val:>{metric_widths[m]}.4f}"
            lines.append(row)

        return "\n".join(lines)

    @staticmethod
    def summary_report(
        circuit_stats: Dict[str, Any],
        execution_time: float,
        success_rate: float,
        metrics: Optional[Dict[str, float]] = None
    ) -> str:
        """Generate summary report"""
        lines = [
            "=" * 60,
            "QUANTUM EXECUTION SUMMARY",
            "=" * 60,
            "",
            "Circuit Information:",
            f"  Total gates: {circuit_stats.get('total_gates', 'N/A')}",
            f"  Single-qubit gates: {circuit_stats.get('single_qubit_gates', 'N/A')}",
            f"  Two-qubit gates: {circuit_stats.get('two_qubit_gates', 'N/A')}",
            "",
            "Execution Results:",
            f"  Execution time: {execution_time:.4f}s",
            f"  Success rate: {success_rate:.2%}",
        ]

        if metrics:
            lines.extend(["", "Metrics:"])
            for name, value in metrics.items():
                lines.append(f"  {name}: {value:.6f}")

        lines.extend(["", "=" * 60])

        return "\n".join(lines)


class StateEvolutionVisualizer:
    """Visualize quantum state evolution"""

    @staticmethod
    def state_trajectory(states: List[np.ndarray], width: int = 60, height: int = 10) -> str:
        """Visualize trajectory of quantum states"""
        if len(states) < 2:
            return "Need at least 2 states"

        # Compute fidelities between consecutive states
        fidelities = []
        for i in range(len(states) - 1):
            if states[i].ndim == 1 and states[i+1].ndim == 1:
                fid = np.abs(np.vdot(states[i], states[i+1])) ** 2
            else:
                # For mixed states
                fid = np.real(np.trace(states[i] @ states[i+1]))
            fidelities.append(fid)

        # Plot
        return MetricsVisualizer.convergence_history(
            list(enumerate(fidelities)),
            width, height
        )

    @staticmethod
    def entanglement_growth(entanglement_entropies: List[float], width: int = 60) -> str:
        """Visualize growth of entanglement entropy"""
        if not entanglement_entropies:
            return "No entanglement data"

        history = [(i, s) for i, s in enumerate(entanglement_entropies)]
        return MetricsVisualizer.convergence_history(history, width)


# Example usage
if __name__ == "__main__":
    print("Testing Quantum Visualization...")

    # Test state visualization
    print("\n=== State Visualization ===")

    bell_state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)
    print(f"Bell state: {QuantumStateVisualizer.state_to_string(bell_state)}")

    bloch = QuantumStateVisualizer.bloch_vector(np.array([1, 0], dtype=complex))
    print(f"|0⟩ Bloch vector: {QuantumStateVisualizer.bloch_coordinates_to_string(bloch)}")

    probs = QuantumStateVisualizer.probability_distribution(bell_state)
    print(f"\nProbability distribution:\n{QuantumStateVisualizer.format_probability_distribution(probs)}")

    # Test circuit visualization
    print("\n=== Circuit Visualization ===")

    circuit = [
        {'type': 'H', 'targets': [0]},
        {'type': 'CNOT', 'targets': [1], 'controls': [0]},
        {'type': 'RZ', 'targets': [0]},
        {'type': 'CNOT', 'targets': [1], 'controls': [0]},
    ]

    print(CircuitVisualizer.circuit_to_ascii(circuit, num_qubits=2))

    stats = CircuitVisualizer.circuit_statistics(circuit)
    print(f"\n{CircuitVisualizer.format_circuit_statistics(stats)}")

    # Test metrics visualization
    print("\n=== Metrics Visualization ===")

    history = [(i, 1.0 / (i + 1)) for i in range(20)]
    print("Convergence history:")
    print(MetricsVisualizer.convergence_history(history, width=40, height=8))

    data = {'X': 0.8, 'Y': 0.6, 'Z': 0.9, 'H': 0.7}
    print(f"\nBar chart:\n{MetricsVisualizer.bar_chart(data)}")

    # Test result visualization
    print("\n=== Result Visualization ===")

    counts = {'00': 450, '11': 480, '01': 35, '10': 35}
    print(ResultVisualizer.measurement_histogram(counts, width=30))

    results = {
        'VQE': {'energy': -1.234, 'fidelity': 0.95},
        'QAOA': {'energy': -1.123, 'fidelity': 0.89},
        'Exact': {'energy': -1.345, 'fidelity': 1.0}
    }
    print(f"\n{ResultVisualizer.comparison_table(results, ['energy', 'fidelity'])}")

    # Summary report
    print("\n=== Summary Report ===")
    print(ResultVisualizer.summary_report(
        circuit_stats={'total_gates': 10, 'single_qubit_gates': 6, 'two_qubit_gates': 4},
        execution_time=0.1234,
        success_rate=0.95,
        metrics={'final_energy': -1.234, 'convergence': 0.001}
    ))
