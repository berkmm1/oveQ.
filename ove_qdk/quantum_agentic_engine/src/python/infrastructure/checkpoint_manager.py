#!/usr/bin/env python3
"""
Checkpoint Manager for Quantum Agentic Engine
Handles model saving, loading, and versioning
"""

import json
import pickle
import gzip
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class CheckpointMetadata:
    """Metadata for a checkpoint"""

    def __init__(
        self,
        checkpoint_id: str,
        episode: int,
        timestamp: str,
        metrics: Dict[str, float],
        config: Dict[str, Any],
        file_size: int = 0
    ):
        self.checkpoint_id = checkpoint_id
        self.episode = episode
        self.timestamp = timestamp
        self.metrics = metrics
        self.config = config
        self.file_size = file_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            'checkpoint_id': self.checkpoint_id,
            'episode': self.episode,
            'timestamp': self.timestamp,
            'metrics': self.metrics,
            'config': self.config,
            'file_size': self.file_size
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointMetadata':
        return cls(**data)


class CheckpointManager:
    """Manage training checkpoints"""

    def __init__(
        self,
        checkpoint_dir: str = "./checkpoints",
        max_checkpoints: int = 10,
        compress: bool = True,
        keep_best: bool = True
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = max_checkpoints
        self.compress = compress
        self.keep_best = keep_best

        self.metadata_file = self.checkpoint_dir / "checkpoint_index.json"
        self.checkpoints: List[CheckpointMetadata] = []
        self.best_checkpoint_id: Optional[str] = None

        self._load_index()

    def _load_index(self):
        """Load checkpoint index"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                self.checkpoints = [
                    CheckpointMetadata.from_dict(c) for c in data.get('checkpoints', [])
                ]
                self.best_checkpoint_id = data.get('best_checkpoint_id')

    def _save_index(self):
        """Save checkpoint index"""
        data = {
            'checkpoints': [c.to_dict() for c in self.checkpoints],
            'best_checkpoint_id': self.best_checkpoint_id
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _generate_id(self, episode: int) -> str:
        """Generate unique checkpoint ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"checkpoint_ep{episode}_{timestamp}"

    def save_checkpoint(
        self,
        episode: int,
        state: Dict[str, Any],
        metrics: Dict[str, float],
        config: Dict[str, Any],
        is_best: bool = False
    ) -> str:
        """Save a checkpoint"""
        checkpoint_id = self._generate_id(episode)

        # Prepare checkpoint data
        checkpoint_data = {
            'checkpoint_id': checkpoint_id,
            'episode': episode,
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'metrics': metrics,
            'config': config
        }

        # Save checkpoint file
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pkl"

        if self.compress:
            checkpoint_path = checkpoint_path.with_suffix('.pkl.gz')
            with gzip.open(checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)
        else:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)

        # Get file size
        file_size = checkpoint_path.stat().st_size

        # Create metadata
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            episode=episode,
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            config=config,
            file_size=file_size
        )

        # Add to index
        self.checkpoints.append(metadata)

        # Update best checkpoint
        if is_best or self.best_checkpoint_id is None:
            self.best_checkpoint_id = checkpoint_id
            # Create symlink to best
            best_path = self.checkpoint_dir / "best_checkpoint.pkl"
            if best_path.exists() or best_path.is_symlink():
                best_path.unlink()
            shutil.copy(checkpoint_path, best_path)

        # Clean old checkpoints
        self._cleanup_checkpoints()

        # Save index
        self._save_index()

        logger.info(f"Checkpoint saved: {checkpoint_id} ({file_size / 1024:.1f} KB)")

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """Load a checkpoint"""
        if checkpoint_id is None:
            checkpoint_id = self.best_checkpoint_id

        if checkpoint_id is None:
            raise ValueError("No checkpoint available")

        # Find checkpoint file
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pkl"
        if not checkpoint_path.exists():
            checkpoint_path = checkpoint_path.with_suffix('.pkl.gz')

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        # Load checkpoint
        if checkpoint_path.suffix == '.gz':
            with gzip.open(checkpoint_path, 'rb') as f:
                checkpoint_data = pickle.load(f)
        else:
            with open(checkpoint_path, 'rb') as f:
                checkpoint_data = pickle.load(f)

        logger.info(f"Checkpoint loaded: {checkpoint_id}")

        return checkpoint_data

    def _cleanup_checkpoints(self):
        """Remove old checkpoints"""
        if len(self.checkpoints) <= self.max_checkpoints:
            return

        # Sort by episode
        sorted_checkpoints = sorted(self.checkpoints, key=lambda c: c.episode)

        # Keep best checkpoint
        to_remove = sorted_checkpoints[:-self.max_checkpoints]

        for checkpoint in to_remove:
            if checkpoint.checkpoint_id == self.best_checkpoint_id and self.keep_best:
                continue

            # Remove file
            checkpoint_path = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.pkl"
            if not checkpoint_path.exists():
                checkpoint_path = checkpoint_path.with_suffix('.pkl.gz')

            if checkpoint_path.exists():
                checkpoint_path.unlink()
                logger.debug(f"Removed old checkpoint: {checkpoint.checkpoint_id}")

            # Remove from index
            self.checkpoints.remove(checkpoint)

    def list_checkpoints(self) -> List[CheckpointMetadata]:
        """List all checkpoints"""
        return sorted(self.checkpoints, key=lambda c: c.episode, reverse=True)

    def get_best_checkpoint(self) -> Optional[CheckpointMetadata]:
        """Get best checkpoint metadata"""
        if self.best_checkpoint_id is None:
            return None

        for checkpoint in self.checkpoints:
            if checkpoint.checkpoint_id == self.best_checkpoint_id:
                return checkpoint

        return None

    def delete_checkpoint(self, checkpoint_id: str):
        """Delete a checkpoint"""
        # Find and remove from index
        for checkpoint in self.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                # Remove file
                checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pkl"
                if not checkpoint_path.exists():
                    checkpoint_path = checkpoint_path.with_suffix('.pkl.gz')

                if checkpoint_path.exists():
                    checkpoint_path.unlink()

                self.checkpoints.remove(checkpoint)

                # Update best if needed
                if self.best_checkpoint_id == checkpoint_id:
                    if self.checkpoints:
                        self.best_checkpoint_id = self.checkpoints[-1].checkpoint_id
                    else:
                        self.best_checkpoint_id = None

                self._save_index()
                logger.info(f"Checkpoint deleted: {checkpoint_id}")
                return

        raise ValueError(f"Checkpoint not found: {checkpoint_id}")

    def export_checkpoint(
        self,
        checkpoint_id: str,
        export_path: str,
        include_metadata: bool = True
    ):
        """Export checkpoint to external location"""
        checkpoint_data = self.load_checkpoint(checkpoint_id)

        export_path = Path(export_path)

        if include_metadata:
            # Export with metadata
            with open(export_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)
        else:
            # Export state only
            with open(export_path, 'wb') as f:
                pickle.dump(checkpoint_data['state'], f)

        logger.info(f"Checkpoint exported: {export_path}")

    def import_checkpoint(self, import_path: str) -> str:
        """Import checkpoint from external location"""
        import_path = Path(import_path)

        with open(import_path, 'rb') as f:
            checkpoint_data = pickle.load(f)

        # Generate new ID
        checkpoint_id = self._generate_id(checkpoint_data.get('episode', 0))
        checkpoint_data['checkpoint_id'] = checkpoint_id

        # Save to checkpoint directory
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pkl"

        if self.compress:
            checkpoint_path = checkpoint_path.with_suffix('.pkl.gz')
            with gzip.open(checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)
        else:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint_data, f)

        # Add to index
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            episode=checkpoint_data.get('episode', 0),
            timestamp=checkpoint_data.get('timestamp', datetime.now().isoformat()),
            metrics=checkpoint_data.get('metrics', {}),
            config=checkpoint_data.get('config', {}),
            file_size=checkpoint_path.stat().st_size
        )

        self.checkpoints.append(metadata)
        self._save_index()

        logger.info(f"Checkpoint imported: {checkpoint_id}")

        return checkpoint_id

    def get_checkpoint_hash(self, checkpoint_id: str) -> str:
        """Get MD5 hash of checkpoint file"""
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pkl"
        if not checkpoint_path.exists():
            checkpoint_path = checkpoint_path.with_suffix('.pkl.gz')

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        hasher = hashlib.md5()
        with open(checkpoint_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

    def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """Verify checkpoint integrity"""
        try:
            checkpoint_data = self.load_checkpoint(checkpoint_id)
            return checkpoint_data.get('checkpoint_id') == checkpoint_id
        except Exception as e:
            logger.error(f"Checkpoint verification failed: {e}")
            return False


class ModelVersioning:
    """Version control for trained models"""

    def __init__(self, versions_dir: str = "./model_versions"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.versions_dir / "versions.json"
        self.versions: Dict[str, Dict[str, Any]] = {}

        self._load_versions()

    def _load_versions(self):
        """Load version history"""
        if self.versions_file.exists():
            with open(self.versions_file, 'r') as f:
                self.versions = json.load(f)

    def _save_versions(self):
        """Save version history"""
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions, f, indent=2)

    def create_version(
        self,
        model_path: str,
        version: str,
        description: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Create a new model version"""
        version_path = self.versions_dir / f"v{version}"
        version_path.mkdir(exist_ok=True)

        # Copy model
        model_file = version_path / "model.pkl"
        shutil.copy(model_path, model_file)

        # Save version info
        version_info = {
            'version': version,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'tags': tags or [],
            'metadata': metadata or {},
            'model_file': str(model_file)
        }

        self.versions[version] = version_info
        self._save_versions()

        logger.info(f"Model version created: {version}")

    def get_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get version information"""
        return self.versions.get(version)

    def list_versions(self) -> List[Dict[str, Any]]:
        """List all versions"""
        return sorted(
            self.versions.values(),
            key=lambda v: v['timestamp'],
            reverse=True
        )

    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions"""
        v1 = self.versions.get(version1)
        v2 = self.versions.get(version2)

        if v1 is None or v2 is None:
            raise ValueError("Version not found")

        return {
            'version1': v1,
            'version2': v2,
            'differences': {
                k: (v1.get(k), v2.get(k))
                for k in set(v1.keys()) | set(v2.keys())
                if v1.get(k) != v2.get(k)
            }
        }


if __name__ == "__main__":
    # Test checkpoint manager
    manager = CheckpointManager(checkpoint_dir="./test_checkpoints")

    # Save test checkpoint
    state = {'params': [1.0, 2.0, 3.0], 'episode': 100}
    metrics = {'reward': 50.0, 'loss': 0.1}
    config = {'learning_rate': 0.01}

    checkpoint_id = manager.save_checkpoint(
        episode=100,
        state=state,
        metrics=metrics,
        config=config,
        is_best=True
    )

    # List checkpoints
    checkpoints = manager.list_checkpoints()
    print(f"Checkpoints: {len(checkpoints)}")

    # Load checkpoint
    loaded = manager.load_checkpoint(checkpoint_id)
    print(f"Loaded episode: {loaded['episode']}")

    # Test model versioning
    versioning = ModelVersioning(versions_dir="./test_versions")

    # Create version
    versioning.create_version(
        model_path=f"./test_checkpoints/{checkpoint_id}.pkl.gz",
        version="1.0.0",
        description="Initial model",
        tags=["baseline", "v1"]
    )

    # List versions
    versions = versioning.list_versions()
    print(f"Versions: {len(versions)}")

    print("Tests passed!")
