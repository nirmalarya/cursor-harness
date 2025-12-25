# Contributing to cursor-harness

Thank you for your interest in contributing! 🎉

## 🚀 Quick Start for Contributors

### Setup Development Environment

```bash
# Clone the repo
git clone https://github.com/nirmalarya/cursor-harness
cd cursor-harness

# Install in editable mode
pipx install -e .

# Verify
cursor-harness --version
```

### Make Changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes in `cursor_harness/`
3. Test immediately (editable install!)
4. Commit: `git commit -m "feat: your feature"`
5. Push: `git push origin feature/your-feature`
6. Open PR on GitHub

---

## 📋 Areas for Contribution

### High Priority

- **Azure DevOps MCP Integration** - Replace placeholder MCP calls with real implementation
- **GitHub Issues Integration** - Add GitHub as backlog source (like Azure DevOps)
- **Linear Integration** - Add Linear as backlog source
- **Test Quality Improvements** - Enhance test generation and validation
- **Documentation** - More examples, tutorials, guides

### Medium Priority

- **Additional Agents** - UX agent, Performance agent, Accessibility agent
- **More Quality Gates** - Performance benchmarks, accessibility checks
- **Output Formatter Improvements** - Better visualizations
- **Progress Dashboard** - Web UI to monitor harness runs

### Low Priority

- **Additional Language Support** - Rust, Java, C#, etc.
- **Cloud Integration** - AWS, GCP, Azure deployment helpers
- **Telemetry** - Usage analytics (opt-in)

---

## 🧪 Testing Your Changes

```bash
# Test CLI still works
cursor-harness --help

# Test on sample project
cursor-harness greenfield ./test-project --spec cursor_harness/specs/simple_todo_spec.txt

# Verify no regressions
# (Full test suite coming soon!)
```

---

## 📝 Code Style

- **Python**: Follow PEP 8
- **Type hints**: Use for all functions
- **Docstrings**: Required for public functions
- **Comments**: Explain WHY, not WHAT

---

## 🤝 Pull Request Process

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Update documentation if needed
6. Submit PR with clear description
7. Wait for review

---

## 💬 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Ideas**: Open a GitHub Issue with "enhancement" label

---

## 🙏 Thank You!

Every contribution helps make autonomous software development better!

**Contributors will be listed in CONTRIBUTORS.md**

