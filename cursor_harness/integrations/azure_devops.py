"""Azure DevOps integration for backlog mode."""

import json
from pathlib import Path
from typing import List, Dict, Optional


class AzureDevOpsIntegration:
    """
    Fetch and update Azure DevOps work items.
    
    Uses MCP tools if available, otherwise returns empty state.
    """
    
    def __init__(self, org: str, project: str, project_dir: Path):
        self.org = org
        self.project = project
        self.project_dir = project_dir
        self.state_file = project_dir / ".cursor" / "backlog-state.json"
    
    def fetch_pbis(self) -> List[Dict]:
        """
        Fetch PBIs from Azure DevOps.
        
        Returns list of PBIs in format:
        [
          {
            "id": "PBI-3.6.1",
            "numeric_id": 16750,
            "title": "Add flag description",
            "description": "...",
            "acceptance_criteria": "...",
            "processed": false
          }
        ]
        """
        
        # Try to use MCP
        try:
            # This will be called by the agent using MCP tools
            # For now, return empty if MCP not available
            print(f"   ℹ️  Azure DevOps MCP not available")
            print(f"   Agent will need to fetch PBIs manually using MCP tools")
            return []
        except:
            return []
    
    def save_backlog_state(self, pbis: List[Dict]):
        """Save backlog state to file."""
        
        self.state_file.parent.mkdir(exist_ok=True, parents=True)
        
        data = {
            "org": self.org,
            "project": self.project,
            "pbis": pbis
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_backlog_state(self) -> Dict:
        """Load backlog state from file."""
        
        if not self.state_file.exists():
            return {"org": self.org, "project": self.project, "pbis": []}
        
        with open(self.state_file) as f:
            return json.load(f)
    
    def update_work_item(self, pbi_id: str, comment: str):
        """
        Update Azure DevOps work item.
        
        Agent will use MCP tools for this.
        This is just a placeholder.
        """
        print(f"   ℹ️  Update {pbi_id}: {comment[:50]}...")

