"""
Project Scaffolder
==================

Sets up complete project structure with rules, standards, and MCP configuration.
Makes cursor-harness self-contained - works on ANY project!
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


class ProjectScaffolder:
    """Scaffolds project structure for cursor-harness."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.harness_root = Path(__file__).parent
    
    def setup_project(self, mode: str = "greenfield"):
        """
        Set up complete project structure.
        
        Args:
            mode: greenfield, enhancement, bugfix, or backlog
        """
        print("\n🔧 Setting up project structure...")
        
        if mode == "greenfield":
            self._setup_greenfield()
        else:
            self._setup_enhancement()
        
        print("✅ Project structure ready!\n")
    
    def _setup_greenfield(self):
        """Set up greenfield project with all necessary files."""
        # 1. Create .cursor/ directory with rules
        self._setup_cursor_rules()
        
        # 2. Create docs/ with standards
        self._setup_docs_standards()
        
        # 3. Create .mcp.json
        self._setup_mcp_config()
        
        # 4. Create sessions/ folder
        self._setup_sessions_folder()
        
        # 5. Create spec/ folder
        (self.project_dir / "spec").mkdir(exist_ok=True)
    
    def _setup_enhancement(self):
        """Set up/update existing project."""
        # Check what's missing and update
        self._ensure_cursor_rules()
        self._ensure_docs_standards()
        self._ensure_mcp_config()
        self._setup_sessions_folder()
    
    def _setup_cursor_rules(self):
        """Copy generic agent rules to .cursor/rules/."""
        target_dir = self.project_dir / ".cursor" / "rules"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy multi-agent rules
        source_dir = self.harness_root / "prompts" / "multi-agent"
        
        agent_files = [
            "01-architect.md",
            "02-engineer.md",
            "03-tester.md",
            "04-code-review.md",
            "05-security.md",
            "06-devops.md",
        ]
        
        print("  📁 Installing agent rules...")
        for agent_file in agent_files:
            source = source_dir / agent_file
            # Remove number prefix for target
            target_name = agent_file[3:]  # Remove "01-" etc.
            target = target_dir / target_name.replace(".md", ".mdc")
            
            if source.exists():
                shutil.copy2(source, target)
                print(f"     ✅ {target_name}")
    
    def _ensure_cursor_rules(self):
        """Ensure .cursor/rules/ exists and is up to date."""
        rules_dir = self.project_dir / ".cursor" / "rules"
        
        if not rules_dir.exists():
            print("  📁 .cursor/rules/ not found - installing...")
            self._setup_cursor_rules()
        else:
            print("  ✅ .cursor/rules/ exists")
            # TODO: Check if rules need updating (version check)
    
    def _setup_docs_standards(self):
        """Create docs/standards/ with generic best practices."""
        docs_dir = self.project_dir / "docs" / "standards"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        print("  📚 Creating standards documentation...")
        
        # Generic coding guidelines
        (docs_dir / "coding-guidelines.md").write_text("""# Coding Guidelines

## General Principles

1. **Code Quality**
   - Write self-documenting code
   - Use meaningful variable/function names
   - Keep functions small and focused (single responsibility)
   - Avoid deep nesting (max 3 levels)

2. **Documentation**
   - JSDoc for all public functions (TypeScript/JavaScript)
   - Docstrings for all public functions (Python)
   - godoc comments for all exported functions (Go)

3. **Error Handling**
   - Always handle errors explicitly
   - Use custom error classes
   - Never swallow errors silently
   - Log errors with context

4. **Testing**
   - Write tests FIRST (TDD)
   - Minimum 80% code coverage
   - Test edge cases and error paths
   - Use descriptive test names

5. **Security**
   - Never commit secrets/API keys
   - Validate all external input
   - Use parameterized queries (SQL)
   - Implement proper authentication/authorization

6. **Performance**
   - Avoid N+1 queries
   - Use appropriate data structures
   - Cache when appropriate
   - Profile before optimizing
""")
        
        # Generic testing standards
        (docs_dir / "testing-standards.md").write_text("""# Testing Standards

## Test Coverage Requirements

- **Minimum:** 80% statement coverage
- **Functions:** 100% coverage preferred
- **Branches:** ≥70% coverage
- **Critical paths:** 100% coverage required

## Test Types

### 1. Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (<100ms per test)
- Comprehensive edge case coverage

### 2. Integration Tests
- Test component interactions
- Use test database
- Verify API contracts
- Test error scenarios

### 3. E2E Tests
- Test critical user flows
- Use Playwright/Puppeteer
- Run against staging environment
- Cover happy paths + error cases

## Test Organization

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── e2e/           # End-to-end tests
```

## Best Practices

1. **Arrange-Act-Assert** pattern
2. **Descriptive test names** (describe what's being tested)
3. **One assertion per test** (when possible)
4. **Test data builders** for complex objects
5. **Cleanup after tests** (avoid side effects)
""")
        
        # Security requirements
        (docs_dir / "security-requirements.md").write_text("""# Security Requirements

## OWASP Top 10 Compliance

All code must be reviewed against [OWASP Top 10](https://owasp.org/www-project-top-ten/).

### Critical Requirements

1. **Authentication & Authorization**
   - Use industry-standard auth (JWT, OAuth2, etc.)
   - Implement RBAC for all protected resources
   - Never trust client-side authorization

2. **Input Validation**
   - Validate ALL external input
   - Use schemas (Zod, Joi, etc.)
   - Whitelist validation (not blacklist)
   - Sanitize for XSS

3. **Secrets Management**
   - NEVER commit secrets to git
   - Use environment variables
   - Rotate secrets regularly
   - Use secret management tools (Vault, etc.)

4. **SQL Injection Prevention**
   - Use ORM (Prisma, TypeORM, SQLAlchemy)
   - OR use parameterized queries
   - Never construct SQL from strings

5. **Dependency Management**
   - Run `npm audit` / `pip audit` regularly
   - Keep dependencies up to date
   - Review security advisories

6. **Error Handling**
   - Don't leak sensitive info in errors
   - Log errors server-side only
   - Generic error messages to clients

## Security Review Checklist

- [ ] No hardcoded secrets
- [ ] All input validated
- [ ] SQL injection prevented
- [ ] XSS prevention implemented
- [ ] CSRF protection (for web apps)
- [ ] Authentication on all protected routes
- [ ] Authorization checks enforced
- [ ] Audit logging for sensitive operations
- [ ] Dependencies scanned for vulnerabilities
- [ ] Error messages don't leak sensitive info
""")
        
        # Naming conventions
        (docs_dir / "naming-conventions.md").write_text("""# Naming Conventions

## Files

- **TypeScript/JavaScript:** `kebab-case.ts`, `kebab-case.tsx`
- **Python:** `snake_case.py`
- **Go:** `kebab-case.go`
- **Tests:** `*.test.ts`, `*_test.py`, `*_test.go`

## Code

### TypeScript/JavaScript
- **Variables/Functions:** `camelCase`
- **Classes/Components:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_prefixWithUnderscore`

### Python
- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** `_prefix_with_underscore`

### Go
- **Variables/Functions:** `camelCase`
- **Exported:** `PascalCase`
- **Constants:** `PascalCase` or `camelCase`

## API

- **Endpoints:** `/kebab-case/resources`
- **Query params:** `camelCase`
- **JSON keys:** `camelCase`

## Database

- **Tables:** `snake_case`
- **Columns:** `snake_case`
- **Indexes:** `idx_table_column`

## Environment Variables

- **All:** `UPPER_SNAKE_CASE`
""")
        
        print("     ✅ coding-guidelines.md")
        print("     ✅ testing-standards.md")
        print("     ✅ security-requirements.md")
        print("     ✅ naming-conventions.md")
        
        # Create ADR template
        adrs_dir = self.project_dir / "docs" / "adrs"
        adrs_dir.mkdir(parents=True, exist_ok=True)
        
        (adrs_dir / "template.md").write_text("""# ADR-XXX: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Deciders:** [Names]
**Technical Story:** [PBI/Issue ID]

## Context

[Describe the context and problem statement]

## Decision Drivers

- [Driver 1]
- [Driver 2]
- [Driver 3]

## Considered Options

- [Option 1]
- [Option 2]
- [Option 3]

## Decision Outcome

**Chosen option:** [Option X]

**Rationale:** [Why this option was chosen]

### Positive Consequences

- [Positive 1]
- [Positive 2]

### Negative Consequences

- [Negative 1]
- [Negative 2]

## Pros and Cons of the Options

### [Option 1]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

### [Option 2]

[Same structure as Option 1]

## Links

- [Related ADRs]
- [External references]
""")
        print("     ✅ adrs/template.md")
    
    def _ensure_docs_standards(self):
        """Ensure docs/standards/ exists."""
        standards_dir = self.project_dir / "docs" / "standards"
        
        if not standards_dir.exists():
            print("  📚 docs/standards/ not found - installing...")
            self._setup_docs_standards()
        else:
            print("  ✅ docs/standards/ exists")
            # TODO: Check if standards need updating
    
    def _setup_mcp_config(self):
        """Create .mcp.json with essential MCPs."""
        mcp_file = self.project_dir / ".mcp.json"
        
        if mcp_file.exists():
            print("  ✅ .mcp.json exists (not overwriting)")
            return
        
        mcp_config = {
            "mcpServers": {
                "playwright": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@playwright/mcp@latest"],
                    "env": {}
                },
                "puppeteer": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
                    "env": {}
                }
            }
        }
        
        import json
        mcp_file.write_text(json.dumps(mcp_config, indent=2))
        print("  ✅ .mcp.json created (Playwright + Puppeteer)")
    
    def _ensure_mcp_config(self):
        """Ensure .mcp.json exists."""
        if not (self.project_dir / ".mcp.json").exists():
            print("  📝 .mcp.json not found - creating...")
            self._setup_mcp_config()
        else:
            print("  ✅ .mcp.json exists")
    
    def _setup_sessions_folder(self):
        """Create sessions folder with current timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        session_dir = self.project_dir / "sessions" / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create README
        (session_dir.parent / "README.md").write_text("""# Sessions

