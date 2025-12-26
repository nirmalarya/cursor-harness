#!/usr/bin/env python3
"""
Multi-Agent Workflow Mode
=========================

Runs projects through multi-agent workflow:
Architect → Engineer → Tester → CodeReview → Security → DevOps
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class MultiAgentWorkflow:
    """Orchestrates multi-agent development workflow."""
    
    def __init__(self, project_dir: Path, project_name: str):
        self.project_dir = project_dir
        self.project_name = project_name
        # Simple: ONE workflow-state.json for current PBI
        self.state_file = project_dir / ".cursor" / "workflow-state.json"
        
        self.agents = [
            "architect",
            "engineer",
            "tester",
            "code_review",
            "security",
            "devops"
        ]
    
    def load_agent_prompt(self, agent: str, context: Dict) -> str:
        """Load agent-specific prompt with context."""
        
        prompt_file = Path(__file__).parent / "prompts" / "multi-agent" / f"{agent}_agent.md"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Agent prompt not found: {prompt_file}")
        
        # Read prompt
        prompt = prompt_file.read_text()
        
        # Replace placeholders with context
        prompt = prompt.replace("{{PROJECT_NAME}}", self.project_name)
        prompt = prompt.replace("{{project_name}}", self.project_name.lower())
        
        # Add PBI/feature context if available
        if "pbi_title" in context:
            prompt = f"""
# Current Work Item

**ID:** {context.get('pbi_id', 'N/A')}
**Title:** {context['pbi_title']}
**Type:** {context.get('pbi_type', 'Feature')}

**Description:**
{context.get('pbi_description', 'No description')}

**Acceptance Criteria:**
{context.get('acceptance_criteria', 'No acceptance criteria')}

---

{prompt}
"""
        
        return prompt
    
    def initialize_for_pbi(self, pbi_id: str, title: str):
        """
        Initialize/reset workflow state for a new PBI.
        
        CRITICAL: Call this when starting a NEW PBI to reset state!
        """
        initial_state = {
            "version": "1.1",
            "workItemId": pbi_id,
            "title": title,
            "currentAgent": "Architect",
            "completedAgents": [],  # Empty for new PBI!
            "checkpoints": [],
            "lastUpdated": datetime.now().isoformat()
        }
        
        self.save_workflow_state(initial_state)
        print(f"   ✅ Initialized workflow state for PBI {pbi_id}")
    
    def get_workflow_state(self) -> Dict:
        """Get current workflow state."""
        
        state_file = self.project_dir / ".cursor" / "workflow-state.json"
        
        if state_file.exists():
            return json.loads(state_file.read_text())
        
        # Initialize new state
        return {
            "version": "1.1",
            "currentAgent": None,
            "completedAgents": [],
            "workflowPath": self.agents,
            "checkpoints": []
        }
    
    def save_workflow_state(self, state: Dict):
        """Save workflow state."""
        
        state_dir = self.project_dir / ".cursor"
        state_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = state_dir / "workflow-state.json"
        state_file.write_text(json.dumps(state, indent=2))
    
    def get_next_agent(self) -> Optional[str]:
        """Get next agent to run based on workflow state."""
        
        state = self.get_workflow_state()
        completed = state.get('completedAgents', [])
        
        for agent in self.agents:
            if agent not in completed:
                return agent
        
        return None  # All agents complete!
    
    def mark_agent_complete(self, agent: str, artifacts: list, commit_sha: str, summary: str):
        """Mark agent as complete and save checkpoint."""
        
        state = self.get_workflow_state()
        
        state['completedAgents'].append(agent)
        state['checkpoints'].append({
            "agent": agent,
            "completedAt": datetime.now().isoformat(),
            "artifacts": artifacts,
            "commit": commit_sha,
            "summary": summary
        })
        
        self.save_workflow_state(state)
    
    def is_workflow_complete(self) -> bool:
        """Check if all agents have completed."""
        
        state = self.get_workflow_state()
        completed = set(state.get('completedAgents', []))
        required = set(self.agents)
        
        return completed >= required


# Integration with cursor_agent_runner.py

async def run_multi_agent_session(
    project_dir: Path,
    pbi_context: Dict,
    model: str,
) -> bool:
    """
    Run one PBI through complete multi-agent workflow.
    
    Args:
        project_dir: Project directory
        pbi_context: PBI information (id, title, description, etc.)
        model: Cursor model to use
    
    Returns:
        True if all agents passed, False otherwise
    """
    from cursor_agent_runner import run_autonomous_agent
    from datetime import datetime
    
    workflow = MultiAgentWorkflow(
        project_dir=project_dir,
        project_name=pbi_context.get('project_name', 'Project')
    )
    
    # Get next agent to run
    next_agent = workflow.get_next_agent()
    
    if not next_agent:
        print("✅ All agents complete for this PBI!")
        return True
    
    print(f"\n{'='*70}")
    print(f"  Running {next_agent.upper()} Agent")
    print(f"{'='*70}\n")
    
    # Load agent-specific prompt
    agent_prompt = workflow.load_agent_prompt(next_agent, pbi_context)
    
    # Run agent session with cursor harness
    # (This would integrate with cursor_agent_runner.py)
    
    # For now, placeholder
    print(f"Agent {next_agent} would run here with Cursor CLI...")
    
    # Mark complete (placeholder)
    # workflow.mark_agent_complete(next_agent, [], "commit-sha", "summary")
    
    return False  # Placeholder


if __name__ == "__main__":
    print("""
Multi-Agent Workflow Mode
=========================

This module provides multi-agent workflow orchestration.

Integration points:
1. cursor_autonomous_agent.py - Entry point, add --mode multi-agent
2. cursor_agent_runner.py - Execution, integrate agent prompts
3. Azure DevOps integration - Fetch PBIs, update status

See docs/MULTI_AGENT_WORKFLOW_MODE.md for design.
    """)

