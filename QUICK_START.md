# cursor-harness - Quick Start Guide

## 🚀 For Your Team (Bayer/Internal)

### Installation (One Command)

```bash
pipx install git+https://github.com/nirmalarya/cursor-harness
```

**That's it!** The `cursor-harness` command is now available system-wide.

### Verify Installation

```bash
cursor-harness --version
# Should show: cursor-harness 2.3.0-dev
```

---

## 🌍 For Engineering Community (Open Source)

### Prerequisites

- Python 3.10 or higher
- pipx (recommended) or pip

**Install pipx if you don't have it:**
```bash
# macOS
brew install pipx

# Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Windows
py -m pip install --user pipx
```

### Installation

```bash
# Install from GitHub
pipx install git+https://github.com/nirmalarya/cursor-harness

# Verify
cursor-harness --version
```

---

## 📖 Usage Examples

### 1. Start New Project

```bash
cursor-harness greenfield ./my-app --spec specs/todo_api.txt
```

### 2. Add Features to Existing Project

```bash
cursor-harness enhance ./existing-app --spec specs/new_features.txt
```

### 3. Fix Bugs

```bash
cursor-harness bugfix ./app --spec specs/bugs.txt
```

### 4. Validate Existing Code

```bash
cursor-harness validate ./legacy-app
# Systematically tests all features
# Builds comprehensive test suite
```

### 5. Process Azure DevOps Backlog (Enterprise!)

```bash
cursor-harness backlog ./togglr \
  --project togglr \
  --epic Epic-3 \
  --max-pbis 5

# Processes 5 PBIs autonomously!
# Updates Azure DevOps automatically!
```

---

## 🔧 Configuration

### For Azure DevOps (Enterprise Teams)

**Environment variables (optional):**
```bash
export AZURE_DEVOPS_ORG="your-org"
export AZURE_DEVOPS_PROJECT="your-project"

# Then simpler commands:
cursor-harness backlog ./app --epic Epic-3
```

### For Anthropic API (Required)

**Set API key:**
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Get your key from: https://console.anthropic.com/

---

## 📚 Documentation

- [Installation Guide](INSTALL.md) - Detailed installation options
- [Multi-Agent Workflow](docs/MULTI_AGENT_WORKFLOW_MODE.md) - How multi-agent works
- [Azure DevOps Integration](docs/AUTONOMOUS_BACKLOG_MODE.md) - Backlog processing
- [Contributing](CONTRIBUTING.md) - How to contribute

---

## 🆘 Troubleshooting

### Command not found after install

```bash
# Ensure pipx path is in your shell
pipx ensurepath

# Or add manually to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

### Import errors

```bash
# Reinstall with dependencies
pipx uninstall cursor-harness
pipx install git+https://github.com/nirmalarya/cursor-harness
```

### Permission errors

```bash
# Use pipx (recommended) instead of pip
# pipx creates isolated environments
```

---

## 🎯 Quick Test

```bash
# Test the CLI works
cursor-harness --help

# Test on a sample project
cursor-harness greenfield ./test-app

# Check it's running
ls test-app/
# Should see: spec/, src/, tests/, etc.
```

---

## 🌟 Next Steps

1. Read [Multi-Agent Workflow](docs/MULTI_AGENT_WORKFLOW_MODE.md)
2. Try on a small project first
3. Explore Azure DevOps integration for enterprise
4. Join discussions on GitHub Issues

---

**Questions?** Open an issue: https://github.com/nirmalarya/cursor-harness/issues

**Built with ❤️ for autonomous software development**

