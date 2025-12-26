#!/usr/bin/env python3
"""
Autonomous Backlog Runner
=========================

Runs continuous backlog processing from Azure DevOps.
"""

import asyncio
from pathlib import Path
from typing import Optional

from .azure_devops_integration import AzureDevOpsIntegration
from .multi_agent_mode import MultiAgentWorkflow
from .cursor_agent_runner import run_autonomous_agent
import subprocess


async def run_autonomous_backlog(
    project_dir: Path,
    model: str,
    azure_devops_org: str,
    azure_devops_project: str,
    epic: Optional[str] = None,
    max_pbis: Optional[int] = None,
):
    """
    Run autonomous backlog processing.
    
    Continuously pulls PBIs from Azure DevOps and implements them.
    """
    
    print("\n" + "="*70)
    print("  AUTONOMOUS BACKLOG MODE")
    print("  Continuous PBI Processing from Azure DevOps")
    print("="*70)
    print(f"\nOrganization: {azure_devops_org}")
    print(f"Project: {azure_devops_project}")
    if epic:
        print(f"Epic filter: {epic}")
    if max_pbis:
        print(f"Max PBIs: {max_pbis}")
    else:
        print("Max PBIs: Unlimited (runs until backlog empty)")
    print("\n" + "="*70 + "\n")
    
    # Initialize integrations
    ado = AzureDevOpsIntegration(azure_devops_org, azure_devops_project)
    
    pbis_completed = 0
    
    while True:
        # 1. FETCH SESSION: Query Azure DevOps and create spec
        print("\n🔍 Running Azure DevOps Fetcher Session...")
        print("   (This uses MCP tools to fetch next PBI)\n")
        
        # Run a special fetcher session that uses Azure DevOps MCP
        # The agent will use mcp_azure-devops tools to query and fetch
        fetcher_result = await run_fetcher_session(
            project_dir=project_dir,
            model=model,
            epic=epic,
            ado_project=azure_devops_project,
            ado_org=azure_devops_org
        )
        
        if not fetcher_result or not fetcher_result.get('pbi_id'):
            print("\n✅ No more PBIs in backlog!")
            
            if max_pbis is None:
                print("⏰ Waiting 1 hour before checking again...")
                await asyncio.sleep(3600)
                continue
            else:
                print(f"✅ Completed {pbis_completed} PBIs")
                return
        
        pbi_id = fetcher_result['pbi_id']
        spec_file = project_dir / "spec" / f"{pbi_id}_spec.txt"
        
        print(f"\n✅ PBI fetched: {pbi_id}")
        print(f"✅ Spec created: {spec_file}\n")
        
        # 4. Run multi-agent workflow
        print("🚀 Starting multi-agent workflow...\n")
        
        success = await run_multi_agent_workflow_for_pbi(
            project_dir=project_dir,
            model=model,
            pbi_id=fetcher_result['pbi_id'],
            spec_file=fetcher_result['spec_file'],
            ado=ado
        )
        
        if success:
            # 5. Mark as Done
            ado.mark_done(pbi['id'])
            
            pbis_completed += 1
            print(f"\n🎉 {pbi['id']} COMPLETE!")
            print(f"   Total: {pbis_completed}/{max_pbis or '∞'}\n")
            
            # Check limit
            if max_pbis and pbis_completed >= max_pbis:
                print(f"✅ Reached limit ({max_pbis} PBIs)")
                return
            
            # Continue to next
            print("⏭️  Moving to next PBI in 10 seconds...\n")
            await asyncio.sleep(10)
        else:
            print(f"\n❌ {pbi['id']} FAILED!")
            print("Stopping for human intervention\n")
            return


async def run_fetcher_session(
    project_dir: Path,
    model: str,
    epic: Optional[str],
    ado_project: str,
    ado_org: str
) -> Optional[Dict]:
    """
    Fetch next PBI from Azure DevOps using REST API.
    
    Returns:
        Dict with pbi_id and spec_file path, or None if no PBIs
    """
    print("  Fetching next PBI from Azure DevOps REST API...")
    
    # Use REST API directly (no MCP needed!)
    from .azure_devops_integration import AzureDevOpsIntegration
    
    ado = AzureDevOpsIntegration(ado_org, ado_project)
    
    # Query for next New PBI
    print(f"  Querying for 'New' PBIs{' in ' + epic if epic else ''}...")
    pbi_id = ado.get_next_new_pbi(epic=epic)
    
    if not pbi_id:
        print("  ❌ No 'New' PBIs found in backlog")
        return None
    
    # Fetch full work item details
    print(f"  📋 Fetching work item {pbi_id}...")
    work_item = ado.get_work_item(pbi_id)
    
    if not work_item:
        print(f"  ❌ Failed to fetch work item {pbi_id}")
        return None
    
    # Convert to spec format
    spec_content = ado.convert_to_spec(work_item)
    
    # Save spec file
    spec_dir = project_dir / "spec"
    spec_dir.mkdir(exist_ok=True)
    
    spec_file = spec_dir / f"{pbi_id}_spec.txt"
    spec_file.write_text(spec_content)
    
    print(f"  ✅ Created spec: {spec_file}")
    
    # Commit spec file
    import subprocess
    subprocess.run(["git", "add", str(spec_file)], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"spec: Add specification for work item {pbi_id}"],
        cwd=project_dir,
        capture_output=True
    )
    
    print(f"  ✅ Committed spec file")
    
    return {
        'pbi_id': str(pbi_id),
        'spec_file': str(spec_file)
    }


