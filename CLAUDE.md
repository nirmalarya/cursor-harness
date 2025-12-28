# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cursor-harness v3.0 is an autonomous coding harness based on [Anthropic's effective harness pattern](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). It enables autonomous, incremental development through a two-agent session pattern:

1. **Initializer Agent** (Session 1): Sets up environment, creates feature_list.json, initializes git
2. **Coding Agent** (Sessions 2-N): Implements ONE feature at a time with fresh context, tests, commits, and updates progress

**Key Philosophy:** Simple core (~1,100 lines) based on Anthropic's proven pattern, extended for production use with multiple modes (greenfield, enhancement, backlog).

## Development Commands

### Installation
```bash
# Install in development mode
pip install -e .

# Or using pipx
pipx install -e .
```

### Running the Harness

```bash
# Greenfield mode (new project)
cursor-harness greenfield ./my-app --spec app_spec.txt

# Enhancement mode (existing project)
cursor-harness enhance ./existing-app --spec enhancements.txt

# Backlog mode (Azure DevOps)
cursor-harness backlog ./project --org MyOrg --project MyProject
```

### Testing

```bash
# Run simple test
python tests/test_simple.py

# Run with pytest (if available)
pytest tests/

# Test specific mode manually
python cursor_harness/core.py greenfield /tmp/test-project spec.txt
```

### Development Workflow

```bash
# 1. Make changes to code
# 2. Test locally first (no automated test runner yet)
python tests/test_simple.py

# 3. Commit changes
git add .
git commit -m "description"
```

## Architecture

### Core Session Pattern (Anthropic's Two-Prompt System)

The harness uses different prompts based on mode and session:

**Initializer Prompts** (Session 1):
- `cursor_harness/prompts/initializer.md` - Greenfield
- `cursor_harness/prompts/enhancement_initializer.md` - Enhancement
- `cursor_harness/prompts/backlog_initializer.md` - Backlog

**Coding Prompts** (Sessions 2-N):
- `cursor_harness/prompts/coding.md` - Greenfield
- `cursor_harness/prompts/enhancement_coding.md` - Enhancement
- `cursor_harness/prompts/backlog_coding.md` - Backlog

**Continuation Prompts** (For large projects >50 features):
- `cursor_harness/prompts/continuation_coding.md`
- `cursor_harness/prompts/enhancement_continuation.md`
- `cursor_harness/prompts/backlog_continuation.md`

All prompts include `cursor_harness/prompts/system_instructions.md` for common instructions.

### Module Structure

```
cursor_harness/
├── core.py                          # Main orchestrator (~430 lines)
│   ├── CursorHarness                # Main harness class
│   ├── WorkItem                     # Work unit dataclass
│   └── ExecutionResult              # Result tracking
│
├── cli.py                           # CLI interface (~68 lines)
│   └── main()                       # Argument parsing, harness invocation
│
├── executor/
│   └── cursor_executor.py           # cursor-agent CLI integration (~250 lines)
│       └── CursorExecutor           # Streams JSON output, tracks tool usage
│
├── prompts/                         # Session prompts (Anthropic pattern)
│   ├── initializer.md               # Greenfield session 1
│   ├── coding.md                    # Greenfield sessions 2-N
│   ├── enhancement_*.md             # Enhancement mode prompts
│   ├── backlog_*.md                 # Backlog mode prompts
│   ├── continuation_*.md            # Large project (>50 features) prompts
│   └── system_instructions.md       # Common instructions
│
├── validators/
│   ├── test_runner.py               # Pytest/npm test execution (~100 lines)
│   ├── secrets_scanner.py           # Detects exposed secrets (~100 lines)
│   └── e2e_tester.py                # Puppeteer E2E testing (~100 lines)
│
├── infra/
│   └── healer.py                    # Self-healing infrastructure (~100 lines)
│       └── InfrastructureHealer     # Auto-starts Docker, runs migrations, creates buckets
│
├── integrations/
│   └── azure_devops.py              # Azure DevOps backlog integration
│       └── AzureDevOpsIntegration   # PBI fetching, state management
│
├── hooks.py                         # Cursor hooks system
│   └── HooksManager                 # Creates hooks.json + shell scripts
│       ├── setup_default_hooks()    # Auto-validation via cursor-agent
│       └── _create_cursorignore()   # Security: blocks .env, keys, credentials
│
└── loop_detector.py                 # Prevents infinite loops
    └── LoopDetector                 # Timeout, repeated reads, no-progress detection
```