This folder contains organized session summaries and artifacts from cursor-harness runs.

Each session is in a timestamped folder:
```
sessions/
├── 2025-12-25-143022/
│   ├── session-summary.md
│   ├── artifacts/
│   │   ├── adrs/
│   │   ├── tests/
│   │   └── docs/
│   └── cursor-progress.txt
└── 2025-12-26-091500/
    └── ...
```

## Session Summary Format

Each `session-summary.md` contains:
- PBI/Work item details
- Agent results (Architect, Engineer, Tester, etc.)
- Commits made
- Files created/modified
- Test results
- Quality scores
- Completion status
""")
        
        print(f"  ✅ sessions/{timestamp}/ created")
        
        return session_dir
    
    def create_session_summary(
        self,
        session_dir: Path,
        pbi_id: str,
        pbi_title: str,
        agent_results: dict
    ):
        """Create comprehensive session summary."""
        
        summary = f"""# Session Summary - {pbi_id}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Work Item:** {pbi_id} - {pbi_title}
**Mode:** Multi-Agent Workflow

---

## 📊 Agent Results

"""
        
        for agent, result in agent_results.items():
            summary += f"""
### {agent.title()} Agent

**Status:** {result.get('status', 'Unknown')}
**Score/Grade:** {result.get('score', 'N/A')}
**Commit:** {result.get('commit', 'N/A')}

