# cursor-harness v3.0 - Modes Guide

## Overview

cursor-harness v3.0 supports 4 modes for different development scenarios:

| Mode | Use Case | Work Source | Status |
|------|----------|-------------|--------|
| **Greenfield** | New project from scratch | `feature_list.json` | ✅ Implemented |
| **Enhancement** | Add features to existing app | Spec file | ✅ Implemented |
| **Backlog** | Process Azure DevOps PBIs | Azure DevOps API | ✅ Implemented |
| **Bugfix** | Fix specific bugs | Spec file | ⚠️ TODO |

---

## 1. Greenfield Mode

**Use:** Building a new project from scratch

**How it works:**

```bash
# 1. Create project structure
mkdir my-new-app
cd my-new-app

# 2. Create feature list
cat > feature_list.json << 'EOF'
[
  {
    "id": "1",
    "title": "Create README",
    "description": "Create project README with overview",
    "passing": false
  },
  {
    "id": "2",
    "title": "Setup Python project",
    "description": "Create setup.py, requirements.txt",
    "passing": false
  },
  {
    "id": "3",
    "title": "Implement main feature",
    "description": "Core functionality with tests",
    "passing": false
  }
]
EOF

# 3. Create spec (optional)
cat > spec.txt << 'EOF'
# My New App

Build a Python CLI tool that does X, Y, Z.

## Requirements
- Python 3.9+
- Tests with pytest
- 80%+ coverage
EOF

# 4. Run harness
cursor-harness greenfield . --spec spec.txt
```

**What happens:**
1. Reads `feature_list.json`
2. Gets first feature where `passing: false`
3. Executes feature (uses Cursor's auth)
4. Validates (git changes, tests)
5. Marks `passing: true` in feature_list.json
6. Moves to next feature
7. Repeats until all features passing

**State tracking:**
- `feature_list.json` - progress (passing: true/false)
- `.cursor/completed_*.json` - completion records
- Git commits - each feature committed

---

## 2. Enhancement Mode (Brownfield)

**Use:** Adding features to existing project

**How it works:**

```bash
# 1. Go to existing project
cd ~/my-existing-app

# 2. Create enhancement spec
cat > enhancements.txt << 'EOF'
# Enhancements for My App

Add these features:
- Dark mode toggle
- Export to PDF
- User preferences panel
- Keyboard shortcuts
EOF

# 3. Run harness
cursor-harness enhance . --spec enhancements.txt
```

**What happens:**
1. Parses `enhancements.txt` for items (lines starting with `- `)
2. Creates `.cursor/enhancement-state.json`:
   ```json
   [
     {"id": "1", "title": "Dark mode toggle", "completed": false},
     {"id": "2", "title": "Export to PDF", "completed": false},
     ...
   ]
   ```
3. Gets first incomplete enhancement
4. Executes enhancement
5. Validates and commits
6. Marks `completed: true`
7. Moves to next

**State tracking:**
- `.cursor/enhancement-state.json` - completion state
- Existing codebase preserved
- Incremental commits per enhancement

---

## 3. Backlog Mode

**Use:** Processing Azure DevOps work items

**How it works:**

```bash
# 1. Go to project
cd ~/my-project

# 2. Run backlog mode
cursor-harness backlog . \
  --org Bayer-SMO-USRMT \
  --project togglr
```

**What happens:**
1. Fetches PBIs from Azure DevOps (using MCP):
   ```
   GET https://dev.azure.com/{org}/{project}/_apis/wit/workitems
   ```
2. Creates `.cursor/backlog-state.json`:
   ```json
   {
     "org": "Bayer-SMO-USRMT",
     "project": "togglr",
     "pbis": [
       {
         "id": "PBI-3.6.1",
         "numeric_id": 16750,
         "title": "Add flag description field",
         "description": "...",
         "acceptance_criteria": "...",
         "processed": false
       },
       ...
     ]
   }
   ```
3. Gets first unprocessed PBI
4. Executes PBI
5. Validates and commits
6. Updates Azure DevOps work item (via MCP)
7. Marks `processed: true`
8. Moves to next PBI

**State tracking:**
- `.cursor/backlog-state.json` - local state
- Azure DevOps - remote state (updated via MCP)
- Multi-agent workflow optional

**Azure DevOps integration:**
- Fetches work items
- Reads description, acceptance criteria
- Updates work item comments
- Marks work item "Done" when complete

---

## 4. Bugfix Mode

**Use:** Fixing specific bugs

**Status:** ⚠️ NOT YET IMPLEMENTED

**Planned:**

```bash
# Create bug spec
cat > bug.txt << 'EOF'
# Bug: Login fails with special characters

## Symptoms
- User can't login with email containing +
- Error: "Invalid email format"

## Expected
- Should accept RFC-compliant emails
- Including + . _ - characters

## Files
- src/auth/validator.ts
- tests/auth.test.ts
EOF

# Run bugfix mode
cursor-harness bugfix . --spec bug.txt
```

**TODO:**
- Implement `modes/bugfix.py`
- Add to CLI
- Bug-specific validation (regression tests)

---

## Mode Comparison

| Feature | Greenfield | Enhancement | Backlog | Bugfix |
|---------|------------|-------------|---------|--------|
| **Existing code?** | No | Yes | Yes | Yes |
| **Work source** | feature_list.json | Spec file | Azure DevOps | Spec file |
| **State file** | feature_list.json | enhancement-state.json | backlog-state.json | bugfix-state.json |
| **Remote tracking** | No | No | Yes (ADO) | Optional |
| **Multi-agent** | Optional | Optional | Yes | Optional |
| **Validation** | Tests, secrets | Tests, secrets, regression | Tests, E2E, ADO update | Regression tests |

---

## Common Workflow

**All modes follow same pattern:**

```python
while not complete:
    work_item = get_next_work()
    
    if not work_item:
        break
    
    # Execute
    success = execute_work_item(work_item)
    
    # Validate
    if success and validate(work_item):
        mark_complete(work_item)
    else:
        retry_or_skip(work_item)

# Final validation
run_tests()
scan_secrets()
```

**Key differences:**
- `get_next_work()` - different source per mode
- `mark_complete()` - different state tracking per mode
- `validate()` - mode-specific validation

---

## Current Implementation Status

### ✅ Working
- **Greenfield:** Full implementation, tested
- **Enhancement:** Full implementation, needs testing
- **Backlog:** Full implementation, needs MCP integration testing

### ⚠️ TODO
- **Bugfix:** Not yet implemented
- **Multi-agent:** Optional, not wired up yet
- **E2E testing:** Validators exist, not integrated

### 🔧 Next Steps
1. Test enhancement mode on real project
2. Test backlog mode with Azure DevOps
3. Implement bugfix mode
4. Wire up multi-agent as optional feature
5. Integrate E2E validators

---

## Usage Examples

### Quick Start - Greenfield

```bash
# Create simple TODO app
cursor-harness greenfield ./todo-app --spec todo-spec.txt
```

### Add Features - Enhancement

```bash
# Add dark mode to existing app
cursor-harness enhance ./my-app --spec dark-mode.txt
```

### Process Backlog

```bash
# Process all Togglr PBIs
cursor-harness backlog ~/workspace/togglr \
  --org Bayer-SMO-USRMT \
  --project togglr \
  --timeout 1440  # 24 hours
```

---

**Simple, clean, works!** 🚀

