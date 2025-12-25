# Installation Guide

## For Your Organization

**Install cursor-harness system-wide:**

### Option 1: Using pipx (Recommended)

```bash
# Install pipx if you don't have it
brew install pipx

# Install cursor-harness from GitHub
pipx install git+https://github.com/nirmalarya/cursor-autonomous-harness

# Or from local directory (development)
cd cursor-autonomous-harness
pipx install -e .
```

**Benefits:**
- ✅ Isolated environment (doesn't affect system Python)
- ✅ Available system-wide
- ✅ Easy to update
- ✅ Clean uninstall

**After install:**
```bash
cursor-harness --version  # Works from anywhere!
cursor-harness backlog /path/to/togglr --project togglr
```

---

### Option 2: Using pip with virtual environment

```bash
# Create venv
python3 -m venv ~/.cursor-harness-env

# Activate
source ~/.cursor-harness-env/bin/activate

# Install
pip install git+https://github.com/nirmalarya/cursor-autonomous-harness

# Add to PATH (in ~/.zshrc or ~/.bashrc)
echo 'export PATH="$HOME/.cursor-harness-env/bin:$PATH"' >> ~/.zshrc
```

---

### Option 3: Editable install (Development)

```bash
cd cursor-autonomous-harness
pip3 install -e . --break-system-packages

# Or with pipx for development
pipx install -e .
```

---

## For Organization-Wide Distribution

### Internal PyPI Server

**Setup internal package index:**

```bash
# Build package
cd cursor-autonomous-harness
python3 -m build

# Upload to internal PyPI
twine upload --repository-url https://pypi.your-company.com dist/*
```

**Users install:**
```bash
pip install cursor-harness --index-url https://pypi.your-company.com
```

---

### Git Installation (Simple)

**Add to your org's internal docs:**

```bash
# Install from GitHub
pip install git+https://github.com/nirmalarya/cursor-autonomous-harness

# Or specific version/tag
pip install git+https://github.com/nirmalarya/cursor-autonomous-harness@v2.3.0
```

---

## Verify Installation

```bash
# Check version
cursor-harness --version

# See all commands
cursor-harness --help

# Test on a project
cursor-harness backlog /path/to/togglr --project togglr --epic Epic-3 --max-pbis 1
```

---

## Update

```bash
# With pipx
pipx upgrade cursor-harness

# Or reinstall latest
pipx uninstall cursor-harness
pipx install git+https://github.com/nirmalarya/cursor-autonomous-harness
```

---

## Uninstall

```bash
# With pipx
pipx uninstall cursor-harness

# With pip
pip uninstall cursor-harness
```