**Key Deliverables:**
{result.get('deliverables', 'N/A')}

**Notes:**
{result.get('notes', 'N/A')}

---
"""
        
        summary += f"""
## 📁 Files Created/Modified

{agent_results.get('files_summary', 'See git log for details')}

---

## 🎯 Completion Status

**Overall:** {agent_results.get('overall_status', 'Unknown')}
**Deployment Ready:** {agent_results.get('deployment_ready', 'Unknown')}

---

## 🔗 References

- Azure DevOps: {agent_results.get('ado_url', 'N/A')}
- Git commits: See `git log --grep="{pbi_id}"`
"""
        
        (session_dir / "session-summary.md").write_text(summary)
        print(f"  ✅ Session summary created")
    
    def check_and_update_structure(self) -> dict:
        """
        Check project structure and report what needs updating.
        
        Returns:
            Dict with status of each component
        """
        status = {
            "cursor_rules": (self.project_dir / ".cursor" / "rules").exists(),
            "docs_standards": (self.project_dir / "docs" / "standards").exists(),
            "mcp_config": (self.project_dir / ".mcp.json").exists(),
            "sessions_folder": (self.project_dir / "sessions").exists(),
        }
        
        missing = [k for k, v in status.items() if not v]
        
        if missing:
            print(f"\n⚠️  Missing: {', '.join(missing)}")
            print("   cursor-harness will set these up automatically\n")
        else:
            print("\n✅ Project structure complete\n")
        
        return status

