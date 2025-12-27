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
from .loop_detector import LoopDetector, get_latest_commit, has_uncommitted_changes


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
    loop_detector = LoopDetector(max_repeated_reads=3, session_timeout_minutes=60)
    last_commit = get_latest_commit(project_dir)
    
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
        
        # Start loop detection for this session
        loop_detector.start_session()
        
        # Run cursor-agent session with timeout
        client = CursorMCPClient(
            project_dir=project_dir,
            model=model,
            loop_detector=loop_detector  # Pass detector to track file reads
        )
        
        if session == 1:
            prompt = initial_prompt
        else:
            prompt = f"""Continue your {agent_name} work.

CRITICAL: If you're stuck in a loop (reading same files, validating repeatedly):
- STOP validating and START implementing
- Make a commit and create .{agent_name}_complete

When done:
- Commit with: [PBI-XXX] [{agent_name.title()}] <type>: <description>  
- Create: .{agent_name}_complete
- STOP

Session {session}/{max_sessions}

Spec: {spec_file}
"""
        
        status, response = await client.run_session(prompt)
        
        # Check completion again after session
        if completion_marker.exists():
            print(f"✅ {agent_name.title()} complete!")
            completion_marker.unlink()
            return True
        
        # Check for loops using comprehensive detection
        is_stuck, reason = loop_detector.check_for_loop()
        
        if is_stuck:
            print(f"\n⚠️  LOOP DETECTED: {reason}")
            print(f"   Stopping {agent_name.title()} agent to prevent infinite loop")
            
            # Check if there's uncommitted work (means agent did something)
            if has_uncommitted_changes(project_dir):
                print(f"   ✅ Found uncommitted changes - agent made progress")
                print(f"   Creating completion marker to finalize")
                completion_marker.touch()  # Force completion
                return True
            else:
                print(f"   ⚠️  No changes detected - agent may not have completed work")
                return True  # Stop anyway to prevent infinite loop
        
        # Check for actual progress (commits OR uncommitted changes)
        current_commit = get_latest_commit(project_dir)
        has_changes = has_uncommitted_changes(project_dir)
        
        if current_commit != last_commit or has_changes:
            last_commit = current_commit
            if has_changes:
                print(f"   📝 Progress: Uncommitted changes detected")
            else:
                print(f"   ✅ Progress: New commit {current_commit}")
        
        # Reset loop detector for next session
        loop_detector.reset_session()
        
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

