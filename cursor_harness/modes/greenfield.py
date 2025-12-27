"""
Greenfield Mode Adapter

Works with feature_list.json pattern:
[
  {"id": "1", "title": "...", "description": "...", "passing": false},
  {"id": "2", "title": "...", "description": "...", "passing": true},
  ...
]
"""

import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Feature:
    """A feature from feature_list.json."""
    id: str
    title: str
    description: str
    passing: bool
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Feature':
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            passing=data.get("passing", False)
        )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "passing": self.passing
        }


class GreenfieldMode:
    """
    Greenfield mode adapter.
    
    Manages feature_list.json workflow:
    - Load features from list
    - Return next non-passing feature
    - Mark features as passing when complete
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.feature_list_path = project_dir / "feature_list.json"
    
    def initialize(self):
        """Initialize feature list if it doesn't exist."""
        if not self.feature_list_path.exists():
            # Create empty list
            self._save_features([])
            print(f"   Created empty feature_list.json")
    
    def load_features(self) -> List[Feature]:
        """Load all features from feature_list.json."""
        if not self.feature_list_path.exists():
            return []
        
        with open(self.feature_list_path) as f:
            data = json.load(f)
        
        return [Feature.from_dict(item) for item in data]
    
    def get_next_feature(self) -> Optional[Feature]:
        """Get next non-passing feature."""
        features = self.load_features()
        
        for feature in features:
            if not feature.passing:
                return feature
        
        return None
    
    def mark_passing(self, feature_id: str):
        """Mark a feature as passing."""
        features = self.load_features()
        
        for feature in features:
            if feature.id == feature_id:
                feature.passing = True
                break
        
        self._save_features(features)
    
    def mark_failing(self, feature_id: str):
        """Mark a feature as failing."""
        features = self.load_features()
        
        for feature in features:
            if feature.id == feature_id:
                feature.passing = False
                break
        
        self._save_features(features)
    
    def is_complete(self) -> bool:
        """Check if all features are passing."""
        features = self.load_features()
        
        if not features:
            return True  # Empty list = complete
        
        return all(f.passing for f in features)
    
    def get_progress(self) -> dict:
        """Get progress statistics."""
        features = self.load_features()
        
        total = len(features)
        passing = sum(1 for f in features if f.passing)
        
        return {
            "total": total,
            "passing": passing,
            "remaining": total - passing,
            "percentage": (passing / total * 100) if total > 0 else 0
        }
    
    def _save_features(self, features: List[Feature]):
        """Save features to feature_list.json."""
        data = [f.to_dict() for f in features]
        
        with open(self.feature_list_path, 'w') as f:
            json.dump(data, f, indent=2)

