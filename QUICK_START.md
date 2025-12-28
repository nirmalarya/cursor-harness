# cursor-harness v3.0 - Quick Start

## Installation

```bash
pipx install -e /Users/nirmalarya/Workspace/cursor-harness-v3
```

## Greenfield Mode (New Project)

```bash
# 1. Create spec
cat > /tmp/my-app-spec.txt << 'SPEC'
# Todo App

Build a CLI todo application:
- Add todos
- List todos  
- Mark complete
- Delete todos

Python 3.9+, JSON storage, pytest tests
SPEC

# 2. Run harness
cursor-harness greenfield /tmp/my-todo-app --spec /tmp/my-app-spec.txt

# 3. What happens:
#    Session 1: Creates feature_list.json, init.sh, git
#    Sessions 2-N: Implements features one by one
```

## Enhancement Mode (Existing Project)

```bash
# 1. Create enhancement spec
cat > /tmp/enhancements.txt << 'SPEC'
Add these features:
- Dark mode toggle
- Export to PDF
- Keyboard shortcuts
SPEC

# 2. Run harness
cursor-harness enhance ~/my-existing-app --spec /tmp/enhancements.txt

# 3. What happens:
#    Session 1: Creates enhancement_list.json
#    Sessions 2-N: Adds enhancements one by one
```

## Backlog Mode (Azure DevOps)

```bash
# Run harness
cursor-harness backlog ~/my-project \
  --org Bayer-SMO-USRMT \
  --project togglr

# What happens:
#   Session 1: Fetches PBIs, creates feature_list.json
#   Sessions 2-N: Processes PBIs one by one
#   Updates Azure DevOps when complete
```

## How It Works

**Anthropic's Two-Prompt Pattern:**

1. **Session 1 (Initializer)**
   - Creates feature_list.json (all features, passes: false)
   - Creates init.sh (start server)
   - Creates cursor-progress.txt (tracking)
   - Initializes git

2. **Sessions 2-N (Coding)**
   - Reads progress + git logs
   - Picks ONE feature (passes: false)
   - Implements with TDD
   - Tests end-to-end
   - Commits changes
   - Updates cursor-progress.txt
   - Marks feature passes: true

3. **Completion**
   - When all features passes: true
   - Runs final validation (tests, secrets)
   - Done!

## Artifacts Created

- `feature_list.json` - Progress tracking
- `cursor-progress.txt` - Session notes
- `init.sh` - Start development server
- `.cursor/` - State files
- Git commits - Full history

## Troubleshooting

**"No authentication found"**
- Login to Cursor IDE
- OR set `export ANTHROPIC_API_KEY=sk-...`

**"Feature not marked as passing"**
- Check cursor-progress.txt for errors
- Check git log for commits
- Verify feature_list.json updated

**"Server won't start"**
- Check init.sh script
- Verify dependencies installed
- Check Docker services (if applicable)

## Version Comparison

- **v2.3.0** - Stable, greenfield only, 2.5K lines
- **v2.5.0** - Complex, all modes, 10K lines, slow
- **v3.0.0-beta** - Simple, all modes, 2K lines, fast ✅

---

**Simple. Proven. Production-ready.** 🚀
