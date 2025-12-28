#!/usr/bin/env python3
"""cursor-harness v3.0 CLI."""

import sys
import argparse
from pathlib import Path
from .core import CursorHarness


def main():
    parser = argparse.ArgumentParser(
        description='cursor-harness v3.0 - Simple, reliable autonomous coding'
    )
    parser.add_argument('--version', action='version', version='cursor-harness v3.0.0-beta')
    
    subparsers = parser.add_subparsers(dest='mode', help='Mode')
    
    # Greenfield
    greenfield = subparsers.add_parser('greenfield', help='New project from scratch')
    greenfield.add_argument('project_dir', type=Path, help='Project directory')
    greenfield.add_argument('--spec', type=Path, help='Specification file')
    greenfield.add_argument('--timeout', type=int, default=480, help='Timeout in minutes')
    greenfield.add_argument('--model', type=str, default='claude-sonnet-4', help='Model to use (claude-sonnet-4, gpt-4, etc)')
    
    # Enhancement
    enhance = subparsers.add_parser('enhance', help='Add features to existing project')
    enhance.add_argument('project_dir', type=Path, help='Project directory')
    enhance.add_argument('--spec', type=Path, required=True, help='Enhancement spec')
    enhance.add_argument('--timeout', type=int, default=480, help='Timeout in minutes')
    enhance.add_argument('--model', type=str, default='claude-sonnet-4', help='Model to use')
    
    # Backlog
    backlog = subparsers.add_parser('backlog', help='Process Azure DevOps backlog')
    backlog.add_argument('project_dir', type=Path, help='Project directory')
    backlog.add_argument('--org', required=True, help='Azure DevOps organization')
    backlog.add_argument('--project', required=True, help='Azure DevOps project')
    backlog.add_argument('--timeout', type=int, default=1440, help='Timeout in minutes')
    backlog.add_argument('--model', type=str, default='claude-sonnet-4', help='Model to use')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    # Create harness
    harness = CursorHarness(
        project_dir=args.project_dir,
        mode=args.mode,
        spec_file=getattr(args, 'spec', None),
        timeout_minutes=args.timeout,
        model=getattr(args, 'model', 'claude-sonnet-4')
    )
    
    # Pass Azure DevOps info for backlog mode
    if args.mode == 'backlog':
        harness.ado_org = args.org
        harness.ado_project = args.project
    
    # Run
    success = harness.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

