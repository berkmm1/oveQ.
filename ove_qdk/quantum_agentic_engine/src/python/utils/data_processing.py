#!/usr/bin/env python3
"""
Data Processing Utilities for Quantum Agentic Engine
Dataset handling, preprocessing, and augmentation
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable, Iterator
from dataclasses import dataclass
import logging
from pathlib import Path
import json
import pickle

logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Dataset configuration"""
    batch_size: int = 32
    shuffle: bool = True
    normalize: bool = True
    augment: bool = False
    validation_split: float = 0.2
    test_split: float = 0.1


class QuantumDataset:
    """Base class for quantum-compatible datasets"""

    def __init__(self, config: DatasetConfig = None):
        self.config = config or DatasetConfig()
        self.data = []
        self.labels = []

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[np.ndarray, Any]:
        return self.data[idx], self.labels[idx]

    def add_sample(self, data: np.ndarray, label: Any):
        """Add a sample to the dataset"""
        self.data.append(data)
        self.labels.append(label)

    def normalize(self, method: str = 'standard'):
        """Normalize dataset"""
        if not self.data:
            return

        data_array = np.array(self.data)

        if method == 'standard':
            mean = np.mean(data_array, axis=0)
            std = np.std(data_array, axis=0)
            self.data = [(d - mean) / (std + 1e-8) for d in self.data]
        elif method == 'minmax':
            min_val = np.min(data_array, axis=0)
            max_val = np.max(data_array, axis=0)
            self.data = [(d - min_val) / (max_val - min_val + 1e-8) for d in self.data]
        elif method == 'quantum':
            # Normalize to [-1, 1] for quantum encoding
            max_abs = np.max(np.abs(data_array))
            self.data = [d / (max_abs + 1e-8) for d in self.data]

    def split(self) -> Tuple['QuantumDataset', 'QuantumDataset', 'QuantumDataset']:
        """Split dataset into train/val/test"""
        n = len(self)
        n_test = int(n * self.config.test_split)
        n_val = int(n * self.config.validation_split)
        n_train = n - n_val - n_test

        indices = np.random.permutation(n) if self.config.shuffle else np.arange(n)

        train_indices = indices[:n_train]
        val_indices = indices[n_train:n_train + n_val]
        test_indices = indices[n_train + n_val:]

        train_dataset = QuantumDataset(self.config)
        val_dataset = QuantumDataset(self.config)
        test_dataset = QuantumDataset(self.config)

        for idx in train_indices:
            train_dataset.add_sample(self.data[idx], self.labels[idx])

        for idx in val_indices:
            val_dataset.add_sample(self.data[idx], self.labels[idx])

        for idx in test_indices:
            test_dataset.add_sample(self.data[idx], self.labels[idx])

        return train_dataset, val_dataset, test_dataset

    def batch_iterator(self) -> Iterator[Tuple[np.ndarray, List[Any]]]:
        """Create batch iterator"""
        indices = np.random.permutation(len(self)) if self.config.shuffle else np.arange(len(self))

        for i in range(0, len(self), self.config.batch_size):
            batch_indices = indices[i:i + self.config.batch_size]
            batch_data = np.array([self.data[idx] for idx in batch_indices])
            batch_labels = [self.labels[idx] for idx in batch_indices]
            yield batch_data, batch_labels

    def save(self, filepath: str):
        """Save dataset to file"""
        data = {
            'data': self.data,
            'labels': self.labels,
            'config': self.config.__dict__
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, filepath: str) -> 'QuantumDataset':
        """Load dataset from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        dataset = cls(DatasetConfig(**data['config']))
        dataset.data = data['data']
        dataset.labels = data['labels']
        return dataset


class ExperienceDataset(QuantumDataset):
    """Dataset for reinforcement learning experiences"""

    def __init__(self, config: DatasetConfig = None):
        super().__init__(config)
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []

    def add_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Add an experience tuple"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)

    def __len__(self) -> int:
        return len(self.states)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return {
            'state': self.states[idx],
            'action': self.actions[idx],
            'reward': self.rewards[idx],
            'next_state': self.next_states[idx],
            'done': self.dones[idx]
        }

    def compute_returns(self, gamma: float = 0.99) -> np.ndarray:
        """Compute discounted returns"""
        returns = np.zeros(len(self.rewards))
        running_return = 0

        for t in reversed(range(len(self.rewards))):
            running_return = self.rewards[t] + gamma * running_return * (1 - self.dones[t])
            returns[t] = running_return

        return returns

    def compute_advantages(
        self,
        values: np.ndarray,
        gamma: float = 0.99,
        lam: float = 0.95
    ) -> np.ndarray:
        """Compute GAE advantages"""
        advantages = np.zeros(len(self.rewards))
        last_advantage = 0

        for t in reversed(range(len(self.rewards))):
            if t == len(self.rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]

            delta = self.rewards[t] + gamma * next_value * (1 - self.dones[t]) - values[t]
            advantages[t] = delta + gamma * lam * last_advantage * (1 - self.dones[t])
            last_advantage = advantages[t]

        return advantages


class DataAugmenter:
    """Data augmentation for quantum states"""

    @staticmethod
    def add_gaussian_noise(data: np.ndarray, noise_level: float = 0.1) -> np.ndarray:
        """Add Gaussian noise"""
        noise = np.random.randn(*data.shape) * noise_level
        return data + noise

    @staticmethod
    def random_rotation(data: np.ndarray, max_angle: float = np.pi/8) -> np.ndarray:
        """Apply random rotation"""
        angle = np.random.uniform(-max_angle, max_angle)
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ])

        if len(data.shape) == 1 and len(data) >= 2:
            return rotation_matrix @ data[:2]
        return data

    @staticmethod
    def phase_shift(data: np.ndarray, max_shift: float = np.pi/4) -> np.ndarray:
        """Apply random phase shift"""
        shift = np.random.uniform(-max_shift, max_shift)
        return data * np.exp(1j * shift) if np.iscomplexobj(data) else data

    @staticmethod
    def amplitude_scaling(data: np.ndarray, scale_range: Tuple[float, float] = (0.8, 1.2)) -> np.ndarray:
        """Random amplitude scaling"""
        scale = np.random.uniform(*scale_range)
        return data * scale

    @staticmethod
    def random_permutation(data: np.ndarray, axis: int = 0) -> np.ndarray:
        """Randomly permute elements"""
        perm = np.random.permutation(data.shape[axis])
        return np.take(data, perm, axis=axis)


class QuantumDataEncoder:
    """Encode classical data for quantum processing"""

    @staticmethod
    def angle_encoding(data: np.ndarray, normalize: bool = True) -> np.ndarray:
        """
        Encode data using angle encoding
        Maps data to rotation angles
        """
        if normalize:
            data = np.clip(data, -1, 1)
        return np.arccos(data)

    @staticmethod
    def amplitude_encoding(data: np.ndarray) -> np.ndarray:
        """
        Encode data using amplitude encoding
        Normalizes data to represent quantum amplitudes
        """
        norm = np.linalg.norm(data)
        return data / (norm + 1e-8) if norm > 0 else data

    @staticmethod
    def basis_encoding(data: np.ndarray, threshold: float = 0.0) -> np.ndarray:
        """
        Encode data using basis encoding
        Converts to binary representation
        """
        return (data > threshold).astype(int)

    @staticmethod
    def dense_angle_encoding(data: np.ndarray) -> np.ndarray:
        """
        Dense angle encoding using both Rx and Ry rotations
        """
        angles_x = np.arccos(np.clip(data, -1, 1))
        angles_y = np.arcsin(np.clip(data, -1, 1))
        return np.concatenate([angles_x, angles_y])

    @staticmethod
    def phase_encoding(data: np.ndarray) -> np.ndarray:
        """
        Encode data in phases
        """
        return np.exp(1j * np.pi * data)


class DataPipeline:
    """Complete data processing pipeline"""

    def __init__(
        self,
        encoder: str = 'angle',
        normalize: bool = True,
        augment: bool = False,
        augmentation_config: Dict = None
    ):
        self.encoder = encoder
        self.normalize = normalize
        self.augment = augment
        self.augmentation_config = augmentation_config or {}
        self.augmenter = DataAugmenter()

    def process(self, data: np.ndarray) -> np.ndarray:
        """Process data through pipeline"""
        # Normalization
        if self.normalize:
            data = self._normalize(data)

        # Augmentation
        if self.augment:
            data = self._augment(data)

        # Encoding
        data = self._encode(data)

        return data

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data"""
        return (data - np.mean(data)) / (np.std(data) + 1e-8)

    def _augment(self, data: np.ndarray) -> np.ndarray:
        """Apply data augmentation"""
        if np.random.random() < self.augmentation_config.get('noise_prob', 0.3):
            data = self.augmenter.add_gaussian_noise(
                data,
                self.augmentation_config.get('noise_level', 0.1)
            )

        if np.random.random() < self.augmentation_config.get('scale_prob', 0.3):
            data = self.augmenter.amplitude_scaling(data)

        return data

    def _encode(self, data: np.ndarray) -> np.ndarray:
        """Encode data for quantum processing"""
        encoder = QuantumDataEncoder()

        if self.encoder == 'angle':
            return encoder.angle_encoding(data)
        elif self.encoder == 'amplitude':
            return encoder.amplitude_encoding(data)
        elif self.encoder == 'basis':
            return encoder.basis_encoding(data)
        elif self.encoder == 'dense_angle':
            return encoder.dense_angle_encoding(data)
        elif self.encoder == 'phase':
            return encoder.phase_encoding(data)
        else:
            return data


