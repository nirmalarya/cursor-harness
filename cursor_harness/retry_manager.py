"""
Retry Manager
=============

Tracks retry attempts per feature to prevent infinite retry loops.
Implements 3-retry pattern matching claude-harness's proven approach.
"""

import json
from pathlib import Path
from typing import Dict


class RetryManager:
    """Tracks retry attempts per feature."""

    MAX_RETRIES = 3

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.retry_file = project_dir / ".cursor-harness" / "retry_state.json"
        self.retry_state: Dict[str, int] = self._load_state()

    def _load_state(self) -> Dict[str, int]:
        """Load retry state from disk."""
        if self.retry_file.exists():
            try:
                with open(self.retry_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_state(self):
        """Persist retry state to disk."""
        self.retry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.retry_file, "w") as f:
            json.dump(self.retry_state, f, indent=2)

    def can_retry(self, feature_id: str) -> bool:
        """
        Check if feature can be retried.

        Args:
            feature_id: Unique identifier for the feature

        Returns:
            True if attempts < MAX_RETRIES, False otherwise
        """
        attempts = self.retry_state.get(feature_id, 0)
        return attempts < self.MAX_RETRIES

    def record_attempt(self, feature_id: str):
        """
        Record a retry attempt.

        Args:
            feature_id: Unique identifier for the feature
        """
        self.retry_state[feature_id] = self.retry_state.get(feature_id, 0) + 1
        self._save_state()

    def reset_feature(self, feature_id: str):
        """
        Reset retry count (called on success).

        Args:
            feature_id: Unique identifier for the feature
        """
        if feature_id in self.retry_state:
            del self.retry_state[feature_id]
            self._save_state()

    def get_attempts(self, feature_id: str) -> int:
        """
        Get number of attempts for a feature.

        Args:
            feature_id: Unique identifier for the feature

        Returns:
            Number of attempts made (0 if never attempted)
        """
        return self.retry_state.get(feature_id, 0)

    def mark_skipped(self, feature_id: str):
        """
        Mark a feature as skipped (max retries exceeded).

        This is just a semantic wrapper for clarity in calling code.

        Args:
            feature_id: Unique identifier for the feature
        """
        # Feature is already tracked in retry_state, no additional action needed
        # The high retry count itself indicates it should be skipped
        pass
