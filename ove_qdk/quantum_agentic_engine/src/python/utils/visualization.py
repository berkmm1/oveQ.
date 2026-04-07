#!/usr/bin/env python3
"""
Visualization Utilities for Quantum Agentic Engine
Advanced plotting and visualization tools
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import seaborn as sns
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Set default style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


class QuantumStateVisualizer:
    """Visualize quantum states and operations"""

    @staticmethod
    def plot_bloch_sphere(
        state_vector: np.ndarray,
        title: str = "Bloch Sphere",
        save_path: Optional[str] = None
    ):
        """
        Plot state on Bloch sphere

        Args:
            state_vector: 2-element complex vector [α, β]
            title: Plot title
            save_path: Path to save figure
        """
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Draw sphere
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x = np.outer(np.cos(u), np.sin(v))
        y = np.outer(np.sin(u), np.sin(v))
        z = np.outer(np.ones(np.size(u)), np.cos(v))

        ax.plot_surface(x, y, z, alpha=0.1, color='blue')

        # Draw axes
        ax.plot([-1, 1], [0, 0], [0, 0], 'k-', linewidth=1)
        ax.plot([0, 0], [-1, 1], [0, 0], 'k-', linewidth=1)
        ax.plot([0, 0], [0, 0], [-1, 1], 'k-', linewidth=1)

        # Labels
        ax.text(1.2, 0, 0, '|+⟩', fontsize=12)
        ax.text(-1.2, 0, 0, '|-⟩', fontsize=12)
        ax.text(0, 1.2, 0, '|+i⟩', fontsize=12)
        ax.text(0, -1.2, 0, '|-i⟩', fontsize=12)
        ax.text(0, 0, 1.2, '|0⟩', fontsize=12)
        ax.text(0, 0, -1.2, '|1⟩', fontsize=12)

        # Convert state to Bloch coordinates
        alpha, beta = state_vector[0], state_vector[1]

        # Bloch coordinates
        x_bloch = 2 * np.real(np.conj(alpha) * beta)
        y_bloch = 2 * np.imag(np.conj(alpha) * beta)
        z_bloch = np.abs(alpha)**2 - np.abs(beta)**2

        # Plot state vector
        ax.quiver(0, 0, 0, x_bloch, y_bloch, z_bloch,
                 length=1.0, normalize=True, color='red',
                 arrow_length_ratio=0.1, linewidth=3)

        # Plot point
        ax.scatter([x_bloch], [y_bloch], [z_bloch],
                  color='red', s=100, marker='o')

        ax.set_xlim([-1.2, 1.2])
        ax.set_ylim([-1.2, 1.2])
        ax.set_zlim([-1.2, 1.2])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(title)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_state_evolution(
        states: List[np.ndarray],
        times: Optional[List[float]] = None,
        title: str = "State Evolution",
        save_path: Optional[str] = None
    ):
        """Plot evolution of quantum state over time"""
        if times is None:
            times = list(range(len(states)))

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Extract amplitudes
        amplitudes = np.array([np.abs(s)**2 for s in states])
        phases = np.array([np.angle(s) for s in states])

        # Plot probability amplitudes
        ax = axes[0, 0]
        for i in range(amplitudes.shape[1]):
            ax.plot(times, amplitudes[:, i], label=f'|{i}⟩')
        ax.set_xlabel('Time')
        ax.set_ylabel('Probability')
        ax.set_title('Probability Amplitudes')
        ax.legend()
        ax.grid(True)

        # Plot phases
        ax = axes[0, 1]
        for i in range(phases.shape[1]):
            ax.plot(times, phases[:, i], label=f'|{i}⟩')
        ax.set_xlabel('Time')
        ax.set_ylabel('Phase (rad)')
        ax.set_title('Phases')
        ax.legend()
        ax.grid(True)

        # Plot entropy
        ax = axes[1, 0]
        entropies = [-np.sum(p * np.log2(p + 1e-10)) for p in amplitudes]
        ax.plot(times, entropies, 'b-', linewidth=2)
        ax.set_xlabel('Time')
        ax.set_ylabel('Entropy (bits)')
        ax.set_title('Von Neumann Entropy')
        ax.grid(True)

        # Plot purity
        ax = axes[1, 1]
        purities = [np.sum(p**2) for p in amplitudes]
        ax.plot(times, purities, 'g-', linewidth=2)
        ax.set_xlabel('Time')
        ax.set_ylabel('Purity')
        ax.set_title('State Purity')
        ax.grid(True)

        plt.suptitle(title, fontsize=14)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_density_matrix(
        density_matrix: np.ndarray,
        title: str = "Density Matrix",
        save_path: Optional[str] = None
    ):
        """Visualize density matrix"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Real part
        ax = axes[0]
        im = ax.imshow(np.real(density_matrix), cmap='RdBu',
                      vmin=-1, vmax=1, aspect='auto')
        ax.set_title('Real Part')
        ax.set_xlabel('Basis State')
        ax.set_ylabel('Basis State')
        plt.colorbar(im, ax=ax)

        # Imaginary part
        ax = axes[1]
        im = ax.imshow(np.imag(density_matrix), cmap='RdBu',
                      vmin=-1, vmax=1, aspect='auto')
        ax.set_title('Imaginary Part')
        ax.set_xlabel('Basis State')
        ax.set_ylabel('Basis State')
        plt.colorbar(im, ax=ax)

        plt.suptitle(title, fontsize=14)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig


