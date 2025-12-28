# cursor-harness v3.0

**Simple, Reliable, Production-Ready Autonomous Coding**

Based on [Anthropic's effective harness pattern](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Design

Based on Anthropic's two-agent pattern:

**1. Initializer Agent** (First session)
- Sets up environment
- Creates feature list
- Initializes git
- Creates startup script

**2. Coding Agent** (Subsequent sessions)
- Fresh context window (no memory)
- Reads progress files and git
- Implements ONE feature at a time
- Tests end-to-end
- Commits and updates progress

## Modes

- ✅ **Greenfield** - New projects (feature_list.json)
- ✅ **Enhancement** - Add to existing apps (enhancement_list.json)
- ✅ **Backlog** - Azure DevOps PBIs (feature_list.json from PBIs)

## Key Features

### 1. Anthropic's Proven Pattern
- Two-prompt system (initializer + coding)
- Incremental progress (one feature at a time)
- Clear artifacts (feature_list.json, cursor-progress.txt, git)
- Session-based (fresh context each time)

### 2. Production Enhancements
- Multiple modes (greenfield, enhancement, backlog)
- Self-healing infrastructure (Docker, DB, buckets)
- Real validation (tests, E2E, secrets scanning)
- Azure DevOps integration

### 3. Simple & Reliable
- ~1,100 lines total (vs 10,000+ in v2.x)
- Easy to understand and debug
- Uses Cursor's auth (no API key needed!)
- Tested pattern from Anthropic

## Architecture

```
cursor_harness/
├── core.py                      # Session orchestrator (~250 lines)
├── cli.py                       # CLI interface (~60 lines)
├── executor/
│   └── cursor_executor.py       # Claude executor (~250 lines)
├── prompts/
│   ├── initializer.md           # Greenfield session 1
│   ├── coding.md                # Greenfield sessions 2-N
│   ├── enhancement_initializer.md
│   ├── enhancement_coding.md
│   ├── backlog_initializer.md
│   └── backlog_coding.md
├── validators/
│   ├── test_runner.py           # Test execution (~100 lines)
│   └── secrets_scanner.py       # Security scanning (~100 lines)
└── infra/
    └── healer.py                # Infrastructure self-healing (~100 lines)
```

**Total: ~1,100 lines** (simple, maintainable)

## Development Plan

### Week 1: Core (Days 1-3)
- **Day 1:** Simple loop + feature_list.json
- **Day 2:** All modes (greenfield, enhancement, backlog)
- **Day 3:** Infrastructure self-healing

### Week 2: Validation (Days 4-7)
- **Day 4:** Puppeteer E2E testing
- **Day 5:** Security scanning
- **Day 6:** Quality gates
- **Day 7:** Integration testing (Togglr, AutoGraph, AI Trading)

### Week 3: Production (Days 8-10)
- **Day 8:** Multi-agent (optional feature)
- **Day 9:** Documentation
- **Day 10:** Hardening & week-long test

## Why v3.0?

### v1.0 (autonomous-harness)
- ✅ Works great for greenfield
- ❌ No brownfield support
- ❌ No E2E testing
- ❌ Missed CSS errors, exposed secrets

### v2.x (cursor-harness)
- ✅ Multi-agent workflow
- ✅ Azure DevOps integration
- ❌ Over-engineered (10K+ lines)
- ❌ Slow, loops, unreliable

### v3.0 (this!)
- ✅ Simple core (Anthropic's pattern)
- ✅ All modes (greenfield → backlog)
- ✅ Real validation (E2E, security)
- ✅ Production-ready

## Usage

```bash
# Greenfield
cursor-harness greenfield ./my-app --spec app_spec.txt

# Enhancement
cursor-harness enhance ./existing-app --feature "Add dark mode"

# Bugfix
cursor-harness bugfix ./existing-app --issue "Fix login bug"

# Backlog (Azure DevOps)
cursor-harness backlog ./project --org MyOrg --project MyProject
```

## Status

**Current:** Day 1 - Building simple core

**Next:** Test on simple project, then add modes

---

**Built to solve real production problems, not just demos!** 🚀

