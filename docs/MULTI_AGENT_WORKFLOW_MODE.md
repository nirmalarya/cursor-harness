# Multi-Agent Workflow Mode - Generic Implementation

**Vision:** Any project can use multi-agent workflow (not just Togglr!)

---

## 🎯 Concept

**Multi-agent workflow:**
```
Backlog → Architect → Engineer → Tester → CodeReview → Security → DevOps → Done
```

**This is a PATTERN, not Togglr-specific!**

**Should work for:**
- ✅ Togglr (feature flags platform)
- ✅ AutoGraph (diagramming platform)
- ✅ SHERPA (orchestration platform)
- ✅ Any web app, API, CLI, desktop app

---

## 🏗️ Generic Agent Definitions

### **Architect Agent (Project-Agnostic)**

**Role:** Design technical solution

**Process:**
1. Read requirement (from PBI, spec, or issue)
2. Analyze technical approach
3. Create ADR (Architecture Decision Record)
4. Define:
   - API contracts (if applicable)
   - Database schema (if applicable)
   - Component architecture
   - Technology choices
   - Performance targets
5. Commit ADR to `docs/adrs/`

**Adapts to project:**
- Web app: API design, frontend components
- CLI: Command structure, config format
- Library: Public API design
- Mobile: Screen flow, state management

**Quality gate:** ADR created, design documented

---

### **Engineer Agent (Project-Agnostic)**

**Role:** Implement feature with TDD

**Process:**
1. Read ADR (from Architect)
2. **RED:** Write failing tests first
3. **GREEN:** Implement minimum code to pass
4. **REFACTOR:** Clean up while keeping tests green
5. Ensure ≥80% test coverage
6. Follow project coding standards

**Adapts to project:**
- TypeScript: Jest/Vitest tests
- Python: pytest tests
- Go: testing package tests
- Any language: Test-first approach

**Quality gate:** Tests pass, ≥80% coverage, code quality

---

### **Tester Agent (Project-Agnostic)**

**Role:** Comprehensive testing & validation

**Process:**
1. Run unit tests (verify ≥80% coverage)
2. Create E2E tests:
   - Web: Puppeteer/Playwright
   - API: curl/httpie tests
   - CLI: Command execution tests
   - Desktop: UI automation tests
3. Test edge cases
4. Verify error handling
5. Grade implementation (A/B/C/D/F)

**Adapts to project:**
- Web UI: Browser E2E tests
- REST API: API integration tests
- CLI: Command tests
- Library: Example usage tests

**Quality gate:** All tests pass, E2E coverage, Grade ≥B

---

### **CodeReview Agent (Project-Agnostic)**

**Role:** Code quality enforcement

**Process:**
1. Check naming conventions (project-specific)
2. Verify no `any` types (TypeScript)
3. Check error handling
4. Verify documentation (JSDoc/docstrings/godoc)
5. Check for anti-patterns
6. Score 1-10

**Adapts to project:**
- TypeScript: ESLint, Prettier, no `any`
- Python: Ruff, Black, type hints
- Go: gofmt, golint, go vet
- Any: Project-specific linting

**Quality gate:** Score ≥7/10

---

### **Security Agent (Project-Agnostic)**

**Role:** Security validation

**Process:**
1. OWASP Top 10 review
2. Check auth/authz (if applicable)
3. Input validation
4. Secrets scanning
5. Dependency scan (`npm audit`, `pip audit`, etc.)
6. Score 1-10

**Adapts to project:**
- Web: XSS, CSRF, SQL injection
- API: Auth, rate limiting, input validation
- CLI: File permissions, command injection
- Any: OWASP principles apply

**Quality gate:** Score ≥7/10, no critical vulnerabilities

---

### **DevOps Agent (Project-Agnostic)**

**Role:** Deployment readiness

**Process:**
1. Verify build succeeds
2. Run all tests
3. Check linting passes
4. Visual smoke test (if UI)
5. Verify no regressions
6. Ready for deployment

**Adapts to project:**
- TypeScript: `pnpm build`, `pnpm test`, `pnpm lint`
- Python: `python -m build`, `pytest`, `ruff`
- Go: `go build`, `go test`, `golangci-lint`
- Any: Project-specific commands

**Quality gate:** Build success, tests pass, deployment ready

---

## 🔄 How It Works for Different Projects:

### **For Togglr (TypeScript monorepo):**
```
Architect: Creates ADR for new feature
Engineer: TDD with Jest, implements in packages/control-plane
Tester: Playwright E2E tests
CodeReview: ESLint, checks for `any` types
Security: OWASP scan, `pnpm audit`
DevOps: `pnpm build`, `pnpm test`, smoke test
```

### **For AutoGraph (Python + Next.js):**
```
Architect: Creates ADR for diagram feature
Engineer: TDD with pytest (backend) + Jest (frontend)
Tester: Puppeteer E2E tests
CodeReview: Ruff (Python), ESLint (TypeScript)
Security: Bandit (Python), npm audit (Node)
DevOps: Docker build, full test suite
```

### **For SHERPA (Python CLI):**
```
Architect: Creates ADR for CLI command
Engineer: TDD with pytest
Tester: CLI command execution tests
CodeReview: Ruff, type hints
Security: Bandit, secrets scan
DevOps: Package build, CLI tests
```

**Same workflow, adapts to each project!** 🎯

---

## 📋 What This Means:

**cursor-harness becomes:**
```
cursor-autonomous-harness/
├── prompts/
│   ├── multi-agent/           ← NEW! Generic agents
│   │   ├── architect_agent.md
│   │   ├── engineer_agent.md
│   │   ├── tester_agent.md
│   │   ├── code_review_agent.md
│   │   ├── security_agent.md
│   │   └── devops_agent.md
│   └── ...
├── modes/
│   ├── greenfield.py
│   ├── enhancement.py
│   ├── bugfix.py
│   └── multi_agent_workflow.py  ← NEW!
└── integrations/
    ├── azure_devops.py           ← NEW!
    └── github_issues.py          ← Future
```

---

## ✅ Benefits:

**One harness for everything:**
- ✅ Greenfield (spec file) → New projects
- ✅ Enhancement (spec file) → Add features
- ✅ Bugfix (spec file) → Fix issues
- ✅ **Multi-agent workflow (PBI/Issue)** → Enterprise SDLC
- ✅ **Autonomous backlog (Azure DevOps)** → Continuous delivery

**Works with:**
- ✅ Spec files (standalone projects)
- ✅ Azure DevOps (enterprise teams)
- ✅ GitHub Issues (open source)
- ✅ Linear (startups)
- ✅ Any issue tracker (adaptable!)

---

## 🎊 Your Vision is Perfect:

**Extract Togglr's multi-agent workflow → Make it generic → Add to cursor-harness → Use everywhere!**

**Result:**
- Togglr uses it ✅
- Future projects use it ✅
- One workflow, many projects ✅

**Want me to start extracting Togglr's agents and making them generic?** 🚀