class CircuitVisualizer:
    """Visualize quantum circuits"""

    @staticmethod
    def draw_circuit(
        gates: List[Dict[str, Any]],
        n_qubits: int,
        title: str = "Quantum Circuit",
        save_path: Optional[str] = None
    ):
        """
        Draw quantum circuit diagram

        Args:
            gates: List of gate dictionaries
            n_qubits: Number of qubits
            title: Plot title
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(max(12, len(gates) * 0.5), n_qubits * 0.8))

        # Draw qubit lines
        for q in range(n_qubits):
            ax.axhline(y=q, xmin=0, xmax=1, color='black', linewidth=1)
            ax.text(-0.5, q, f'q{q}', fontsize=10, ha='right', va='center')

        # Draw gates
        x_pos = 0
        for gate in gates:
            if gate['type'] == 'hadamard':
                q = gate['qubit']
                box = FancyBboxPatch((x_pos - 0.2, q - 0.2), 0.4, 0.4,
                                    boxstyle="round,pad=0.02",
                                    facecolor='yellow', edgecolor='black')
                ax.add_patch(box)
                ax.text(x_pos, q, 'H', ha='center', va='center', fontsize=10)
                x_pos += 0.8

            elif gate['type'] == 'rotation':
                q = gate['qubit']
                box = FancyBboxPatch((x_pos - 0.2, q - 0.2), 0.4, 0.4,
                                    boxstyle="round,pad=0.02",
                                    facecolor='lightblue', edgecolor='black')
                ax.add_patch(box)
                ax.text(x_pos, q, f'R{gate["axis"]}', ha='center', va='center', fontsize=8)
                x_pos += 0.8

            elif gate['type'] == 'cnot':
                control = gate['control']
                target = gate['target']

                # Control dot
                circle = Circle((x_pos, control), 0.08, color='black')
                ax.add_patch(circle)

                # Target cross
                ax.plot([x_pos - 0.1, x_pos + 0.1], [target, target], 'k-', linewidth=2)
                ax.plot([x_pos, x_pos], [target - 0.1, target + 0.1], 'k-', linewidth=2)

                # Connection line
                ax.plot([x_pos, x_pos], [control, target], 'k-', linewidth=1)

                x_pos += 0.8

        ax.set_xlim(-1, x_pos + 0.5)
        ax.set_ylim(-0.5, n_qubits - 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=14, pad=20)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig


class TrainingVisualizer:
    """Visualize training progress and metrics"""

    @staticmethod
    def plot_training_curves(
        episode_rewards: List[float],
        losses: Optional[List[float]] = None,
        q_values: Optional[List[float]] = None,
        epsilons: Optional[List[float]] = None,
        title: str = "Training Progress",
        save_path: Optional[str] = None
    ):
        """Plot comprehensive training curves"""
        n_plots = 2 + (losses is not None) + (q_values is not None) + (epsilons is not None)
        n_cols = 2
        n_rows = (n_plots + 1) // 2

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4 * n_rows))
        axes = axes.flatten() if n_plots > 2 else [axes] if n_plots == 1 else axes

        plot_idx = 0

        # Episode rewards
        ax = axes[plot_idx]
        ax.plot(episode_rewards, alpha=0.3, color='blue', label='Raw')

        # Smoothed rewards
        if len(episode_rewards) >= 100:
            smoothed = np.convolve(episode_rewards, np.ones(100)/100, mode='valid')
            ax.plot(range(99, len(episode_rewards)), smoothed,
                   color='red', linewidth=2, label='Smoothed (100)')

        ax.set_xlabel('Episode')
        ax.set_ylabel('Reward')
        ax.set_title('Episode Rewards')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plot_idx += 1

        # Losses
        if losses:
            ax = axes[plot_idx]
            ax.plot(losses, color='orange', linewidth=1)
            ax.set_xlabel('Training Step')
            ax.set_ylabel('Loss')
            ax.set_title('Training Loss')
            ax.grid(True, alpha=0.3)
            plot_idx += 1

        # Q-values
        if q_values:
            ax = axes[plot_idx]
            ax.plot(q_values, color='green', linewidth=1)
            ax.set_xlabel('Training Step')
            ax.set_ylabel('Q-Value')
            ax.set_title('Mean Q-Value')
            ax.grid(True, alpha=0.3)
            plot_idx += 1

        # Epsilon
        if epsilons:
            ax = axes[plot_idx]
            ax.plot(epsilons, color='purple', linewidth=2)
            ax.set_xlabel('Episode')
            ax.set_ylabel('Epsilon')
            ax.set_title('Exploration Rate')
            ax.grid(True, alpha=0.3)
            plot_idx += 1

        # Hide unused subplots
        for idx in range(plot_idx, len(axes)):
            axes[idx].axis('off')

        plt.suptitle(title, fontsize=14)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_reward_distribution(
        rewards: List[float],
        title: str = "Reward Distribution",
        save_path: Optional[str] = None
    ):
        """Plot reward distribution histogram"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Histogram
        ax = axes[0]
        ax.hist(rewards, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
        ax.axvline(np.mean(rewards), color='red', linestyle='--',
                  linewidth=2, label=f'Mean: {np.mean(rewards):.2f}')
        ax.axvline(np.median(rewards), color='green', linestyle='--',
                  linewidth=2, label=f'Median: {np.median(rewards):.2f}')
        ax.set_xlabel('Reward')
        ax.set_ylabel('Frequency')
        ax.set_title('Reward Histogram')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Box plot
        ax = axes[1]
        bp = ax.boxplot([rewards], patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        ax.set_ylabel('Reward')
        ax.set_title('Reward Box Plot')
        ax.grid(True, alpha=0.3)

        plt.suptitle(title, fontsize=14)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig


class MultiAgentVisualizer:
    """Visualize multi-agent interactions"""

    @staticmethod
    def plot_agent_network(
        positions: np.ndarray,
        connections: List[Tuple[int, int]],
        title: str = "Agent Network",
        save_path: Optional[str] = None
    ):
        """Plot agent network topology"""
        fig, ax = plt.subplots(figsize=(10, 10))

        # Draw connections
        for i, j in connections:
            ax.plot([positions[i, 0], positions[j, 0]],
                   [positions[i, 1], positions[j, 1]],
                   'gray', alpha=0.5, linewidth=1)

        # Draw agents
        ax.scatter(positions[:, 0], positions[:, 1],
                  s=500, c='blue', alpha=0.7, edgecolors='black', linewidth=2)

        # Label agents
        for i, pos in enumerate(positions):
            ax.text(pos[0], pos[1], str(i), ha='center', va='center',
                   fontsize=12, fontweight='bold', color='white')

        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    @staticmethod
    def plot_consensus_dynamics(
        agent_states: np.ndarray,
        title: str = "Consensus Dynamics",
        save_path: Optional[str] = None
    ):
        """Plot how agents reach consensus"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # State evolution
        ax = axes[0]
        for i in range(agent_states.shape[1]):
            ax.plot(agent_states[:, i], label=f'Agent {i}')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('State Value')
        ax.set_title('State Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Agreement level
        ax = axes[1]
        agreement = [np.std(agent_states[t, :]) for t in range(len(agent_states))]
        ax.plot(agreement, color='red', linewidth=2)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Standard Deviation')
        ax.set_title('Agreement Level (lower is better)')
        ax.grid(True, alpha=0.3)

        plt.suptitle(title, fontsize=14)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig


class EnvironmentVisualizer:
    """Visualize environment states"""

    @staticmethod
    def plot_gridworld(
        grid: np.ndarray,
        agent_pos: Tuple[int, int],
        goal_pos: Tuple[int, int],
        obstacles: List[Tuple[int, int]],
        title: str = "Grid World",
        save_path: Optional[str] = None
    ):
        """Visualize grid world environment"""
        fig, ax = plt.subplots(figsize=(10, 10))

        n = grid.shape[0]

        # Draw grid
        for i in range(n + 1):
            ax.axhline(i, 0, n, color='black', linewidth=1)
            ax.axvline(i, 0, n, color='black', linewidth=1)

        # Draw obstacles
        for obs in obstacles:
            rect = plt.Rectangle((obs[1], n - obs[0] - 1), 1, 1,
                                facecolor='gray', edgecolor='black')
            ax.add_patch(rect)

        # Draw goal
        rect = plt.Rectangle((goal_pos[1], n - goal_pos[0] - 1), 1, 1,
                            facecolor='green', edgecolor='black', alpha=0.7)
        ax.add_patch(rect)
        ax.text(goal_pos[1] + 0.5, n - goal_pos[0] - 0.5, 'G',
               ha='center', va='center', fontsize=16, fontweight='bold')

        # Draw agent
        circle = plt.Circle((agent_pos[1] + 0.5, n - agent_pos[0] - 0.5), 0.3,
                           facecolor='blue', edgecolor='black')
        ax.add_patch(circle)
        ax.text(agent_pos[1] + 0.5, n - agent_pos[0] - 0.5, 'A',
               ha='center', va='center', fontsize=12, fontweight='bold', color='white')

        ax.set_xlim(0, n)
        ax.set_ylim(0, n)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=14)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig


def create_training_report(
    metrics: Dict[str, List[float]],
    output_dir: str,
    experiment_name: str = "experiment"
):
    """Create comprehensive training report with all visualizations"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Training curves
    TrainingVisualizer.plot_training_curves(
        episode_rewards=metrics.get('episode_rewards', []),
        losses=metrics.get('losses'),
        q_values=metrics.get('q_values'),
        epsilons=metrics.get('epsilons'),
        title=f"{experiment_name} - Training Progress",
        save_path=output_path / f"{experiment_name}_training_curves.png"
    )
    plt.close()

    # Reward distribution
    if 'episode_rewards' in metrics:
        TrainingVisualizer.plot_reward_distribution(
            rewards=metrics['episode_rewards'],
            title=f"{experiment_name} - Reward Distribution",
            save_path=output_path / f"{experiment_name}_reward_dist.png"
        )
        plt.close()

    logger.info(f"Training report saved to {output_path}")


if __name__ == "__main__":
    # Test visualizations

    # Test Bloch sphere
    state = np.array([1/np.sqrt(2), 1/np.sqrt(2)])
    QuantumStateVisualizer.plot_bloch_sphere(state, "Test State")
    plt.savefig("/mnt/okcomputer/output/test_bloch.png")
    plt.close()

    # Test training curves
    rewards = np.random.randn(100).cumsum()
    losses = np.random.exponential(0.1, 100)
    TrainingVisualizer.plot_training_curves(
        episode_rewards=rewards.tolist(),
        losses=losses.tolist()
    )
    plt.savefig("/mnt/okcomputer/output/test_training.png")
    plt.close()

    print("Test visualizations saved!")
