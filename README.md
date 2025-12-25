# cursor-harness

**Enterprise-grade autonomous coding harness with multi-agent workflow and Azure DevOps integration.**

[![Version](https://img.shields.io/badge/version-2.3.0--dev-blue)](https://github.com/nirmalarya/cursor-harness)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🎯 What is cursor-harness?

**Autonomous coding harness that:**
- Implements features from specifications
- Validates existing codebases
- Processes Azure DevOps backlogs continuously
- Runs multi-agent workflows (Architect → Engineer → Tester → CodeReview → Security → DevOps)
- Enforces 12 quality gates
- Works for any project type (web, API, CLI, desktop, mobile)

**Built on:** Anthropic's autonomous agent pattern (initializer + coder sessions)

---

## 🚀 Quick Start

### Installation

```bash
# Install with pipx (recommended)
pipx install git+https://github.com/nirmalarya/cursor-harness

# Or for development
git clone https://github.com/nirmalarya/cursor-harness
cd cursor-harness
pipx install -e .
```

### Usage

```bash
# Start new project
cursor-harness greenfield ./my-app --spec specs/todo_api.txt

# Add features to existing project
cursor-harness enhance ./my-app --spec specs/new_features.txt

# Fix bugs
cursor-harness bugfix ./my-app --spec specs/bugs.txt

# Process Azure DevOps backlog (Enterprise!)
cursor-harness backlog ./togglr --project togglr --epic Epic-3

# Validate existing codebase
cursor-harness validate ./my-app
```

---

## ✨ Features

### **12 Quality Gates**
1. Stop condition (no scope creep)
2. Service health checks
3. Database schema validation
4. Browser integration testing
5. E2E testing (Puppeteer/Playwright)
6. Zero TODOs policy
7. Security checklist
8. Regression testing
9. File organization
10. Test execution enforcement
11. Infrastructure validation
12. Smoke test suite

### **Multiple Modes**
- **Greenfield:** Build new projects from scratch
- **Enhancement:** Add features to existing projects
- **Bugfix:** Fix issues systematically
- **Validation:** Test existing code comprehensively
- **Autonomous Backlog:** Continuous Azure DevOps processing

### **Multi-Agent Workflow**
- **Architect:** Design & ADR creation
- **Engineer:** TDD implementation
- **Tester:** E2E tests & coverage
- **CodeReview:** Quality enforcement
- **Security:** OWASP compliance
- **DevOps:** Deployment readiness

---

## 🏢 Enterprise Features

### **Azure DevOps Integration**
- Fetch PBIs/Bugs from backlog
- Run multi-agent workflow
- Update work items after each agent
- Mark as Done automatically
- Continuous backlog processing

### **Generic & Adaptable**
Works for:
- Web apps (React, Vue, Angular, Next.js)
- APIs (FastAPI, Express, Django, Rails)
- CLIs (Click, Typer, Commander)
- Desktop apps (Electron, Tauri)
- Mobile apps (React Native, Flutter)
- Any tech stack!

---

## 📖 Documentation

- [Installation Guide](INSTALL.md)
- [Multi-Agent Workflow](docs/MULTI_AGENT_WORKFLOW_MODE.md)
- [Autonomous Backlog Mode](docs/AUTONOMOUS_BACKLOG_MODE.md)
- [Anthropic Harness Pattern](docs/MULTI_AGENT_WITH_HARNESS_PATTERN.md)
- [TODO List](TODO_FOR_TOGGLR_INTEGRATION.md)

---

## 🎓 Examples

### **Validate Existing Project**
```bash
cursor-harness validate ./my-legacy-app
# Marks all features unverified
# Systematically tests each one
# Builds comprehensive test suite
# Result: Fully validated codebase!
```

### **Process Epic from Azure DevOps**
```bash
cursor-harness backlog ./enterprise-app \
  --project my-project \
  --epic Epic-3 \
  --max-pbis 10

# Processes 10 PBIs autonomously
# Each through full multi-agent workflow
# Updates Azure DevOps automatically
# No human intervention needed!
```

---

## 🏗️ Architecture

**Based on Anthropic's autonomous agent pattern:**
- **Session 1:** Initializer (plan work, generate feature_list.json)
- **Session 2+:** Coder (implement features sequentially)
- **Stops:** Automatically at 100% completion

**Multi-agent mode:**
- Each agent runs full harness (not just one session!)
- Architect: 6 sessions, Engineer: 11 sessions, Tester: 8 sessions
- Total: 35-50 sessions per PBI
- Respects the foundation pattern!

---

## 🤝 Contributing

Contributions welcome!

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📊 Project Status

- **Version:** 2.3.0-dev
- **Status:** Beta (production-ready, actively developed)
- **Tested on:** AutoGraph (658 features), SHERPA (165 features)
- **Used for:** Togglr (enterprise feature flag platform)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Built on [Anthropic's autonomous agent pattern](https://docs.anthropic.com/)
- Inspired by enterprise SDLC best practices
- Tested on real-world projects

---

## 🔗 Links

- **Repository:** https://github.com/nirmalarya/cursor-harness
- **Issues:** https://github.com/nirmalarya/cursor-harness/issues
- **Sister Project:** [autonomous-harness](https://github.com/nirmalarya/autonomous-harness) (Claude Agent SDK version)

---

**Built with ❤️ for autonomous software development**