### Key Design Patterns

1. **Mode-based prompt selection** (core.py:327-376)
   - `_build_prompt()` selects appropriate prompt based on:
     - `self.mode` (greenfield/enhancement/backlog)
     - `self.is_first_session` (initializer vs coding)
     - `self.is_continuation` (>50 features)

2. **Session execution via cursor-agent CLI** (core.py:299-324)
   - Uses `cursor_executor.py` to invoke `cursor-agent` command
   - Streams JSON output for real-time feedback
   - No direct API calls - leverages Cursor's authentication

3. **State tracking through files**
   - `feature_list.json` - Greenfield progress (`passing: true/false`)
   - `.cursor/enhancement-state.json` - Enhancement progress
   - `.cursor/backlog-state.json` - Backlog progress (Azure DevOps PBIs)
   - `cursor-progress.txt` - Session notes
   - Git commits - Full implementation history

4. **Automatic validation via hooks** (hooks.py)
   - `hooks.json` defines cursor-agent hooks
   - Shell scripts run automatically on events:
     - `beforeShellExecution`: Blocks git commits with secrets
     - `afterFileEdit`: Runs linters, tests (language-specific)
     - `stop`: Final validation (coverage, build)

5. **Infrastructure self-healing** (infra/healer.py)
   - Auto-starts Docker services if down
   - Runs database migrations if needed
   - Creates MinIO buckets if missing
   - Only runs for brownfield modes (enhancement, backlog)

## Operating Modes

### 1. Greenfield Mode
- **Purpose:** Build new project from scratch
- **Work source:** `feature_list.json` created by initializer
- **State tracking:** `feature_list.json` (`passing: true/false`)
- **Git:** Initialized in setup if not present

### 2. Enhancement Mode
- **Purpose:** Add features to existing project
- **Work source:** Spec file parsed for features (lines starting with `- `)
- **State tracking:** `.cursor/enhancement-state.json`
- **Infrastructure:** Self-healing runs on setup

### 3. Backlog Mode
- **Purpose:** Process Azure DevOps PBIs
- **Work source:** Azure DevOps API via MCP integration
- **State tracking:** `.cursor/backlog-state.json` + Azure DevOps updates
- **Special features:** Updates work item comments, marks "Done"

## Important Implementation Details

### Cursor-Agent Integration

The harness invokes `cursor-agent` CLI (not direct API):

```python
# cursor_harness/executor/cursor_executor.py
process = subprocess.Popen([
    "cursor-agent",
    "-p",                              # Prompt mode
    "--force",                         # Skip confirmations
    "--model", self.model,             # Model selection
    "--output-format", "stream-json",  # Streaming JSON
    "--stream-partial-output"
], cwd=self.project_dir, stdin=subprocess.PIPE, ...)
```

**Requirements:**
- Cursor IDE must be logged in (provides auth)
- OR set `ANTHROPIC_API_KEY` environment variable
- Verifies `cursor-agent --version` succeeds during init

### Hooks System (Security Critical)

The hooks system creates `.cursorignore` to prevent agent access to:
- `.env` files and variants (`.env.*`, `*.env`)
- Credentials (`credentials.json`, `secrets.json`, service account files)
- Keys and certificates (`.key`, `.pem`, `id_rsa`, etc.)
- Backup files (`.bak`, `.backup`) - prevents leaks like AutoGraph's `.env.bak` incident

**Hook types:**
- `beforeShellExecution` - Gates risky operations (git commits with secrets)
- `afterFileEdit` - Auto-format, quick checks (language-specific)
- `stop` - Final validation before session ends

