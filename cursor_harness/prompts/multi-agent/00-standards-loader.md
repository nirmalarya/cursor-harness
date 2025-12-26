# Standards Loader for Generic Multi-Agent Prompts

## Auto-Detection of Project Standards

**Before executing agent work, check if project has custom standards:**

```
If docs/standards/ exists:
  - Use project-specific standards
  - Reference docs/standards/coding-guidelines.md
  - Reference docs/standards/testing-standards.md
  - Reference docs/standards/security-requirements.md
  - Reference docs/standards/naming-conventions.md

If docs/standards/ does NOT exist:
  - Standards were installed by cursor-harness
  - Still follow the same standards structure
```

**This allows generic agent prompts to work with ANY project!**

## Placeholder Replacement

Generic prompts use `{{PROJECT_NAME}}` placeholders.

cursor-harness replaces these with actual project name before sending to agent.

**Example:**
```
"Review {{PROJECT_NAME}} codebase for security issues"
→ "Review togglr codebase for security issues"
```

## ADR Numbering

**Auto-detect next ADR number:**

```bash
# Check existing ADRs
ls docs/adrs/ADR-*.md | tail -1
# Extract number, increment
# Use for new ADR
```

**This ensures:**
- No ADR number collisions
- Proper sequential numbering
- Works for any project
