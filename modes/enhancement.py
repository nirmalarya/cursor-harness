"""Enhancement Mode - Add features to existing projects."""

import json
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Enhancement:
    id: str
    title: str
    description: str
    completed: bool = False


class EnhancementMode:
    """Enhancement mode for adding features to existing projects."""
    
    def __init__(self, project_dir: Path, spec_file: Path):
        self.project_dir = project_dir
        self.spec_file = spec_file
        self.state_file = project_dir / ".cursor" / "enhancement-state.json"
    
    def initialize(self):
        """Initialize from spec file."""
        if not self.state_file.exists():
            enhancements = self._parse_spec()
            self._save_state(enhancements)
    
    def _parse_spec(self) -> List[Enhancement]:
        """Parse enhancements from spec file."""
        spec_text = self.spec_file.read_text()
        # Simple parsing - look for numbered items
        enhancements = []
        lines = spec_text.split('\n')
        current_id = 1
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                title = line[2:].strip()
                if title:
                    enhancements.append(Enhancement(
                        id=str(current_id),
                        title=title,
                        description=title,
                        completed=False
                    ))
                    current_id += 1
        
        return enhancements
    
    def get_next_enhancement(self) -> Optional[Enhancement]:
        """Get next incomplete enhancement."""
        enhancements = self._load_state()
        for enh in enhancements:
            if not enh.completed:
                return enh
        return None
    
    def mark_complete(self, enhancement_id: str):
        """Mark enhancement as complete."""
        enhancements = self._load_state()
        for enh in enhancements:
            if enh.id == enhancement_id:
                enh.completed = True
        self._save_state(enhancements)
    
    def is_complete(self) -> bool:
        """Check if all enhancements are complete."""
        enhancements = self._load_state()
        return all(e.completed for e in enhancements)
    
    def _load_state(self) -> List[Enhancement]:
        """Load state from file."""
        if not self.state_file.exists():
            return []
        with open(self.state_file) as f:
            data = json.load(f)
        return [Enhancement(**item) for item in data]
    
    def _save_state(self, enhancements: List[Enhancement]):
        """Save state to file."""
        self.state_file.parent.mkdir(exist_ok=True, parents=True)
        data = [e.__dict__ for e in enhancements]
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