class FeatureExtractor:
    """Feature extraction utilities"""

    @staticmethod
    def statistical_features(data: np.ndarray) -> Dict[str, float]:
        """Extract statistical features"""
        return {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'median': float(np.median(data)),
            'skewness': float(np.mean((data - np.mean(data))**3) / (np.std(data)**3 + 1e-8)),
            'kurtosis': float(np.mean((data - np.mean(data))**4) / (np.std(data)**4 + 1e-8))
        }

    @staticmethod
    def frequency_features(data: np.ndarray) -> Dict[str, float]:
        """Extract frequency domain features"""
        fft = np.fft.fft(data)
        magnitude = np.abs(fft)

        return {
            'dominant_freq': float(np.argmax(magnitude)),
            'spectral_energy': float(np.sum(magnitude**2)),
            'spectral_entropy': float(-np.sum(magnitude * np.log(magnitude + 1e-10))),
            'spectral_centroid': float(np.sum(np.arange(len(magnitude)) * magnitude) / np.sum(magnitude))
        }

    @staticmethod
    def quantum_features(data: np.ndarray) -> Dict[str, float]:
        """Extract quantum-inspired features"""
        # Encode as quantum state
        encoded = QuantumDataEncoder.amplitude_encoding(data)

        # Compute pseudo-density matrix
        density = np.outer(encoded, encoded.conj())

        # Von Neumann entropy approximation
        eigenvalues = np.linalg.eigvalsh(density)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        entropy = -np.sum(eigenvalues * np.log2(eigenvalues))

        return {
            'quantum_entropy': float(entropy),
            'quantum_purity': float(np.trace(density @ density)),
            'quantum_fisher': float(np.var(encoded))
        }


if __name__ == "__main__":
    # Test data processing

    # Create sample dataset
    dataset = QuantumDataset()
    for i in range(100):
        data = np.random.randn(16)
        label = i % 4
        dataset.add_sample(data, label)

    print(f"Dataset size: {len(dataset)}")

    # Normalize
    dataset.normalize('quantum')
    print("Dataset normalized")

    # Split
    train, val, test = dataset.split()
    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    # Test batch iterator
    for batch_data, batch_labels in train.batch_iterator():
        print(f"Batch shape: {batch_data.shape}")
        break

    # Test feature extraction
    sample = dataset[0][0]
    stats = FeatureExtractor.statistical_features(sample)
    print(f"Statistical features: {stats}")

    quantum_feats = FeatureExtractor.quantum_features(sample)
    print(f"Quantum features: {quantum_feats}")
