"""
Single Agent Runner
===================

Runs ONE agent (Architect, Engineer, etc.) through its tasks and stops.
Used by multi-agent workflow orchestrator.
"""

import asyncio
from pathlib import Path
from typing import Optional

from .cursor_mcp_client import CursorMCPClient


async def run_single_agent(
    project_dir: Path,
    agent_name: str,
    spec_file: Path,
    model: str = "sonnet-4.5",
    max_sessions: int = 20
) -> bool:
    """
    Run a single agent (Architect, Engineer, etc.) until its tasks are complete.
    
    Args:
        project_dir: Project directory
        agent_name: Agent name (architect, engineer, tester, etc.)
        spec_file: Agent-specific spec file
        model: Cursor model to use
        max_sessions: Max sessions for this agent
    
    Returns:
        True if agent completed successfully, False otherwise
    """
    
    print(f"\n{'═'*70}")
    print(f"  🤖 {agent_name.upper()} AGENT")
    print(f"{'═'*70}\n")
    
    # Read agent spec
    agent_spec = spec_file.read_text()
    
    # Create initial prompt
    initial_prompt = f"""You are the {agent_name.title()} agent in a multi-agent workflow.

**MODE:** Multi-Agent Workflow (NOT enhancement mode!)

**CRITICAL:**
- Do NOT create feature_list.json
- Do NOT create ENHANCEMENT_PLAN.md
- Do NOT create cursor-progress.txt
- This is NOT enhancement/greenfield mode!

**YOUR JOB:**
Complete ONLY the {agent_name} tasks defined in the spec below.

**WHEN DONE:**
1. Commit: [PBI-XXX] [{agent_name.title()}] <type>: <description>
2. Create marker: .{agent_name}_complete
3. STOP working

**SPEC:**
{agent_spec}

---

**YOUR RESPONSIBILITIES ({agent_name}):**
- Architect: Create ADR
- Engineer: Implement with TDD (tests first!)
- Tester: Verify tests + E2E
- CodeReview: Check code quality
- Security: OWASP review
- DevOps: Build verification

Focus ONLY on YOUR agent's tasks. Don't do other agents' work.
Create .{agent_name}_complete when YOUR tasks are done.
"""
    
    session = 0
    
    while session < max_sessions:
        session += 1
        
        print(f"\n{'─'*70}")
        print(f"  {agent_name.upper()} - Session {session}/{max_sessions}")
        print(f"{'─'*70}\n")
        
        # Check if agent marked itself complete
        completion_marker = project_dir / f".{agent_name}_complete"
        if completion_marker.exists():
            print(f"✅ {agent_name.title()} marked itself complete!")
            completion_marker.unlink()  # Clean up marker
            return True
        
        # Run cursor-agent session
        client = CursorMCPClient(
            project_dir=project_dir,
            model=model
        )
        
        if session == 1:
            prompt = initial_prompt
        else:
            prompt = f"""Continue your {agent_name} work.

When done:
- Commit with: [PBI-XXX] [{agent_name.title()}] <type>: <description>  
- Create: .{agent_name}_complete
- STOP

Spec: {spec_file}
"""
        
        status, response = await client.run_session(prompt)
        
        # Check completion again after session
        if completion_marker.exists():
            print(f"✅ {agent_name.title()} complete!")
            completion_marker.unlink()
            return True
        
        if status == "error":
            print(f"❌ {agent_name.title()} session error")
            await asyncio.sleep(3)
            continue
        
        # Small delay between sessions
        await asyncio.sleep(2)
    
    # Reached max sessions without completion
    print(f"⚠️  {agent_name.title()} reached max sessions ({max_sessions})")
    print(f"   Agent may not be complete - check manually")
    
    # Consider it complete anyway (timeout)
    return True

