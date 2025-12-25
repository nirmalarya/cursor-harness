#!/usr/bin/env python3
"""
cursor-harness CLI
==================

Professional CLI for cursor-autonomous-harness.

Usage:
  cursor-harness greenfield <project-dir> [--spec <file>]
  cursor-harness enhance <project-dir> --spec <file>
  cursor-harness bugfix <project-dir> --spec <file>
  cursor-harness backlog <project-dir> --project <name> [--epic <epic>] [--max-pbis <n>]
  cursor-harness validate <project-dir> [--tests]
  cursor-harness --version
  cursor-harness --help
"""

import argparse
import asyncio
import sys
from pathlib import Path

from cursor_agent_runner import run_autonomous_agent
from autonomous_backlog_runner import run_autonomous_backlog


VERSION = "2.3.0-dev"


def cmd_greenfield(args):
    """Start a new project from spec."""
    asyncio.run(
        run_autonomous_agent(
            project_dir=Path(args.project_dir),
            model=args.model,
            max_iterations=args.max_iterations,
            mode="greenfield",
            spec_file=args.spec,
        )
    )


def cmd_enhance(args):
    """Add features to existing project."""
    if not args.spec:
        print("Error: --spec required for enhance mode")
        print("Example: cursor-harness enhance ./myapp --spec specs/new_features.txt")
        sys.exit(1)
    
    asyncio.run(
        run_autonomous_agent(
            project_dir=Path(args.project_dir),
            model=args.model,
            max_iterations=args.max_iterations,
            mode="enhancement",
            spec_file=args.spec,
        )
    )


def cmd_bugfix(args):
    """Fix bugs in existing project."""
    if not args.spec:
        print("Error: --spec required for bugfix mode")
        print("Example: cursor-harness bugfix ./myapp --spec specs/bugs.txt")
        sys.exit(1)
    
    asyncio.run(
        run_autonomous_agent(
            project_dir=Path(args.project_dir),
            model=args.model,
            max_iterations=args.max_iterations,
            mode="bugfix",
            spec_file=args.spec,
        )
    )


def cmd_backlog(args):
    """Process backlog from Azure DevOps."""
    if not args.azure_devops_project:
        print("Error: --azure-devops-project required")
        print("Example: cursor-harness backlog ./togglr --project togglr --epic Epic-3")
        sys.exit(1)
    
    asyncio.run(
        run_autonomous_backlog(
            project_dir=Path(args.project_dir),
            model=args.model,
            azure_devops_org=args.azure_devops_org,
            azure_devops_project=args.azure_devops_project,
            epic=args.epic,
            max_pbis=args.max_pbis,
        )
    )


def cmd_validate(args):
    """Validate existing codebase with tests."""
    print("Validation mode - mark all features unverified, then validate each")
    
    # Reset all features to unverified
    feature_file = Path(args.project_dir) / "spec" / "feature_list.json"
    if feature_file.exists():
        import json
        features = json.load(open(feature_file))
        for f in features:
            f['passes'] = False
        
        with open(feature_file, 'w') as file:
            json.dump(features, file, indent=2)
        
        print(f"✅ Marked {len(features)} features as unverified")
    
    # Run validation
    asyncio.run(
        run_autonomous_agent(
            project_dir=Path(args.project_dir),
            model=args.model,
            max_iterations=args.max_iterations or 500,
            mode="enhancement",
            spec_file="specs/validation_mode.txt",  # Generic validation spec
        )
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cursor-harness",
        description="Autonomous coding harness using Cursor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # New project
  cursor-harness greenfield ./my-app --spec specs/todo_api.txt

  # Add features
  cursor-harness enhance ./my-app --spec specs/new_features.txt

  # Fix bugs
  cursor-harness bugfix ./my-app --spec specs/bugs.txt

  # Process Azure DevOps backlog
  cursor-harness backlog ./togglr --project togglr --epic Epic-3 --max-pbis 5

  # Validate existing code
  cursor-harness validate ./my-app

For more info: https://github.com/nirmalarya/cursor-autonomous-harness
        """,
    )

    parser.add_argument("--version", action="version", version=f"cursor-harness {VERSION}")

    # Global options
    parser.add_argument("--model", type=str, default="sonnet-4.5", help="Cursor model (default: sonnet-4.5)")
    parser.add_argument("--max-iterations", type=int, default=None, help="Max iterations (default: unlimited)")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # greenfield
    greenfield_parser = subparsers.add_parser("greenfield", help="Start new project")
    greenfield_parser.add_argument("project_dir", type=str, help="Project directory")
    greenfield_parser.add_argument("--spec", type=str, help="Specification file")

    # enhance
    enhance_parser = subparsers.add_parser("enhance", help="Add features to existing project")
    enhance_parser.add_argument("project_dir", type=str, help="Project directory")
    enhance_parser.add_argument("--spec", type=str, required=True, help="Enhancement specification file")

    # bugfix
    bugfix_parser = subparsers.add_parser("bugfix", help="Fix bugs in existing project")
    bugfix_parser.add_argument("project_dir", type=str, help="Project directory")
    bugfix_parser.add_argument("--spec", type=str, required=True, help="Bugfix specification file")

    # backlog (autonomous)
    backlog_parser = subparsers.add_parser("backlog", help="Process Azure DevOps backlog")
    backlog_parser.add_argument("project_dir", type=str, help="Project directory")
    backlog_parser.add_argument("--project", dest="azure_devops_project", type=str, required=True, help="Azure DevOps project name")
    backlog_parser.add_argument("--org", dest="azure_devops_org", type=str, default="Bayer-SMO-USRMT", help="Azure DevOps organization")
    backlog_parser.add_argument("--epic", type=str, help="Filter by epic (e.g., Epic-3)")
    backlog_parser.add_argument("--max-pbis", type=int, help="Max PBIs to process")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate existing codebase")
    validate_parser.add_argument("project_dir", type=str, help="Project directory")
    validate_parser.add_argument("--tests", action="store_true", help="Run existing tests")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command
    commands = {
        "greenfield": cmd_greenfield,
        "enhance": cmd_enhance,
        "bugfix": cmd_bugfix,
        "backlog": cmd_backlog,
        "validate": cmd_validate,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("  INTERRUPTED")
        print("="*70)
        print("\nProgress saved. Resume with same command.")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()

