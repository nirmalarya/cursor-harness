#!/usr/bin/env python3
"""
Cursor Autonomous Coding Agent (Cursor CLI Version)
===================================================

A long-running autonomous coding agent using Cursor's built-in AI via CLI.
No separate API key needed - uses your Cursor subscription!
"""

import argparse
import asyncio
import subprocess
from pathlib import Path

from .cursor_agent_runner import run_autonomous_agent
from .prompts import copy_spec_to_project, get_coding_prompt, get_initializer_prompt
from mcp_config import MCPConfigParser, create_cursor_mcp_config, install_mcp_servers
from .autonomous_backlog_runner import run_autonomous_backlog


# Configuration
DEFAULT_MODEL = "sonnet-4.5"  # Claude Sonnet 4.5


def check_cursor_auth() -> bool:
    """Check if user is authenticated with Cursor."""
    try:
        result = subprocess.run(
            ["cursor", "agent", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "Logged in" in result.stdout
    except:
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cursor Autonomous Coding Agent - Build apps with Cursor's AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh project
  python cursor_autonomous_agent.py --project-dir ./my_app

  # Use a specific model
  python cursor_autonomous_agent.py --project-dir ./my_app --model gpt-5

  # Limit iterations for testing
  python cursor_autonomous_agent.py --project-dir ./my_app --max-iterations 3

  # Continue existing project
  python cursor_autonomous_agent.py --project-dir ./my_app

Available Models:
  sonnet-4.5              Claude Sonnet 4.5 (default)
  sonnet-4.5-thinking     Claude Sonnet 4.5 with extended thinking
  opus-4.5                Claude Opus 4.5
  opus-4.5-thinking       Claude Opus 4.5 with extended thinking
  opus-4.1                Claude Opus 4.1
  gpt-5.2                 GPT-5.2
  gpt-5.1                 GPT-5.1
  auto                    Auto-select best model
  composer-1              Composer model

Authentication:
  Uses your Cursor subscription - no separate API key needed!
  If not logged in, run: cursor agent login
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./cursor_project"),
        help="Directory for the project (default: ./cursor_project)",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Cursor model to use (default: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["greenfield", "enhancement", "bugfix", "multi-agent", "autonomous-backlog"],
        default="greenfield",
        help="Development mode: greenfield (new project), enhancement (add features), bugfix (fix issues), multi-agent (run one PBI through workflow), autonomous-backlog (continuous backlog processing)",
    )

    parser.add_argument(
        "--spec",
        type=str,
        default=None,
        help="Path to specification file (e.g., specs/autograph_puppeteer_migration.txt)",
    )

    # Azure DevOps integration
    parser.add_argument(
        "--azure-devops-org",
        type=str,
        default="Bayer-SMO-USRMT",
        help="Azure DevOps organization",
    )

    parser.add_argument(
        "--azure-devops-project",
        type=str,
        default=None,
        help="Azure DevOps project name (e.g., togglr)",
    )

    parser.add_argument(
        "--pbi-id",
        type=str,
        default=None,
        help="Specific PBI ID to process (e.g., PBI-3.1.1 or BUG-16741)",
    )

    parser.add_argument(
        "--epic",
        type=str,
        default=None,
        help="Filter by epic (e.g., Epic-3)",
    )

    parser.add_argument(
        "--max-pbis",
        type=int,
        default=None,
        help="Maximum number of PBIs to process in autonomous-backlog mode",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Check if authenticated with Cursor
    print("Checking Cursor authentication...")
    if not check_cursor_auth():
        print("\n" + "=" * 70)
        print("  ERROR: Not logged in to Cursor")
        print("=" * 70)
        print("\nPlease authenticate with Cursor first:")
        print("  cursor agent login")
        print("\nThen run this script again.")
        return

    print("✓ Authenticated with Cursor")
    print()

    # Ensure project directory exists
    project_dir = args.project_dir.resolve()

    # Check if this is a fresh start
    feature_file = project_dir / "feature_list.json"
    is_first_run = not feature_file.exists()

    if is_first_run:
        # Copy app spec to project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        copy_spec_to_project(project_dir)
        
        # Parse and configure MCP servers from spec
        spec_file = project_dir / "app_spec.txt"
        if spec_file.exists():
            print("\n" + "=" * 70)
            print("  Configuring MCP Servers from Spec")
            print("=" * 70 + "\n")
            
            parser = MCPConfigParser(spec_file)
            mcp_servers = parser.parse_mcp_servers()
            
            if mcp_servers:
                print(f"Found {len(mcp_servers)} MCP servers in spec:")
                for name in mcp_servers.keys():
                    print(f"  - {name}")
                
                # Create Cursor MCP configuration
                create_cursor_mcp_config(project_dir, mcp_servers)
                
                # Check/install MCP servers
                install_mcp_servers(mcp_servers)
                
                print("\n" + "=" * 70)
                print("  MCP Configuration Complete")
                print("=" * 70 + "\n")
            else:
                print("No MCP servers found in spec (will use Cursor defaults)\n")

    # Validate required arguments
    if args.mode in ["enhancement", "bugfix"] and not args.spec:
        print(f"Error: --spec is required for {args.mode} mode")
        print(f"\nExample: --spec specs/sherpa_enhancement_spec.txt")
        return
    
    if args.mode in ["multi-agent", "autonomous-backlog"] and not args.azure_devops_project:
        print(f"Error: --azure-devops-project is required for {args.mode} mode")
        print(f"\nExample: --azure-devops-project togglr")
        return

    # Route to appropriate mode
    try:
        if args.mode == "autonomous-backlog":
            # Continuous backlog processing
            asyncio.run(
                run_autonomous_backlog(
                    project_dir=project_dir,
                    model=args.model,
                    azure_devops_org=args.azure_devops_org,
                    azure_devops_project=args.azure_devops_project,
                    epic=args.epic,
                    max_pbis=args.max_pbis,
                )
            )
        elif args.mode == "multi-agent":
            # Single PBI workflow
            print("Multi-agent mode: Use autonomous-backlog with --max-pbis 1 for now")
            return
        else:
            # Traditional modes
            asyncio.run(
                run_autonomous_agent(
                    project_dir=project_dir,
                    model=args.model,
                    max_iterations=args.max_iterations,
                    mode=args.mode,
                    spec_file=args.spec,
                )
            )
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("  INTERRUPTED BY USER")
        print("="*70)
        print("\nCursor agent has been terminated.")
        print("Progress is saved in the project directory.")
        print("\nTo resume, run the same command again:")
        print(f"  python cursor_autonomous_agent.py --project-dir {project_dir}")
        print("="*70)
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()

