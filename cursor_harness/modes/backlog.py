"""Backlog Mode - Process Azure DevOps work items."""

import json
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class PBI:
    id: str
    numeric_id: int
    title: str
    description: str
    acceptance_criteria: str
    processed: bool = False


class BacklogMode:
    """Backlog mode for processing Azure DevOps PBIs."""
    
    def __init__(self, project_dir: Path, org: str, project: str):
        self.project_dir = project_dir
        self.org = org
        self.project = project
        self.state_file = project_dir / ".cursor" / "backlog-state.json"
    
    def initialize(self):
        """Initialize backlog from Azure DevOps."""
        if not self.state_file.exists():
            print("   Fetching backlog from Azure DevOps...")
            # Will use MCP to fetch
            self._fetch_backlog()
    
    def _fetch_backlog(self):
        """Fetch backlog from Azure DevOps."""
        # Placeholder - will use mcp_azure-devops tools
        pbis = []
        self._save_state(pbis)
    
    def get_next_pbi(self) -> Optional[PBI]:
        """Get next unprocessed PBI."""
        pbis = self._load_state()
        for pbi in pbis:
            if not pbi.processed:
                return pbi
        return None
    
    def mark_processed(self, pbi_id: str):
        """Mark PBI as processed."""
        pbis = self._load_state()
        for pbi in pbis:
            if pbi.id == pbi_id:
                pbi.processed = True
        self._save_state(pbis)
    
    def is_complete(self) -> bool:
        """Check if all PBIs are processed."""
        pbis = self._load_state()
        return len(pbis) > 0 and all(p.processed for p in pbis)
    
    def _load_state(self) -> List[PBI]:
        """Load state from file."""
        if not self.state_file.exists():
            return []
        with open(self.state_file) as f:
            data = json.load(f)
        return [PBI(**item) for item in data.get('pbis', [])]
    
    def _save_state(self, pbis: List[PBI]):
        """Save state to file."""
        self.state_file.parent.mkdir(exist_ok=True, parents=True)
        data = {
            'org': self.org,
            'project': self.project,
            'pbis': [p.__dict__ for p in pbis]
        }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

