# Project Structure - Mandatory Organization

**All projects MUST follow this structure!**

---

## 📁 Required Directory Structure

```
project/
├── spec/                      # ALL SPECIFICATIONS (source of truth!)
│   ├── app_spec.txt          # Greenfield: Full app specification
│   ├── enhancement_spec.txt  # Enhancement: New features to add
│   ├── bugfix_spec.txt       # Bugfix: Issues to fix
│   └── feature_list.json     # Generated: All features (tracked by agent)
├── src/ or package_name/      # Source code (backend/frontend)
│   ├── api/
│   ├── core/
│   ├── models/
│   └── ...
├── tests/                     # ALL test files here
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── e2e/                  # End-to-end tests (Playwright/Puppeteer)
│   └── fixtures/             # Test fixtures and helpers
├── .sessions/                 # Session artifacts (gitignored!)
│   ├── SESSION_*.md          # Session summaries
│   ├── claude-progress.txt   # Progress notes
│   └── baseline_features.txt # Regression baseline
├── scripts/                   # Utility scripts
│   ├── setup/               # Setup and initialization
│   ├── deploy/              # Deployment scripts
│   └── utils/               # Utility scripts
├── docs/                      # User-facing documentation
│   ├── architecture/        # Architecture docs
│   ├── api/                 # API documentation
│   └── guides/              # User guides
├── infrastructure/            # Infrastructure as code (if applicable)
│   ├── docker/
│   ├── k8s/
│   └── terraform/
├── logs/                      # Log files (gitignored)
└── (< 20 essential config files in root)
    ├── README.md
    ├── package.json or requirements.txt
    ├── docker-compose.yml
    ├── .gitignore
    ├── .env.example
    └── ...
```

---

## 🎯 Auto-Create Structure (Initializer)

**Add to initializer_prompt.md:**

```bash
# STEP: CREATE PROJECT STRUCTURE

echo "Creating project directory structure..."

# Create essential directories
mkdir -p src
mkdir -p tests/{unit,integration,e2e,fixtures}
mkdir -p .sessions
mkdir -p scripts/{setup,deploy,utils}
mkdir -p docs/{architecture,api,guides}
mkdir -p logs

# Create .gitignore
cat > .gitignore << 'EOF'
# Session artifacts (build-time, not source)
.sessions/
SESSION_*.md
*-progress.txt

# Logs (never commit!)
logs/
*.log

# Environment (never commit!)
.env
.env.local

# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
.venv/

# Build outputs
dist/
build/
.next/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
EOF

echo "✅ Project structure created"
```

---

## 🎯 Enforce Organization (Every Session)

**Add to coding_prompt.md (before commit):**

```bash
# STEP: ENFORCE FILE ORGANIZATION

echo "Checking file organization..."

# Count root directory files
root_files=$(ls -1 2>/dev/null | grep -v "^\." | wc -l)

if [ "$root_files" -gt 20 ]; then
    echo "⚠️  Root directory has $root_files files (max: 20)"
    echo "ORGANIZING FILES NOW..."
    
    # Move misplaced files automatically
    
    # All test files → tests/
    find . -maxdepth 1 -name "test_*.py" -exec mv {} tests/unit/ \; 2>/dev/null
    find . -maxdepth 1 -name "test_*.ts" -exec mv {} tests/e2e/ \; 2>/dev/null
    find . -maxdepth 1 -name "*_test.py" -exec mv {} tests/unit/ \; 2>/dev/null
    find . -maxdepth 1 -name "*.test.ts" -exec mv {} tests/e2e/ \; 2>/dev/null
    
    # All session files → .sessions/
    find . -maxdepth 1 -name "SESSION_*.md" -exec mv {} .sessions/ \; 2>/dev/null
    find . -maxdepth 1 -name "*_COMPLETE.md" -exec mv {} .sessions/ \; 2>/dev/null
    find . -maxdepth 1 -name "*_SUMMARY.md" -exec mv {} .sessions/ \; 2>/dev/null
    
    # Debug/utility scripts → scripts/
    find . -maxdepth 1 -name "debug_*.py" -exec mv {} scripts/utils/ \; 2>/dev/null
    find . -maxdepth 1 -name "check_*.py" -exec mv {} scripts/utils/ \; 2>/dev/null
    find . -maxdepth 1 -name "verify_*.py" -exec mv {} scripts/utils/ \; 2>/dev/null
    find . -maxdepth 1 -name "analyze_*.py" -exec mv {} scripts/utils/ \; 2>/dev/null
    
    # Documentation → docs/
    find . -maxdepth 1 -name "*_GUIDE.md" -exec mv {} docs/guides/ \; 2>/dev/null
    find . -maxdepth 1 -name "*_ARCHITECTURE.md" -exec mv {} docs/architecture/ \; 2>/dev/null
    
    # Re-count
    root_files=$(ls -1 2>/dev/null | grep -v "^\." | wc -l)
    echo "✅ Organized! Root now has $root_files files"
fi

if [ "$root_files" -gt 25 ]; then
    echo "⚠️  Still too many files ($root_files) - manual review needed"
    ls -1
    echo ""
    echo "Please organize remaining files before committing!"
fi

echo "✅ File organization check complete"
```

**Runs automatically before every commit!**

---

## 🎯 Enhanced .gitignore (Auto-Generated)

```gitignore
# Session artifacts (build-time, not source)
.sessions/
SESSION_*.md
*-progress.txt
baseline_features.txt
feature_list.json.bak

# Logs (NEVER commit!)
logs/
*.log
*.log.*

# Environment variables (NEVER commit!)
.env
.env.local
.env.*.local

# Dependencies
node_modules/
__pycache__/
*.py[cod]
*.so
venv/
.venv/
*.egg-info/

# Build outputs
dist/
build/
.next/
target/

# Test artifacts
.pytest_cache/
.coverage
htmlcov/
test_results/
playwright-report/
screenshots/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
.DS_Store?
._*

# Databases (local dev only)
*.db
*.db-journal
```

---

## 📋 What Gets Created When

### Session 1 (Initializer):
```bash
# Creates:
project/
├── src/                    # Empty, ready for code
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .sessions/              # For build artifacts
├── scripts/
├── docs/
├── logs/
├── .gitignore             # Comprehensive
├── feature_list.json      # In .sessions/ (not root!)
└── README.md              # Basic
```

### Sessions 2+ (Coding):
- Source code → `src/` or `package_name/`
- Tests → `tests/unit/`, `tests/e2e/`, etc.
- Scripts → `scripts/`
- Docs → `docs/`
- Session notes → `.sessions/`
- Logs → `logs/`

**Root stays clean (< 20 files)!**

---

## ✅ This Prevents SHERPA/AutoGraph Mess!

**SHERPA v1.0 had:** 150+ files in root (messy!)  
**With v2.0:** < 20 files in root (clean!)

**AutoGraph v3.0 had:** 358 files in root (disaster!)  
**With v2.0:** < 20 files in root (professional!)

---

Let me add this to the prompts now:

<function_calls>
<invoke name="search_replace">
<parameter name="file_path">/Users/nirmalarya/Workspace/autonomous-harness/prompts/initializer_prompt.md
