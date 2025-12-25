"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

import shutil
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    return prompt_path.read_text()


def get_initializer_prompt(mode: str = "greenfield") -> str:
    """Load the initializer prompt based on mode."""
    if mode == "enhancement":
        return load_prompt("enhancement_initializer_prompt")
    elif mode == "bugfix":
        return load_prompt("enhancement_initializer_prompt")  # Same as enhancement
    else:
        return load_prompt("initializer_prompt")


def get_coding_prompt(mode: str = "greenfield") -> str:
    """Load the coding agent prompt based on mode."""
    if mode == "enhancement":
        return load_prompt("enhancement_coding_prompt")
    elif mode == "bugfix":
        return load_prompt("bugfix_mode_prompt")
    else:
        return load_prompt("coding_prompt")


def copy_spec_to_project(project_dir: Path, spec_file: str = None, mode: str = "greenfield") -> None:
    """Copy the spec file and helper tools into the project directory."""
    # Create spec/ directory in project
    spec_dir = project_dir / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy spec file to project/spec/
    if spec_file:
        spec_source = Path(spec_file)
        # Determine target name based on mode
        if mode in ["enhancement", "bugfix"]:
            spec_name = "enhancement_spec.txt"
        else:
            spec_name = "app_spec.txt"
    else:
        # Use default example spec
        spec_source = Path(__file__).parent / "specs" / "simple_example_spec.txt"
        spec_name = "app_spec.txt"
    
    spec_dest = spec_dir / spec_name
    
    if not spec_dest.exists() or mode in ["enhancement", "bugfix"]:
        shutil.copy(spec_source, spec_dest)
        print(f"Copied {spec_source.name} to project directory as {spec_name}")
    
    # Copy helper tools to project from harness root
    harness_root = Path(__file__).parent
    tools_to_copy = ["regression_tester.py"]
    
    for tool in tools_to_copy:
        tool_source = harness_root / tool
        tool_dest = project_dir / tool
        if tool_source.exists() and not tool_dest.exists():
            shutil.copy(tool_source, tool_dest)
            print(f"Copied {tool} to project directory")
