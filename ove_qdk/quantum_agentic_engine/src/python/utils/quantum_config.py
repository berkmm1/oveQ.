"""
Quantum Configuration Manager
============================

Centralized configuration management for the quantum agentic engine.
Handles loading, validation, and merging of configuration files.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum, auto
import copy
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConfigSource(Enum):
    """Sources of configuration."""
    DEFAULT = auto()
    FILE = auto()
    ENVIRONMENT = auto()
    CODE = auto()
    COMMAND_LINE = auto()


@dataclass
class AgentConfig:
    """Configuration for quantum agent."""
    num_qubits: int = 20
    max_iterations: int = 1000
    convergence_threshold: float = 1e-6
    learning_rate: float = 0.01
    discount_factor: float = 0.99
    exploration_rate: float = 0.1
    memory_size: int = 10000
    batch_size: int = 32
    num_episodes: int = 100
    episode_length: int = 100
    reward_scale: float = 1.0
    use_error_correction: bool = True
    error_correction_code: str = "surface"
    backend: str = "simulator"
    shots: int = 1024
    optimization_level: int = 1


@dataclass
class CircuitConfig:
    """Configuration for quantum circuits."""
    max_depth: int = 100
    max_gates: int = 1000
    gate_set: List[str] = field(default_factory=lambda: ['H', 'X', 'Y', 'Z', 'CNOT', 'Rx', 'Ry', 'Rz'])
    allow_parameterized: bool = True
    allow_measurements: bool = True
    allow_classical_control: bool = True
    transpile_before_execution: bool = True
    optimization_passes: List[str] = field(default_factory=lambda: ['cancel_inverse', 'merge_rotations'])


@dataclass
class TrainingConfig:
    """Configuration for training."""
    algorithm: str = "quantum_ppo"
    epochs: int = 100
    steps_per_epoch: int = 4000
    gamma: float = 0.99
    lam: float = 0.95
    clip_ratio: float = 0.2
    target_kl: float = 0.01
    value_function_lr: float = 1e-3
    policy_lr: float = 3e-4
    entropy_coefficient: float = 0.01
    max_grad_norm: float = 0.5
    save_frequency: int = 10
    eval_frequency: int = 5
    checkpoint_dir: str = "./checkpoints"


@dataclass
class EnvironmentConfig:
    """Configuration for quantum environments."""
    env_type: str = "quantum_grid"
    grid_size: int = 4
    num_actions: int = 4
    observation_dim: int = 16
    reward_function: str = "sparse"
    max_steps: int = 100
    stochastic: bool = False
    partial_observable: bool = False
    multi_agent: bool = False
    num_agents: int = 1


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_console: bool = True
    enable_file: bool = False
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    metrics_enabled: bool = True
    profiling_enabled: bool = False


@dataclass
class QuantumConfig:
    """Main quantum configuration."""
    agent: AgentConfig = field(default_factory=AgentConfig)
    circuit: CircuitConfig = field(default_factory=CircuitConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    version: str = "1.0.0"
    config_source: str = "default"


class ConfigurationManager:
    """
    Centralized configuration manager.

    Handles loading configuration from multiple sources,
    validation, and dynamic updates.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize configuration manager."""
        if self._initialized:
            return

        self._config = QuantumConfig()
        self._config_history: List[Dict] = []
        self._validators: Dict[str, callable] = {}
        self._sources: Dict[str, ConfigSource] = {}

        self._register_default_validators()
        self._initialized = True

    def _register_default_validators(self) -> None:
        """Register default configuration validators."""
        self.register_validator('agent.num_qubits', self._validate_positive_int)
        self.register_validator('agent.learning_rate', self._validate_positive_float)
        self.register_validator('agent.discount_factor', self._validate_probability)
        self.register_validator('training.epochs', self._validate_positive_int)
        self.register_validator('circuit.max_depth', self._validate_positive_int)

    def register_validator(self, path: str, validator: callable) -> None:
        """
        Register a validator for a configuration path.

        Args:
            path: Dot-separated path to configuration value
            validator: Validation function
        """
        self._validators[path] = validator

    def load_from_file(self, filepath: str, source: ConfigSource = ConfigSource.FILE) -> None:
        """
        Load configuration from file.

        Args:
            filepath: Path to configuration file
            source: Configuration source type
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        # Load based on file extension
        if filepath.suffix in ['.yaml', '.yml']:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        elif filepath.suffix == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported configuration format: {filepath.suffix}")

        self._merge_config(data, source)
        logger.info(f"Configuration loaded from {filepath}")

    def load_from_dict(self, config_dict: Dict[str, Any],
                      source: ConfigSource = ConfigSource.CODE) -> None:
        """
        Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary
            source: Configuration source type
        """
        self._merge_config(config_dict, source)

    def load_from_environment(self, prefix: str = "QUANTUM_") -> None:
        """
        Load configuration from environment variables.

        Args:
            prefix: Prefix for environment variables
        """
        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert QUANTUM_AGENT_NUM_QUBITS to agent.num_qubits
                config_key = key[len(prefix):].lower().replace('_', '.')

                # Try to parse value
                parsed_value = self._parse_env_value(value)
                self._set_nested_value(env_config, config_key, parsed_value)

        if env_config:
            self._merge_config(env_config, ConfigSource.ENVIRONMENT)
            logger.info("Configuration loaded from environment variables")

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value."""
        # Try int
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try bool
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False

        # Try list (comma-separated)
        if ',' in value:
            return [self._parse_env_value(v.strip()) for v in value.split(',')]

        # Return as string
        return value

    def _merge_config(self, updates: Dict[str, Any], source: ConfigSource) -> None:
        """
        Merge configuration updates.

        Args:
            updates: Configuration updates
            source: Source of updates
        """
        # Save current state to history
        self._config_history.append({
            'timestamp': self._get_timestamp(),
            'config': copy.deepcopy(asdict(self._config)),
            'source': source.name
        })

        # Merge updates
        self._deep_merge(asdict(self._config), updates)

        # Validate
        self.validate()

        # Track sources
        for key in self._flatten_keys(updates):
            self._sources[key] = source

    def _deep_merge(self, base: Dict, updates: Dict) -> None:
        """Deep merge dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _flatten_keys(self, d: Dict, parent_key: str = '') -> List[str]:
        """Flatten dictionary keys."""
        keys = []
        for key, value in d.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                keys.extend(self._flatten_keys(value, full_key))
            else:
                keys.append(full_key)
        return keys

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by path.

        Args:
            path: Dot-separated path
            default: Default value if not found

        Returns:
            Configuration value
        """
        config_dict = asdict(self._config)
        return self._get_nested_value(config_dict, path, default)

    def set(self, path: str, value: Any, source: ConfigSource = ConfigSource.CODE) -> None:
        """
        Set configuration value by path.

        Args:
            path: Dot-separated path
            value: Value to set
            source: Source of the value
        """
        config_dict = asdict(self._config)
        self._set_nested_value(config_dict, path, value)

        # Update config object
        self._config = self._dict_to_config(config_dict)

        # Track source
        self._sources[path] = source

        # Validate
        self.validate_path(path)

    def _get_nested_value(self, d: Dict, path: str, default: Any = None) -> Any:
        """Get nested dictionary value."""
        keys = path.split('.')
        current = d

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def _set_nested_value(self, d: Dict, path: str, value: Any) -> None:
        """Set nested dictionary value."""
        keys = path.split('.')
        current = d

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def validate(self) -> bool:
        """
        Validate entire configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        for path, validator in self._validators.items():
            value = self.get(path)
            if value is not None:
                validator(value, path)

        return True

    def validate_path(self, path: str) -> bool:
        """
        Validate specific configuration path.

        Args:
            path: Path to validate

        Returns:
            True if valid
        """
        if path in self._validators:
            value = self.get(path)
            self._validators[path](value, path)

        return True

    def _validate_positive_int(self, value: Any, path: str) -> None:
        """Validate positive integer."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{path} must be a positive integer, got {value}")

    def _validate_positive_float(self, value: Any, path: str) -> None:
        """Validate positive float."""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{path} must be a positive number, got {value}")

    def _validate_probability(self, value: Any, path: str) -> None:
        """Validate probability value."""
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            raise ValueError(f"{path} must be between 0 and 1, got {value}")

    def get_config(self) -> QuantumConfig:
        """Get current configuration."""
        return self._config

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return asdict(self._config)

    def save_to_file(self, filepath: str, format: str = 'yaml') -> None:
        """
        Save configuration to file.

        Args:
            filepath: Output file path
            format: Output format ('yaml' or 'json')
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        config_dict = self.get_config_dict()

        if format == 'yaml':
            with open(filepath, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        elif format == 'json':
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Configuration saved to {filepath}")

    def get_sources(self) -> Dict[str, str]:
        """Get configuration sources."""
        return {path: source.name for path, source in self._sources.items()}

    def get_history(self) -> List[Dict]:
        """Get configuration history."""
        return self._config_history

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._config = QuantumConfig()
        self._sources.clear()
        self._config_history.clear()
        logger.info("Configuration reset to defaults")

    def _dict_to_config(self, d: Dict) -> QuantumConfig:
        """Convert dictionary to QuantumConfig."""
        return QuantumConfig(
            agent=AgentConfig(**d.get('agent', {})),
            circuit=CircuitConfig(**d.get('circuit', {})),
            training=TrainingConfig(**d.get('training', {})),
            environment=EnvironmentConfig(**d.get('environment', {})),
            logging=LoggingConfig(**d.get('logging', {}))
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global configuration manager instance
_config_manager = ConfigurationManager()


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager."""
    return _config_manager


def load_config(filepath: str) -> QuantumConfig:
    """
    Load configuration from file.

    Args:
        filepath: Path to configuration file

    Returns:
        Loaded configuration
    """
    manager = get_config_manager()
    manager.load_from_file(filepath)
    return manager.get_config()


def get_config() -> QuantumConfig:
    """Get current configuration."""
    return get_config_manager().get_config()


def set_config_value(path: str, value: Any) -> None:
    """Set configuration value."""
    get_config_manager().set(path, value)


def get_config_value(path: str, default: Any = None) -> Any:
    """Get configuration value."""
    return get_config_manager().get(path, default)


# Default configuration templates
DEFAULT_CONFIGS = {
    'minimal': QuantumConfig(
        agent=AgentConfig(num_qubits=5, max_iterations=100),
        training=TrainingConfig(epochs=10)
    ),
    'standard': QuantumConfig(),
    'advanced': QuantumConfig(
        agent=AgentConfig(num_qubits=50, use_error_correction=True),
        training=TrainingConfig(epochs=500, algorithm='quantum_sac'),
        circuit=CircuitConfig(max_depth=500, max_gates=10000)
    ),
    'research': QuantumConfig(
        agent=AgentConfig(num_qubits=100, use_error_correction=True, error_correction_code='steane'),
        training=TrainingConfig(epochs=1000, algorithm='quantum_ppo_adaptive'),
        circuit=CircuitConfig(max_depth=1000, max_gates=50000),
        logging=LoggingConfig(log_level='DEBUG', profiling_enabled=True)
    )
}


def apply_preset(preset_name: str) -> None:
    """
    Apply a configuration preset.

    Args:
        preset_name: Name of preset ('minimal', 'standard', 'advanced', 'research')
    """
    if preset_name not in DEFAULT_CONFIGS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(DEFAULT_CONFIGS.keys())}")

    manager = get_config_manager()
    preset = DEFAULT_CONFIGS[preset_name]

    manager.load_from_dict(asdict(preset), ConfigSource.CODE)
    logger.info(f"Applied configuration preset: {preset_name}")


if __name__ == "__main__":
    # Test configuration manager
    manager = get_config_manager()

    # Print default config
    print("Default configuration:")
    print(json.dumps(manager.get_config_dict(), indent=2))

    # Test getting/setting values
    print("\nTesting get/set:")
    print(f"num_qubits: {manager.get('agent.num_qubits')}")

    manager.set('agent.num_qubits', 30)
    print(f"After update: {manager.get('agent.num_qubits')}")

    # Test validation
    print("\nTesting validation:")
    try:
        manager.set('agent.learning_rate', -0.1)
    except ValueError as e:
        print(f"Validation error: {e}")

    # Test presets
    print("\nTesting presets:")
    apply_preset('advanced')
    print(f"Advanced preset num_qubits: {manager.get('agent.num_qubits')}")