Hooks are run automatically by cursor-agent - the harness doesn't need to invoke them manually.

### Continuation Mode

For large projects (>50 features), continuation mode activates:
- Uses special continuation prompts
- Prevents context overflow
- Detected automatically: `core.py:86-97`

```python
if len(features) > 50:
    self.is_continuation = True
```

### Loop Detection

`loop_detector.py` prevents infinite loops via:
- Session timeout (default: 60 minutes)
- Repeated file reads (max: 5 reads of same file)
- No progress timeout (10 minutes of inactivity)

Integrated into executor: `core.py:307`

### Validation Layers

1. **During execution:** Hooks run automatically (linting, quick tests)
2. **After feature:** Work item validation (tests pass, code created)
3. **Final:** `_final_validation()` - comprehensive tests, secrets scan

## Common Patterns When Editing

### Adding a New Mode

1. Create prompts in `cursor_harness/prompts/`:
   - `{mode}_initializer.md`
   - `{mode}_coding.md`
   - Optional: `{mode}_continuation.md`

2. Update `_build_prompt()` in `core.py`:
   ```python
   elif self.mode == "newmode":
       if self.is_first_session:
           prompt_file = prompts_dir / "newmode_initializer.md"
       else:
           prompt_file = prompts_dir / "newmode_coding.md"
   ```

3. Add CLI command in `cli.py`:
   ```python
   newmode = subparsers.add_parser('newmode', help='Description')
   newmode.add_argument('project_dir', type=Path)
   ```

### Modifying Validation

Edit validators in `cursor_harness/validators/`:
- `test_runner.py` - Test execution logic
- `secrets_scanner.py` - Secret detection patterns
- `e2e_tester.py` - End-to-end Puppeteer tests

Update `_final_validation()` in `core.py:379-409` to call new validators.

### Adjusting Hooks

Edit `cursor_harness/hooks.py`:
- `setup_default_hooks()` - Hook creation logic
- `_create_cursorignore()` - Security ignore patterns

The hooks system is critical for security - be careful when modifying `.cursorignore` patterns.

## Critical Constraints

1. **Never skip hooks** - They provide automatic validation and security
2. **Never commit secrets** - `.cursorignore` and `block-secrets.sh` prevent this
3. **Keep core simple** - v3.0 is intentionally ~1,100 lines vs v2.x's 10,000+
4. **Trust Anthropic's pattern** - Two-prompt system (initializer + coding) is proven
5. **One feature at a time** - Coding sessions implement exactly ONE work item
6. **Fresh context** - Each coding session starts with fresh context (no memory from previous session)

## State Files Reference

- `feature_list.json` - Greenfield/Backlog work items (`passing: true/false`)
- `.cursor/enhancement-state.json` - Enhancement work items (`completed: true/false`)
- `.cursor/backlog-state.json` - Azure DevOps PBIs with org/project metadata
- `cursor-progress.txt` - Human-readable session notes
- `.cursor/completed_*.json` - Completion records per work item
- `.cursor/hooks.json` - Cursor hooks configuration
- `init.sh` - Development server startup script (created by initializer)

## Known Limitations

1. **No bugfix mode yet** - Only greenfield/enhancement/backlog implemented
2. **E2E validators exist but not integrated** - `e2e_tester.py` not wired into main loop
3. **Multi-agent workflow optional** - Feature exists but not activated
4. **Limited test coverage** - Only `tests/test_simple.py` validates core loop

## Design Philosophy (from DESIGN.md)

v3.0 exists because v2.x was over-engineered (10K+ lines, multi-agent orchestration, complex state management). v3.0 returns to Anthropic's simple demo (~200 lines) but extends it for production:

- ✅ Simple core loop (Anthropic's pattern)
- ✅ Multiple modes (greenfield → backlog)
- ✅ Real validation (E2E, security)
- ✅ Production-ready (self-healing, loop detection)

**Never move forward with broken code!** Each day's work must be tested before proceeding.
