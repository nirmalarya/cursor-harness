#!/usr/bin/env python3
"""
Autonomous Backlog Runner
=========================

Runs continuous backlog processing from Azure DevOps.
"""

import asyncio
from pathlib import Path
from typing import Optional

from azure_devops_integration import AzureDevOpsIntegration
from multi_agent_mode import MultiAgentWorkflow
from cursor_agent_runner import run_autonomous_agent


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
            pbi=pbi,
            spec_file=spec_file,
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
    Run special fetcher session to get next PBI via Azure DevOps MCP.
    
    Returns:
        Dict with pbi_id and spec_file path, or None if no PBIs
    """
    # TODO: Run actual Cursor session with azure_devops_fetcher_prompt.md
    # The agent will use MCP tools to query and fetch PBI
    # For now, return None (placeholder)
    return None


async def run_multi_agent_workflow_for_pbi(
    project_dir: Path,
    model: str,
    pbi_id: str,
    spec_file: Path,
) -> bool:
    """
    Run complete multi-agent workflow for one PBI.
    
    RESPECTS ANTHROPIC HARNESS PATTERN:
    - Each agent runs FULL harness (initializer + coders)
    - NOT just one session per agent!
    """
    
    agents = ["architect", "engineer", "tester", "code_review", "security", "devops"]
    
    # Create PBI context
    pbi_context = {
        "project_name": ado.project,
        "pbi_id": pbi['id'],
        "pbi_title": pbi['fields']['System.Title'],
        "pbi_type": pbi['fields']['System.WorkItemType'],
        "pbi_description": pbi['fields'].get('System.Description', ''),
        "acceptance_criteria": pbi['fields'].get('Microsoft.VSTS.Common.AcceptanceCriteria', '')
    }
    
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
        from cursor_agent_runner import run_autonomous_agent
        
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
            commit_sha=get_latest_commit(),
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

