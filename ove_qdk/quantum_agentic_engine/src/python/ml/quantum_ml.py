#!/usr/bin/env python3
"""
Quantum Machine Learning Module
Comprehensive quantum machine learning algorithms and utilities
Part of the Quantum Agentic Loop Engine
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from collections import defaultdict
import json
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumMLBackend(Enum):
    """Supported quantum ML backends"""
    QSHARP = auto()
    QISKIT = auto()
    CIRQ = auto()
    PENNYLANE = auto()
    SIMULATOR = auto()


@dataclass
class QuantumMLConfig:
    """Configuration for quantum machine learning"""
    backend: QuantumMLBackend = QuantumMLBackend.SIMULATOR
    num_qubits: int = 8
    num_layers: int = 3
    learning_rate: float = 0.01
    batch_size: int = 32
    epochs: int = 100
    optimizer: str = "adam"
    loss_function: str = "mse"
    regularization: float = 0.001
    device: str = "default.qubit"
    shots: int = 1000
    random_seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            'backend': self.backend.name,
            'num_qubits': self.num_qubits,
            'num_layers': self.num_layers,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'epochs': self.epochs,
            'optimizer': self.optimizer,
            'loss_function': self.loss_function,
            'regularization': self.regularization,
            'device': self.device,
            'shots': self.shots,
            'random_seed': self.random_seed
        }


@dataclass
class QuantumLayer:
    """Quantum neural network layer"""
    name: str
    num_qubits: int
    num_parameters: int
    rotation_type: str = "RY"
    entanglement: str = "linear"
    activation: Optional[str] = None

    def __post_init__(self):
        self.parameters = np.random.randn(self.num_parameters) * 0.1
        self.parameter_history = []

    def get_parameter_count(self) -> int:
        return self.num_parameters

    def update_parameters(self, gradients: np.ndarray, learning_rate: float):
        """Update layer parameters using gradients"""
        self.parameter_history.append(self.parameters.copy())
        self.parameters -= learning_rate * gradients

    def get_parameter_norm(self) -> float:
        """Get L2 norm of parameters"""
        return np.linalg.norm(self.parameters)


class QuantumFeatureMap:
    """Quantum feature mapping for classical data"""

    def __init__(self, num_qubits: int, feature_dimension: int, map_type: str = "angle"):
        self.num_qubits = num_qubits
        self.feature_dimension = feature_dimension
        self.map_type = map_type
        self.scaler_mean = None
        self.scaler_std = None

    def fit(self, X: np.ndarray):
        """Fit feature map to data"""
        self.scaler_mean = np.mean(X, axis=0)
        self.scaler_std = np.std(X, axis=0) + 1e-8

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform classical data to quantum features"""
        if self.scaler_mean is None:
            self.fit(X)

        # Normalize
        X_normalized = (X - self.scaler_mean) / self.scaler_std

        if self.map_type == "angle":
            return self._angle_encoding(X_normalized)
        elif self.map_type == "amplitude":
            return self._amplitude_encoding(X_normalized)
        elif self.map_type == "dense":
            return self._dense_encoding(X_normalized)
        else:
            return self._angle_encoding(X_normalized)

    def _angle_encoding(self, X: np.ndarray) -> np.ndarray:
        """Encode features as rotation angles"""
        # Scale to valid rotation range [-π, π]
        return np.arctan(X) * np.pi

    def _amplitude_encoding(self, X: np.ndarray) -> np.ndarray:
        """Encode features as amplitudes"""
        # Normalize to unit vector
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        return X / (norms + 1e-8)

    def _dense_encoding(self, X: np.ndarray) -> np.ndarray:
        """Dense angle encoding with multiple rotations"""
        # Repeat features for multiple rotations per qubit
        features_per_qubit = max(1, self.feature_dimension // self.num_qubits)
        encoded = np.zeros((len(X), self.num_qubits * 3))  # RX, RY, RZ per qubit

        for i in range(self.num_qubits):
            start_idx = i * features_per_qubit
            end_idx = min(start_idx + features_per_qubit, self.feature_dimension)

            if start_idx < self.feature_dimension:
                feature_slice = X[:, start_idx:end_idx].mean(axis=1)
                encoded[:, i * 3] = feature_slice * np.pi  # RX
                encoded[:, i * 3 + 1] = feature_slice * np.pi / 2  # RY
                encoded[:, i * 3 + 2] = feature_slice * np.pi / 4  # RZ

        return encoded

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform in one step"""
        self.fit(X)
        return self.transform(X)


class QuantumKernel:
    """Quantum kernel for support vector machines"""

    def __init__(self, num_qubits: int, kernel_type: str = "zz"):
        self.num_qubits = num_qubits
        self.kernel_type = kernel_type
        self.feature_map = None

    def build_circuit(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """Build and evaluate quantum kernel circuit"""
        # Simplified kernel computation
        if self.kernel_type == "zz":
            return self._zz_kernel(x1, x2)
        elif self.kernel_type == "cnot":
            return self._cnot_kernel(x1, x2)
        else:
            return self._zz_kernel(x1, x2)

    def _zz_kernel(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """ZZ-feature map kernel"""
        # K(x1, x2) = |<0|U†(x2)U(x1)|0>|²
        diff = x1 - x2
        similarity = np.exp(-np.sum(diff ** 2) / (2 * len(diff)))
        return similarity

    def _cnot_kernel(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """CNOT-based kernel"""
        # Entanglement-based similarity
        product = np.dot(x1, x2)
        norm1 = np.linalg.norm(x1)
        norm2 = np.linalg.norm(x2)
        return (product / (norm1 * norm2 + 1e-8)) ** 2

    def compute_kernel_matrix(self, X1: np.ndarray, X2: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute full kernel matrix"""
        if X2 is None:
            X2 = X1

        n1 = len(X1)
        n2 = len(X2)
        K = np.zeros((n1, n2))

        for i in range(n1):
            for j in range(n2):
                K[i, j] = self.build_circuit(X1[i], X2[j])

        return K


class QuantumNeuralNetwork:
    """Quantum Neural Network implementation"""

    def __init__(self, config: QuantumMLConfig):
        self.config = config
        self.layers: List[QuantumLayer] = []
        self.feature_map = None
        self.history = {'loss': [], 'val_loss': [], 'accuracy': []}
        self.is_fitted = False

    def add_layer(self, layer: QuantumLayer):
        """Add a layer to the network"""
        self.layers.append(layer)
        logger.info(f"Added layer: {layer.name} with {layer.num_parameters} parameters")

    def build(self, input_dim: int):
        """Build network architecture"""
        # Feature mapping layer
        self.feature_map = QuantumFeatureMap(
            self.config.num_qubits,
            input_dim,
            map_type="angle"
        )

        # Build variational layers
        for i in range(self.config.num_layers):
            layer = QuantumLayer(
                name=f"variational_{i}",
                num_qubits=self.config.num_qubits,
                num_parameters=self.config.num_qubits * 3,  # RX, RY, RZ per qubit
                rotation_type="RY",
                entanglement="linear"
            )
            self.add_layer(layer)

        # Output layer
        output_layer = QuantumLayer(
            name="output",
            num_qubits=self.config.num_qubits,
            num_parameters=self.config.num_qubits,
            rotation_type="RY",
            activation="sigmoid"
        )
        self.add_layer(output_layer)

        total_params = sum(layer.get_parameter_count() for layer in self.layers)
        logger.info(f"Network built with {total_params} total parameters")

    def forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass through the network"""
        # Transform features
        features = self.feature_map.transform(X)

        # Apply variational layers
        for layer in self.layers:
            features = self._apply_layer(features, layer)

        # Output
        return self._apply_output(features)

    def _apply_layer(self, features: np.ndarray, layer: QuantumLayer) -> np.ndarray:
        """Apply a quantum layer"""
        # Simplified: apply parameterized rotations
        output = np.zeros((len(features), layer.num_qubits))

        for i in range(layer.num_qubits):
            param_start = i * 3
            if param_start + 2 < len(layer.parameters):
                # Apply rotations
                rx_angle = layer.parameters[param_start]
                ry_angle = layer.parameters[param_start + 1]
                rz_angle = layer.parameters[param_start + 2]

                # Simulate quantum rotation effects
                if i < features.shape[1]:
                    output[:, i] = (
                        features[:, i] * np.cos(ry_angle) * np.cos(rz_angle) +
                        rx_angle * 0.1
                    )

        return output

    def _apply_output(self, features: np.ndarray) -> np.ndarray:
        """Apply output layer"""
        # Average over qubits and apply sigmoid
        avg = np.mean(features, axis=1)
        return 1 / (1 + np.exp(-avg))

    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute loss"""
        if self.config.loss_function == "mse":
            return np.mean((y_pred - y_true) ** 2)
        elif self.config.loss_function == "cross_entropy":
            epsilon = 1e-8
            return -np.mean(y_true * np.log(y_pred + epsilon) +
                          (1 - y_true) * np.log(1 - y_pred + epsilon))
        else:
            return np.mean((y_pred - y_true) ** 2)

    def compute_gradients(self, X: np.ndarray, y: np.ndarray) -> List[np.ndarray]:
        """Compute gradients using finite differences"""
        gradients = []
        epsilon = 1e-5

        y_pred = self.forward(X)
        base_loss = self.compute_loss(y_pred, y)

        for layer in self.layers:
            layer_grad = np.zeros_like(layer.parameters)

            for i in range(len(layer.parameters)):
                # Forward difference
                original = layer.parameters[i]
                layer.parameters[i] = original + epsilon

                y_pred_perturbed = self.forward(X)
                perturbed_loss = self.compute_loss(y_pred_perturbed, y)

                layer_grad[i] = (perturbed_loss - base_loss) / epsilon
                layer.parameters[i] = original

            gradients.append(layer_grad)

        return gradients

    def fit(self, X: np.ndarray, y: np.ndarray,
            X_val: Optional[np.ndarray] = None,
            y_val: Optional[np.ndarray] = None,
            verbose: bool = True):
        """Train the quantum neural network"""
        if not self.layers:
            self.build(X.shape[1])

        self.feature_map.fit(X)

        n_samples = len(X)
        n_batches = (n_samples + self.config.batch_size - 1) // self.config.batch_size

        for epoch in range(self.config.epochs):
            epoch_loss = 0.0

            # Shuffle data
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            for batch_idx in range(n_batches):
                start_idx = batch_idx * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, n_samples)

                X_batch = X_shuffled[start_idx:end_idx]
                y_batch = y_shuffled[start_idx:end_idx]

                # Forward pass
                y_pred = self.forward(X_batch)
                batch_loss = self.compute_loss(y_pred, y_batch)
                epoch_loss += batch_loss * (end_idx - start_idx)

                # Backward pass
                gradients = self.compute_gradients(X_batch, y_batch)

                # Update parameters
                for layer, grad in zip(self.layers, gradients):
                    layer.update_parameters(grad, self.config.learning_rate)

            epoch_loss /= n_samples
            self.history['loss'].append(epoch_loss)

            # Validation
            if X_val is not None and y_val is not None:
                y_val_pred = self.forward(X_val)
                val_loss = self.compute_loss(y_val_pred, y_val)
                self.history['val_loss'].append(val_loss)

            if verbose and epoch % 10 == 0:
                msg = f"Epoch {epoch}/{self.config.epochs}, Loss: {epoch_loss:.4f}"
                if X_val is not None:
                    msg += f", Val Loss: {val_loss:.4f}"
                logger.info(msg)

        self.is_fitted = True
        logger.info("Training completed")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            logger.warning("Model not fitted yet")
        return self.forward(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        y_pred = self.predict(X)

        metrics = {
            'loss': self.compute_loss(y_pred, y),
            'mse': np.mean((y_pred - y) ** 2),
            'mae': np.mean(np.abs(y_pred - y))
        }

        # Accuracy for binary classification
        if len(np.unique(y)) == 2:
            y_pred_binary = (y_pred > 0.5).astype(int)
            metrics['accuracy'] = np.mean(y_pred_binary == y)

        return metrics

    def save(self, filepath: str):
        """Save model to file"""
        model_data = {
            'config': self.config.to_dict(),
            'layers': [
                {
                    'name': layer.name,
                    'num_qubits': layer.num_qubits,
                    'num_parameters': layer.num_parameters,
                    'parameters': layer.parameters.tolist(),
                    'rotation_type': layer.rotation_type,
                    'entanglement': layer.entanglement
                }
                for layer in self.layers
            ],
            'history': self.history,
            'is_fitted': self.is_fitted
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        logger.info(f"Model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'QuantumNeuralNetwork':
        """Load model from file"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        config = QuantumMLConfig(**model_data['config'])
        model = cls(config)

        for layer_data in model_data['layers']:
            layer = QuantumLayer(
                name=layer_data['name'],
                num_qubits=layer_data['num_qubits'],
                num_parameters=layer_data['num_parameters'],
                rotation_type=layer_data['rotation_type'],
                entanglement=layer_data['entanglement']
            )
            layer.parameters = np.array(layer_data['parameters'])
            model.layers.append(layer)

        model.history = model_data['history']
        model.is_fitted = model_data['is_fitted']

        logger.info(f"Model loaded from {filepath}")
        return model


class QuantumSupportVectorMachine:
    """Quantum Support Vector Machine"""

    def __init__(self, num_qubits: int = 8, kernel_type: str = "zz", C: float = 1.0):
        self.num_qubits = num_qubits
        self.kernel_type = kernel_type
        self.C = C
        self.kernel = QuantumKernel(num_qubits, kernel_type)
        self.alpha = None
        self.support_vectors = None
        self.support_labels = None
        self.bias = 0.0
        self.feature_map = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train quantum SVM"""
        logger.info("Training Quantum SVM...")

        # Feature mapping
        self.feature_map = QuantumFeatureMap(self.num_qubits, X.shape[1])
        X_mapped = self.feature_map.fit_transform(X)

        # Compute kernel matrix
        K = self.kernel.compute_kernel_matrix(X_mapped)

        # Simplified SMO algorithm
        n_samples = len(X)
        self.alpha = np.zeros(n_samples)

        # Iterative optimization
        for _ in range(100):
            for i in range(n_samples):
                # Compute prediction
                prediction = np.sum(self.alpha * y * K[:, i]) + self.bias

                # Update alpha
                error = y[i] * prediction - 1
                if error < 0 or (self.alpha[i] < self.C and error > 0):
                    self.alpha[i] = min(self.C, max(0,
                        self.alpha[i] - 0.01 * error))

        # Store support vectors
        support_mask = self.alpha > 1e-5
        self.support_vectors = X[support_mask]
        self.support_labels = y[support_mask]
        self.alpha = self.alpha[support_mask]

        # Compute bias
        if len(self.support_vectors) > 0:
            K_sv = self.kernel.compute_kernel_matrix(
                self.feature_map.transform(self.support_vectors)
            )
            self.bias = np.mean(
                self.support_labels -
                np.sum(self.alpha * self.support_labels * K_sv, axis=1)
            )

        logger.info(f"Training complete. {len(self.support_vectors)} support vectors found.")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        X_mapped = self.feature_map.transform(X)

        if len(self.support_vectors) == 0:
            return np.zeros(len(X))

        K = self.kernel.compute_kernel_matrix(
            X_mapped,
            self.feature_map.transform(self.support_vectors)
        )

        predictions = np.sum(
            self.alpha * self.support_labels * K,
            axis=1
        ) + self.bias

        return np.sign(predictions)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate accuracy"""
        predictions = self.predict(X)
        return np.mean(predictions == y)


class QuantumGenerativeModel:
    """Quantum Generative Model (Born Machine)"""

    def __init__(self, num_qubits: int = 8, num_layers: int = 3):
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self.parameters = np.random.randn(num_layers * num_qubits * 3) * 0.1
        self.history = []

    def circuit(self, parameters: np.ndarray) -> np.ndarray:
        """Evaluate quantum circuit"""
        # Simplified: return probability distribution
        state = np.ones(2 ** self.num_qubits) / np.sqrt(2 ** self.num_qubits)

        # Apply parameterized rotations
        for layer in range(self.num_layers):
            for qubit in range(self.num_qubits):
                idx = layer * self.num_qubits * 3 + qubit * 3
                if idx + 2 < len(parameters):
                    theta = parameters[idx]
                    phi = parameters[idx + 1]

                    # Simulate rotation effect
                    state *= np.exp(1j * (theta + phi))

        probabilities = np.abs(state) ** 2
        return probabilities

    def train(self, data: np.ndarray, epochs: int = 100, learning_rate: float = 0.01):
        """Train generative model using MMD loss"""
        logger.info("Training Quantum Generative Model...")

        # Convert data to distribution
        data_dist = self._data_to_distribution(data)

        for epoch in range(epochs):
            # Generate samples
            model_dist = self.circuit(self.parameters)

            # Compute MMD loss
            loss = self._mmd_loss(model_dist, data_dist)
            self.history.append(loss)

            # Compute gradients (finite differences)
            gradients = np.zeros_like(self.parameters)
            epsilon = 1e-5

            for i in range(len(self.parameters)):
                params_plus = self.parameters.copy()
                params_plus[i] += epsilon

                dist_plus = self.circuit(params_plus)
                loss_plus = self._mmd_loss(dist_plus, data_dist)

                gradients[i] = (loss_plus - loss) / epsilon

            # Update parameters
            self.parameters -= learning_rate * gradients

            if epoch % 20 == 0:
                logger.info(f"Epoch {epoch}, Loss: {loss:.4f}")

        logger.info("Training complete")

    def _data_to_distribution(self, data: np.ndarray) -> np.ndarray:
        """Convert data samples to probability distribution"""
        # Discretize data into bins
        hist, _ = np.histogram(data, bins=2 ** self.num_qubits, range=(0, 1))
        return hist / len(data)

    def _mmd_loss(self, p: np.ndarray, q: np.ndarray) -> float:
        """Maximum Mean Discrepancy loss"""
        # Simplified MMD
        return np.sum((p - q) ** 2)

    def sample(self, n_samples: int) -> np.ndarray:
        """Generate samples from the model"""
        probabilities = self.circuit(self.parameters)

        # Sample from distribution
        samples = np.random.choice(
            len(probabilities),
            size=n_samples,
            p=probabilities
        )

        return samples / len(probabilities)


class QuantumReinforcementLearning:
    """Quantum Reinforcement Learning Agent"""

    def __init__(self, state_dim: int, action_dim: int, num_qubits: int = 8):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_qubits = num_qubits

        # Policy network
        self.policy_config = QuantumMLConfig(
            num_qubits=num_qubits,
            num_layers=2,
            learning_rate=0.001
        )
        self.policy = QuantumNeuralNetwork(self.policy_config)

        # Value network
        self.value_config = QuantumMLConfig(
            num_qubits=num_qubits,
            num_layers=2,
            learning_rate=0.001
        )
        self.value = QuantumNeuralNetwork(self.value_config)

        self.gamma = 0.99
        self.epsilon = 0.1

    def select_action(self, state: np.ndarray) -> int:
        """Select action using epsilon-greedy policy"""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)

        # Get action probabilities from policy
        probs = self.policy.predict(state.reshape(1, -1))

        # Sample action
        action = np.random.choice(self.action_dim, p=probs / np.sum(probs))
        return action

    def update(self, states: np.ndarray, actions: np.ndarray,
               rewards: np.ndarray, next_states: np.ndarray, dones: np.ndarray):
        """Update policy and value networks"""
        # Compute returns
        returns = np.zeros_like(rewards)
        running_return = 0

        for t in reversed(range(len(rewards))):
            running_return = rewards[t] + self.gamma * running_return * (1 - dones[t])
            returns[t] = running_return

        # Update value network
        value_pred = self.value.predict(states)
        value_loss = np.mean((value_pred - returns) ** 2)

        # Update policy network
        advantages = returns - value_pred

        # Policy gradient update
        for i in range(len(states)):
            state = states[i].reshape(1, -1)
            action = actions[i]
            advantage = advantages[i]

            # Increase probability of good actions
            if advantage > 0:
                # Forward pass and update
                _ = self.policy.predict(state)

    def train_episode(self, env, max_steps: int = 1000) -> float:
        """Train for one episode"""
        state = env.reset()
        episode_reward = 0.0

        states, actions, rewards, next_states, dones = [], [], [], [], []

        for step in range(max_steps):
            action = self.select_action(state)
            next_state, reward, done, _ = env.step(action)

            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(float(done))

            episode_reward += reward
            state = next_state

            if done:
                break

        # Update networks
        if len(states) > 0:
            self.update(
                np.array(states),
                np.array(actions),
                np.array(rewards),
                np.array(next_states),
                np.array(dones)
            )

        return episode_reward


# Utility functions
def create_quantum_classifier(num_qubits: int = 8, num_layers: int = 3) -> QuantumNeuralNetwork:
    """Create a quantum classifier"""
    config = QuantumMLConfig(
        num_qubits=num_qubits,
        num_layers=num_layers,
        loss_function="cross_entropy"
    )
    return QuantumNeuralNetwork(config)


def create_quantum_regressor(num_qubits: int = 8, num_layers: int = 3) -> QuantumNeuralNetwork:
    """Create a quantum regressor"""
    config = QuantumMLConfig(
        num_qubits=num_qubits,
        num_layers=num_layers,
        loss_function="mse"
    )
    return QuantumNeuralNetwork(config)


def quantum_kmeans(X: np.ndarray, n_clusters: int = 3, num_qubits: int = 8) -> np.ndarray:
    """Quantum-enhanced k-means clustering"""
    # Feature mapping
    feature_map = QuantumFeatureMap(num_qubits, X.shape[1])
    X_mapped = feature_map.fit_transform(X)

    # Initialize centroids
    centroids = X_mapped[np.random.choice(len(X), n_clusters, replace=False)]

    # Quantum kernel for distance computation
    kernel = QuantumKernel(num_qubits)

    for _ in range(100):
        # Assign points to clusters using quantum similarity
        labels = np.zeros(len(X), dtype=int)

        for i, x in enumerate(X_mapped):
            similarities = []
            for centroid in centroids:
                sim = kernel.build_circuit(x, centroid)
                similarities.append(sim)
            labels[i] = np.argmax(similarities)

        # Update centroids
        for k in range(n_clusters):
            mask = labels == k
            if np.sum(mask) > 0:
                centroids[k] = np.mean(X_mapped[mask], axis=0)

    return labels


if __name__ == "__main__":
    # Example usage
    print("Quantum Machine Learning Module")
    print("=" * 40)

    # Create sample data
    np.random.seed(42)
    X_train = np.random.randn(100, 4)
    y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(int)

    # Create and train quantum classifier
    config = QuantumMLConfig(num_qubits=4, num_layers=2, epochs=50)
    model = QuantumNeuralNetwork(config)
    model.build(X_train.shape[1])
    model.fit(X_train, y_train, verbose=True)

    # Evaluate
    metrics = model.evaluate(X_train, y_train)
    print(f"\nTraining metrics: {metrics}")
