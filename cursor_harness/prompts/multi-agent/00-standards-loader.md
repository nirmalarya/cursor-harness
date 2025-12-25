# Standards Loader - Find Project Standards

**Before running any agent, load project standards (if they exist)**

---

## 🔍 Auto-Detect Standards

**Check common locations:**

```bash
# Check if project has standards
find . -type d -name "standards" 2>/dev/null | head -5

# Common patterns:
# - docs/standards/
# - .standards/
# - standards/
# - .github/standards/
```

**If found:**
- Read and reference them in agent prompts
- Follow project conventions

**If not found:**
- Use generic best practices
- Follow language conventions
- Create standards directory (suggest to user)

---

## 📋 Standard Files to Look For:

**Coding:**
- `coding-guidelines.md` or `CODING_GUIDELINES.md`
- `style-guide.md`
- `.eslintrc`, `.prettierrc`, `pyproject.toml`, etc.

**Testing:**
- `testing-standards.md` or `TESTING.md`
- `jest.config.js`, `playwright.config.ts`
- Test coverage thresholds in config

**Security:**
- `security-requirements.md` or `SECURITY.md`
- `.github/SECURITY.md`
- OWASP guidelines

**Infrastructure:**
- `infrastructure-as-code.md` or `INFRASTRUCTURE.md`
- Terraform/Kubernetes configs
- Docker best practices

**Git:**
- `git-workflow.md` or `CONTRIBUTING.md`
- `.github/CONTRIBUTING.md`
- Commit message format

---

## 🎯 Usage in Agent Prompts:

**Instead of hardcoding:**
```markdown
❌ [Coding Guidelines](../../docs/standards/coding-guidelines.md)
```

**Use dynamic:**
```markdown
✅ Check for project coding standards:
- If `docs/standards/coding-guidelines.md` exists: Follow it
- If `.github/CODING_GUIDELINES.md` exists: Follow it
- Else: Follow language-specific best practices (TypeScript/Go/Python)

Same for testing, security, infrastructure standards.
```

**Agent adapts to project structure!**

---

## ✅ For Togglr Specifically:

**Has complete standards in `docs/standards/`:**
- coding-guidelines.md ✅
- testing-standards.md ✅
- security-requirements.md ✅
- technical-design-guidelines.md ✅
- infrastructure-as-code.md ✅
- git-workflow.md ✅
- naming-conventions.md ✅
- security-codeql-integration.md ✅

**Agent will find and use all of them!**

---

**For projects without standards:**
- Agent uses generic best practices
- Suggests creating standards
- Can generate standards based on codebase analysis

