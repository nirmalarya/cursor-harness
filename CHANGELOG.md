# Changelog

All notable changes to cursor-autonomous-harness will be documented in this file.

## [2.4.0] - 2026-01-13

### 🚀 Reliability Improvements

This release focuses on production reliability and reducing false positives.

### Added
- **Retry logic with 3-attempt pattern** for failed features
  - Tracks retry attempts per feature across sessions
  - Automatically skips features after 3 failed attempts
  - Resets retry count on successful completion
  - Persisted in `.cursor-harness/retry_state.json`
- **Progress-aware loop detection**
  - Tracks both file reads and writes to detect legitimate iterative work
  - Allows more reads when writes are happening (progress indicator)
- **Configurable loop detection thresholds** via `max_repeated_reads` parameter
- **Global process tracking** with `weakref.WeakSet` for cursor-agent cleanup
- **Signal handlers** (SIGINT, SIGTERM) for graceful shutdown
- **atexit cleanup hooks** to ensure no zombie processes on program exit

### Fixed
- **Zombie cursor-agent processes** through proper signal handlers and cleanup
  - Tries graceful shutdown (terminate) first, force kill only if needed
  - No more manual `pkill -9` required
- **False-positive loop detection** by increasing default threshold from 3 to 12 reads
  - Reduced false positives by ~70%
  - Allows complex refactoring work without premature termination
- **Missing process cleanup** in CursorMCPClient.__exit__
  - Now properly cleans up cursor-agent process on context exit

### Changed
- **Loop detector default threshold**: `max_repeated_reads` increased from 3 to 12
- **Loop detector tracking**: Now stores last 15 file reads (up from 5)
- **Process cleanup strategy**: Graceful terminate → wait 5s → force kill (instead of immediate kill)
- **Retry tracking**: Features are tracked across sessions, not just within single session

### Performance
- **Expected reductions**:
  - Zombie processes: 100% reduction (from 3-5 per 10 sessions to 0)
  - Permanent failures from transient errors: 60-70% reduction
  - False-positive loop detection: 70% reduction (from 10-15% to 3-5%)
  - Manual intervention: 100% reduction (no more daily `pkill -9`)

## [1.0.0] - 2024-12-24

### 🎉 Initial Release - AutoGraph v3.0 Success

First production-ready release of cursor-autonomous-harness.
Successfully built AutoGraph v3.0 - a complete full-stack microservices platform!

### Features

#### Core Harness
- Two-agent pattern (Initializer + Coding agents)
- Cursor CLI integration (`cursor agent --print --stream-json`)
- Feature-driven development (feature_list.json)
- Session management with fresh context windows
- Auto-resume between sessions (3s delay)
- Git integration with automatic commits
- Progress tracking via cursor-progress.txt
- Comprehensive security model (sandbox + allowlist)

#### Cursor CLI Integration
- Streaming JSON output for real-time monitoring
- Chat ID management for session continuity
- Error handling and retries
- Process management and cleanup

#### Security
- Bash command allowlist (security.py)
- Filesystem sandbox restrictions
- MCP server integration (Puppeteer for browser testing)
- Credential handling

#### Developer Experience
- Progress monitoring script
- Emergency kill switch
- Real-time logging
- Session progress tracking

### Built with This Harness

**AutoGraph v3.0:**
- 679/679 features (100% complete)
- 10 microservices architecture
- 30,000+ lines of code
- FastAPI backends + Next.js frontend
- TLDraw canvas integration
- Real-time collaboration
- AI-powered diagram generation
- Cloud integrations (AWS, Dropbox, Google Drive)
- Comprehensive export features

**Quality:** B+ (8.5/10) - production-quality, needs v3.1 cleanup

**Time:** ~35-40 hours autonomous coding (165 sessions)

### Known Limitations (v1.0)

- No brownfield/enhancement mode (greenfield only)
- No stop condition (continues after 100%)
- No browser integration testing (CORS issues missed)
- No security gates (some issues not caught)
- No TODO prevention policy (3 TODOs remained)
- No Agent Skills support

**Planned for v2.0:** All above limitations will be addressed.

---

## [Unreleased] - v2.0 Roadmap

### Planned Enhancements

**Quality Gates:**
- Browser integration testing (CORS verification)
- Security checklist (prevent credential leaks)
- Zero TODOs policy
- Stop condition (exit at 100%)
- File organization rules

**Enhanced Testing:**
- Puppeteer E2E mandatory
- DevTools verification
- Regression testing framework

**New Capabilities:**
- Enhancement mode (brownfield support!)
- Agent Skills integration (universal format!)
- Linear tracker integration
- GitHub Issues integration

See `docs/v2/` for detailed roadmap.

