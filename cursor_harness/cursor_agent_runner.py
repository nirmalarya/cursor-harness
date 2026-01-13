"""
Cursor Agent Runner with Session Management
===========================================

Core logic for running autonomous coding sessions using Cursor CLI.
"""

import asyncio
from pathlib import Path
from typing import Optional

from .cursor_mcp_client import CursorMCPClient, check_cursor_prerequisites
from .mcp_manager import create_mcp_manager_from_cursor_config
from .progress import count_features, print_progress_summary, print_session_header
from .security import SecurityValidator
from .multi_agent_mode import MultiAgentWorkflow
from .azure_devops_integration import AzureDevOpsIntegration
from .project_scaffolder import ProjectScaffolder
from .browser_cleanup import setup_browser_cleanup, kill_orphaned_browsers
from .infrastructure_validator import InfrastructureValidator
from .retry_manager import RetryManager


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: Optional[int] = None,
    mode: str = "greenfield",
    spec_file: Optional[str] = None,
) -> None:
    """
    Run the autonomous agent loop using Cursor CLI.

    Args:
        project_dir: Directory for the project
        model: Cursor model to use (e.g., sonnet-4, gpt-5, sonnet-4-thinking)
        max_iterations: Maximum number of iterations (None for unlimited)
        mode: Development mode (greenfield, enhancement, bugfix)
        spec_file: Path to specification file (required for enhancement/bugfix)
    """
    from .prompts import get_initializer_prompt, get_coding_prompt, copy_spec_to_project
    print("\n" + "=" * 70)
    print("  CURSOR AUTONOMOUS CODING AGENT")
    print("  (Using Cursor CLI)")
    print("=" * 70)
    print(f"\nProject directory: {project_dir.resolve()}")
    print(f"Model: {model}")
    print(f"Mode: {mode}")
    if spec_file:
        print(f"Spec file: {spec_file}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up project structure (rules, docs, MCPs, sessions)
    scaffolder = ProjectScaffolder(project_dir)
    scaffolder.setup_project(mode=mode)
    
    # Validate infrastructure ONCE (critical for autonomous operation!)
    validator = InfrastructureValidator(project_dir)
    infra_valid, infra_message = validator.validate_once(mode=mode)
    
    if not infra_valid:
        print(f"\n❌ Infrastructure validation failed!")
        print(f"   {infra_message}")
        print(f"\n🔧 Fix the issues above, then run cursor-harness again.")
        return
    
    print(f"   ✅ {infra_message}\n")
    
    # Set up browser cleanup
    setup_browser_cleanup()

    # Initialize security validator
    security_validator = SecurityValidator()

    # Initialize retry manager
    retry_manager = RetryManager(project_dir)
    print(f"📊 Retry tracking initialized")

    # Check if this is a fresh start or continuation
    spec_dir = project_dir / "spec"
    feature_file = spec_dir / "feature_list.json"
    enhancement_spec_file = spec_dir / "enhancement_spec.txt"
    
    # Determine if this is the first run
    if mode in ["enhancement", "bugfix"]:
        # Enhancement mode: first run if no enhancement_spec.txt exists
        is_first_run = not enhancement_spec_file.exists()
    else:
        # Greenfield mode: first run if no feature_list.json exists
        is_first_run = not feature_file.exists()

    if is_first_run:
        print(f"🆕 Fresh start - will use initializer agent ({mode} mode)")
        print()
        if mode == "greenfield":
            print("=" * 70)
            print("  NOTE: First session takes 10-20+ minutes!")
            print("  The agent is generating comprehensive test cases.")
            print("  This may appear to hang - it's working.")
            print("=" * 70)
        else:
            print("=" * 70)
            print(f"  {mode.upper()} MODE - Enhancing existing project")
            print("  Reading existing feature_list.json and appending new features.")
            print("=" * 70)
        print()
        # Copy the spec into the project directory for the agent to read
        copy_spec_to_project(project_dir, spec_file, mode)
    else:
        print(f"Continuing existing project ({mode} mode)")
        print_progress_summary(project_dir)

    # Main loop
    iteration = 0
    session_number = 0
    is_initializer_phase = True

    # Track feature states before each session for retry logic
    previous_feature_states = {}

    # cursor-agent handles MCPs automatically - we don't spawn them!

    try:
        while True:
            iteration += 1

            # Load current feature states before session
            if feature_file.exists():
                import json
                try:
                    with open(feature_file) as f:
                        features = json.load(f)
                    previous_feature_states = {
                        f.get('id', f.get('name', '')): f.get('passes', False)
                        for f in features
                    }
                except (json.JSONDecodeError, IOError):
                    pass

            # Check max iterations
            if max_iterations and iteration > max_iterations:
                print(f"\nReached max iterations ({max_iterations})")
                print("To continue, run the script again without --max-iterations")
                break
            
            # Check if project is 100% complete (CRITICAL!)
            # Skip on iteration 1 for enhancement/bugfix (let initializer add features first!)
            if iteration > 1 or mode == "greenfield":
                if feature_file.exists():
                    import json
                    try:
                        with open(feature_file) as f:
                            features = json.load(f)
                        total = len(features)
                        passing = sum(1 for f in features if f.get('passes', False))
                        
                        if passing >= total and total > 0:
                            print("\n" + "=" * 70)
                            print(f"🎉 PROJECT 100% COMPLETE ({passing}/{total} features passing)!")
                            print("=" * 70)
                            print("\nAll features are marked as passing.")
                            print("The autonomous coding work is DONE.")
                            print("\n✅ STOPPING AUTOMATICALLY - No further work needed!")
                            print("\nTo add more features, create a new enhancement spec.")
                            print("=" * 70)
                            return  # Exit the function, stopping the loop
                    except (json.JSONDecodeError, IOError):
                        pass  # Continue if we can't read the file

            # Print session header
            print_session_header(iteration, is_first_run)

            # Create client (fresh context for each session)
            # cursor-agent auto-loads MCPs from ~/.cursor/mcp.json
            client = CursorMCPClient(
                project_dir=project_dir,
                model=model
            )

            # Choose prompt based on session type and mode
            if is_first_run:
                prompt = get_initializer_prompt(mode)
                is_first_run = False  # Only use initializer once
            else:
                prompt = get_coding_prompt(mode)

            # Run session
            status, response = await client.run_session(prompt)

            # After session: Track retry attempts based on feature state changes
            if feature_file.exists() and not is_first_run:
                import json
                try:
                    with open(feature_file) as f:
                        features = json.load(f)

                    # Check which features changed state
                    for feature in features:
                        feature_id = feature.get('id', feature.get('name', ''))
                        if not feature_id:
                            continue

                        current_passes = feature.get('passes', False)
                        previous_passes = previous_feature_states.get(feature_id, False)

                        # Feature was worked on (not passing before, still not passing now)
                        # OR feature became passing (success!)
                        if not previous_passes:
                            if current_passes:
                                # Feature succeeded! Reset retry count
                                retry_manager.reset_feature(feature_id)
                                print(f"   ✅ Feature '{feature_id}' passed - retry count reset")
                            elif feature_id in previous_feature_states:
                                # Feature was attempted but still not passing
                                retry_manager.record_attempt(feature_id)
                                attempts = retry_manager.get_attempts(feature_id)
                                if not retry_manager.can_retry(feature_id):
                                    print(f"   ⚠️  Feature '{feature_id}' exceeded max retries ({attempts}/{RetryManager.MAX_RETRIES})")
                                    print(f"      Consider marking as 'skipped' or investigating why it's failing")
                                elif attempts > 1:
                                    print(f"   🔄 Feature '{feature_id}' retry attempt {attempts}/{RetryManager.MAX_RETRIES}")

                except (json.JSONDecodeError, IOError):
                    pass

            # Handle status
            if status == "complete":
                print("\nAgent completed this session")
                print_progress_summary(project_dir)

                # Check if all features are done
                passing, total = count_features(project_dir)
                if total > 0 and passing >= total:
                    print("\n🎉 All features complete! Project finished.")
                    break

                # Auto-continue
                print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
                await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

            elif status == "max_turns":
                print("\nSession reached max turns")
                print("Will continue with a fresh session...")
                print_progress_summary(project_dir)
                await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

            elif status == "error":
                print(f"\nSession encountered an error: {response}")
                print("Will retry with a fresh session...")
                await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

            # Small delay between sessions
            if max_iterations is None or iteration < max_iterations:
                print("\nPreparing next session...\n")
                await asyncio.sleep(1)
    
    finally:
        # cursor-agent handles MCP cleanup automatically
        pass
    
    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir.resolve()}")
    print_progress_summary(project_dir)

    # Print instructions for running the generated application
    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Run the setup script")
    print("  # Or manually:")
    print("  npm install && npm run dev")
    print("\n  Then open http://localhost:3000 (or check init.sh for the URL)")
    print("-" * 70)

    print("\nDone!")