async def run_fetcher_session_OLD_MCP_VERSION(
    project_dir: Path,
    model: str,
    epic: Optional[str],
    ado_project: str,
    ado_org: str
) -> Optional[Dict]:
    """
    DEPRECATED: Old MCP-based fetcher (doesn't work in CLI).
    Kept for reference.
    """
    from .cursor_mcp_client import CursorMCPClient
    
    print("  Running Azure DevOps Fetcher Session...")
    print("  (Agent will use MCP tools to fetch next PBI)\n")
    
    # Load fetcher prompt
    prompt_file = Path(__file__).parent / "prompts" / "azure_devops_fetcher_prompt.md"
    fetcher_prompt = prompt_file.read_text()
    
    # Replace placeholders
    fetcher_prompt = fetcher_prompt.replace("{{PROJECT_NAME}}", ado_project)
    fetcher_prompt = fetcher_prompt.replace("{{ORGANIZATION}}", ado_org)
    fetcher_prompt = fetcher_prompt.replace("{{EPIC}}", epic or "Any")
    
    # Add query instructions
    if epic:
        query_instruction = f"""
## Query to Run

Use Azure DevOps MCP to query for next work item:

```
Use mcp_azure-devops_search_workitem with:
- searchText: "{epic}"
- project: ["{ado_project}"]
- state: ["New"]
- top: 1

This will return PBIs in Epic {epic} that are "New" (not started).
Get the first one and fetch its details with mcp_azure-devops_wit_get_work_item.
```
"""
    else:
        # No epic filter - query all "New" PBIs
        query_instruction = f"""
## Query to Run

Use Azure DevOps MCP to query for next work item:

```
Use mcp_azure-devops_search_workitem with:
- searchText: ""  (empty - return all)
- project: ["{ado_project}"]
- state: ["New"]
- top: 1

This will return the first PBI that is "New" (not started).
Get its ID and fetch full details with mcp_azure-devops_wit_get_work_item.
```
"""
    
    fetcher_prompt = fetcher_prompt.replace("{{WORK_ITEM_ID}}", "QUERY_RESULT")
    fetcher_prompt = query_instruction + "\n" + fetcher_prompt
    
    # Create client - cursor-agent auto-loads MCPs
    client = CursorMCPClient(
        project_dir=project_dir,
        model=model
    )
    
    # Run fetcher session
    try:
        await client.run_session(fetcher_prompt)
    except Exception as e:
        print(f"❌ Fetcher session failed: {e}")
        return None
    
    # Check if spec file was created
    spec_dir = project_dir / "spec"
    if spec_dir.exists():
        spec_files = list(spec_dir.glob("*_spec.txt"))
        if spec_files:
            # Get most recently created spec
            latest_spec = max(spec_files, key=lambda p: p.stat().st_mtime)
            pbi_id = latest_spec.stem.replace("_spec", "")
            
            print(f"✅ Fetcher session complete!")
            print(f"   PBI ID: {pbi_id}")
            print(f"   Spec: {latest_spec}\n")
            
            return {
                "pbi_id": pbi_id,
                "spec_file": latest_spec
            }
    
    print("❌ No spec file created - no PBIs found or fetch failed\n")
    return None


async def create_agent_spec(
    project_dir: Path,
    pbi_spec_file: Path,
    agent: str,
    model: str
) -> Path:
    """
    Create agent-specific spec combining PBI requirements + agent rules.
    
    Returns:
        Path to agent-specific spec file
    """
    # Read PBI spec
    pbi_spec = pbi_spec_file.read_text()
    
    # Load agent rules
    agent_rules_file = Path(__file__).parent / "prompts" / "multi-agent" / f"{agent}_agent.md"
    
    if not agent_rules_file.exists():
        print(f"⚠️  Agent rules not found: {agent_rules_file}")
        print(f"   Using PBI spec only\n")
        return pbi_spec_file
    
    agent_rules = agent_rules_file.read_text()
    
    # Get workflow state (which agents completed)
    workflow = MultiAgentWorkflow(project_dir, "{{PROJECT}}")
    state = workflow.get_workflow_state()
    completed_agents = state.get('completedAgents', [])
    
    # Combine into agent-specific spec
    agent_spec = f"""{pbi_spec}

---

# {agent.upper()} AGENT - YOUR ROLE

{agent_rules}

---

# Multi-Agent Workflow Context

**Your agent:** {agent.upper()}
**Completed agents:** {', '.join([a.title() for a in completed_agents]) if completed_agents else 'None (you are first)'}
**Remaining agents:** {', '.join([a.title() for a in ['architect', 'engineer', 'tester', 'code_review', 'security', 'devops'] if a not in completed_agents and a != agent])}

**Your task:** Generate feature_list.json for {agent.upper()} agent tasks ONLY!

Do NOT implement other agents' work. Focus on YOUR agent responsibilities.

When you complete all your tasks (100%), the workflow will move to the next agent.

---

# Task Breakdown Guidance for {agent.upper()}

Based on the PBI requirements above and your agent role, break down YOUR work into features.

Example feature_list.json for {agent.upper()}:
- If Architect: Design tasks, research, API contracts, ADR creation
- If Engineer: Test tasks (RED), implementation tasks (GREEN), refactoring (REFACTOR)
- If Tester: Unit test verification, E2E test creation, coverage check, grading
- If CodeReview: Linting, naming conventions, code quality checks
- If Security: OWASP review, dependency scan, vulnerability check
- If DevOps: Build verification, smoke testing, deployment readiness

Generate appropriate features for YOUR agent!
"""
    
    # Save agent-specific spec
    agent_spec_file = project_dir / "spec" / f"{agent}_agent_spec.txt"
    agent_spec_file.write_text(agent_spec)
    
    print(f"✅ Agent spec created: {agent_spec_file}")
    print(f"   Combines: PBI requirements + {agent} agent rules\n")
    
    return agent_spec_file


