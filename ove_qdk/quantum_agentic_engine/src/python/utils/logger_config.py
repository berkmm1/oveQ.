#!/usr/bin/env python3
"""
Logging Configuration for Quantum Agentic Engine
Structured logging with multiple handlers and formatters
"""

import logging
import logging.handlers
import json
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import traceback
from dataclasses import dataclass, asdict


@dataclass
class LogRecord:
    """Structured log record"""
    timestamp: str
    level: str
    logger: str
    message: str
    source: str
    line: int
    extra: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_record = LogRecord(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            source=record.filename,
            line=record.lineno,
            extra=getattr(record, 'extra', {})
        )
        return log_record.to_json()


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        formatted = f"{color}[{record.levelname}]{reset} {record.name}: {record.getMessage()}"

        if record.exc_info:
            formatted += f"\n{traceback.format_exception(*record.exc_info)}"

        return formatted


class QuantumAgentLogger:
    """Custom logger for quantum agentic engine"""

    def __init__(
        self,
        name: str = "quantum_agent",
        log_dir: str = "./logs",
        log_level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True,
        json_output: bool = False,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Clear existing handlers

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(ColoredFormatter())
            self.logger.addHandler(console_handler)

        # File handler
        if file_output:
            log_file = self.log_dir / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)

        # JSON handler
        if json_output:
            json_file = self.log_dir / f"{name}.jsonl"
            json_handler = logging.handlers.RotatingFileHandler(
                json_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            json_handler.setLevel(log_level)
            json_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(json_handler)

    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message"""
        self.logger.debug(message, extra={'extra': extra or {}})

    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message"""
        self.logger.info(message, extra={'extra': extra or {}})

    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message"""
        self.logger.warning(message, extra={'extra': extra or {}})

    def error(self, message: str, extra: Dict[str, Any] = None, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, extra={'extra': extra or {}}, exc_info=exc_info)

    def critical(self, message: str, extra: Dict[str, Any] = None, exc_info: bool = False):
        """Log critical message"""
        self.logger.critical(message, extra={'extra': extra or {}}, exc_info=exc_info)

    def log_metric(self, name: str, value: float, step: Optional[int] = None):
        """Log a metric"""
        extra = {'metric_name': name, 'metric_value': value}
        if step is not None:
            extra['step'] = step
        self.info(f"Metric: {name}={value}", extra=extra)

    def log_hyperparameters(self, params: Dict[str, Any]):
        """Log hyperparameters"""
        self.info(f"Hyperparameters: {json.dumps(params)}", extra={'hyperparameters': params})

    def log_model_info(self, model_info: Dict[str, Any]):
        """Log model information"""
        self.info(f"Model info: {json.dumps(model_info)}", extra={'model_info': model_info})

    def log_training_start(self, config: Dict[str, Any]):
        """Log training start"""
        self.info("=" * 80)
        self.info("TRAINING STARTED")
        self.info("=" * 80)
        self.log_hyperparameters(config)

    def log_training_end(self, metrics: Dict[str, Any]):
        """Log training end"""
        self.info("=" * 80)
        self.info("TRAINING COMPLETED")
        self.info("=" * 80)
        for key, value in metrics.items():
            self.info(f"  {key}: {value}")

    def log_episode(
        self,
        episode: int,
        reward: float,
        length: int,
        epsilon: float,
        loss: Optional[float] = None,
        q_value: Optional[float] = None
    ):
        """Log episode summary"""
        extra = {
            'episode': episode,
            'reward': reward,
            'length': length,
            'epsilon': epsilon
        }
        if loss is not None:
            extra['loss'] = loss
        if q_value is not None:
            extra['q_value'] = q_value

        self.info(
            f"Episode {episode}: reward={reward:.2f}, length={length}, epsilon={epsilon:.4f}",
            extra=extra
        )

    def log_evaluation(self, metrics: Dict[str, float]):
        """Log evaluation results"""
        self.info("=" * 80)
        self.info("EVALUATION RESULTS")
        self.info("=" * 80)
        for key, value in metrics.items():
            self.info(f"  {key}: {value:.4f}")

    def log_checkpoint(self, checkpoint_id: str, episode: int, metrics: Dict[str, float]):
        """Log checkpoint save"""
        self.info(
            f"Checkpoint saved: {checkpoint_id} at episode {episode}",
            extra={'checkpoint_id': checkpoint_id, 'episode': episode, 'metrics': metrics}
        )

    def log_quantum_operation(self, operation: str, qubits: int, duration_ms: float):
        """Log quantum operation"""
        self.debug(
            f"Quantum operation: {operation} ({qubits} qubits, {duration_ms:.2f} ms)",
            extra={'operation': operation, 'qubits': qubits, 'duration_ms': duration_ms}
        )


class LogAggregator:
    """Aggregate logs from multiple sources"""

    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.metrics: Dict[str, List[float]] = {}
        self.events: List[Dict[str, Any]] = []

    def add_metric(self, name: str, value: float, step: Optional[int] = None):
        """Add a metric value"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({'value': value, 'step': step})

    def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event"""
        self.events.append({
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })

    def get_metric_summary(self, name: str) -> Dict[str, float]:
        """Get summary statistics for a metric"""
        if name not in self.metrics:
            return {}

        values = [m['value'] for m in self.metrics[name]]
        return {
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'last': values[-1] if values else 0
        }

    def export_metrics(self, filepath: str):
        """Export metrics to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def export_events(self, filepath: str):
        """Export events to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.events, f, indent=2)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    console: bool = True,
    json_format: bool = False
) -> QuantumAgentLogger:
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    return QuantumAgentLogger(
        name="quantum_agent",
        log_dir=log_dir,
        log_level=level,
        console_output=console,
        json_output=json_format
    )


# Global logger instance
_global_logger: Optional[QuantumAgentLogger] = None


def get_logger() -> QuantumAgentLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logging()
    return _global_logger


def set_logger(logger: QuantumAgentLogger):
    """Set global logger instance"""
    global _global_logger
    _global_logger = logger


if __name__ == "__main__":
    # Test logging
    logger = setup_logging(log_level="DEBUG", json_format=True)

    logger.debug("Debug message", extra={'test': True})
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message", exc_info=False)

    logger.log_metric("reward", 50.0, step=100)
    logger.log_hyperparameters({'lr': 0.01, 'gamma': 0.99})

    logger.log_training_start({'episodes': 1000, 'batch_size': 32})
    logger.log_episode(100, 50.0, 200, 0.1, loss=0.5, q_value=2.5)
    logger.log_training_end({'best_reward': 100.0, 'total_time': 3600})

    # Test log aggregator
    aggregator = LogAggregator()
    aggregator.add_metric("reward", 50.0, step=1)
    aggregator.add_metric("reward", 60.0, step=2)
    aggregator.add_event("checkpoint", {'id': 'cp1'})

    summary = aggregator.get_metric_summary("reward")
    print(f"Metric summary: {summary}")

    print("Logging tests passed!")