async def run_multi_agent_workflow_for_pbi(
    project_dir: Path,
    model: str,
    pbi_id: str,
    spec_file: Path,
    ado: 'AzureDevOpsIntegration'
) -> bool:
    """
    Run complete multi-agent workflow for one PBI.
    
    RESPECTS ANTHROPIC HARNESS PATTERN:
    - Each agent runs FULL harness (initializer + coders)
    - NOT just one session per agent!
    """
    
    agents = ["architect", "engineer", "tester", "code_review", "security", "devops"]
    
    # For now, use the spec file - the PBI was already fetched by the fetcher session
    # In the future, we can fetch from Azure DevOps directly here
    print(f"📋 Using PBI details from spec file: {pbi_id}...")
    
    # Create minimal PBI object from spec (spec already has all the info)
    pbi = {
        'id': pbi_id,
        'fields': {
            'System.Title': pbi_id,  # Will be populated from spec
            'System.WorkItemType': 'PBI',
            'System.Description': f"See {spec_file}",
            'Microsoft.VSTS.Common.AcceptanceCriteria': f"See {spec_file}"
        }
    }
    
    # Create PBI context
    pbi_context = {
        "project_name": ado.project,
        "pbi_id": pbi['id'],
        "pbi_title": pbi['fields']['System.Title'],
        "pbi_type": pbi['fields']['System.WorkItemType'],
        "pbi_description": pbi['fields'].get('System.Description', ''),
        "acceptance_criteria": pbi['fields'].get('Microsoft.VSTS.Common.AcceptanceCriteria', '')
    }
    
    # Initialize workflow manager
    workflow = MultiAgentWorkflow(project_dir, pbi_id)
    
    # Check if workflow already started (resume capability)
    current_state = workflow.get_workflow_state()
    completed_agents = current_state.get('completedAgents', [])
    
    for agent in agents:
        # Skip if already completed
        if agent in completed_agents:
            print(f"⏩ {agent.title()} already complete, skipping...\n")
            continue
        
        print(f"\n{'═'*70}")
        print(f"  🤖 {agent.upper()} AGENT - STARTING FULL HARNESS")
        print(f"{'═'*70}\n")
        
        # Create agent-specific spec (combines PBI + agent rules)
        agent_spec_file = await create_agent_spec(
            project_dir=project_dir,
            pbi_spec_file=spec_file,
            agent=agent,
            model=model
        )
        
        print(f"Running {agent} through FULL harness pattern:")
        print(f"  Session 1: Initializer (plan {agent} tasks)")
        print(f"  Session 2+: Coder (implement tasks)")
        print(f"  Stops automatically when agent tasks complete\n")
        
        # Run FULL autonomous harness for this agent!
        # This respects the Anthropic pattern (initializer + coders)
        from .cursor_agent_runner import run_autonomous_agent
        
        await run_autonomous_agent(
            project_dir=project_dir,
            model=model,
            max_iterations=50,  # Allow multiple sessions per agent
            mode="enhancement",  # Agent enhances existing project
            spec_file=str(agent_spec_file),
        )
        
        # Agent completed (stopped at 100% automatically)
        print(f"\n✅ {agent.upper()} agent complete!\n")
        
        # TODO: Update Azure DevOps via MCP
        # Would use mcp_azure-devops_wit_add_work_item_comment
        
        # Save checkpoint
        workflow.mark_agent_complete(
            agent=agent,
            artifacts=[],  # Would get from agent output
            commit_sha=get_latest_commit(project_dir),
            summary=f"{agent.title()} completed via autonomous harness"
        )
    
    # All agents complete
    return True


if __name__ == "__main__":
    print("""
Autonomous Backlog Runner
=========================

Usage:
  python3 cursor_autonomous_agent.py \\
    --mode autonomous-backlog \\
    --azure-devops-project togglr \\
    --epic Epic-3 \\
    --max-pbis 5

This will process 5 PBIs from Epic-3 continuously!
    """)

