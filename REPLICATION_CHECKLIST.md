# Replication Checklist - autonomous-harness v2.2.0-dev → cursor-autonomous-harness

**Goal:** Bring cursor-harness to feature parity with autonomous-harness v2.2.0-dev

---

## 📋 Files to Copy/Update:

### Prompts (12 files)
- [ ] `prompts/coding_prompt.md` (12 quality gates integrated)
- [ ] `prompts/enhancement_coding_prompt.md` (with stop condition)
- [ ] `prompts/enhancement_initializer_prompt.md`
- [ ] `prompts/bugfix_mode_prompt.md` (with stop condition)
- [ ] `prompts/quality_gates.md` (all 12 gates documented)
- [ ] `prompts/project_structure.md` (spec/ folder structure)
- [ ] `prompts/test_execution_gate.md` (Gate #10)
- [ ] `prompts/infrastructure_validation_gate.md` (Gate #11)
- [ ] `prompts/smoke_test_gate.md` (Gate #12)
- [ ] `prompts/generic_e2e_requirements.md` (project-agnostic!)
- [ ] `prompts/generic_regression_requirements.md` (framework-agnostic!)
- [ ] `prompts/test_quality_standards.md` (quality criteria)

### Specs (Example specifications)
- [ ] `specs/simple_todo_spec.txt`
- [ ] `specs/sherpa_enhancement_spec.txt`
- [ ] `specs/autograph_puppeteer_migration.txt`
- [ ] Create `specs/` folder

### Core Files
- [ ] `regression_tester.py` (updated for spec/ folder)
- [ ] `output_formatter.py` (compact formatter)
- [ ] `security.py` (enhanced allowlist)
- [ ] `agent.py` (stop condition, modes, formatter integration)
- [ ] `prompts.py` (mode-aware, spec/ folder)
- [ ] `progress.py` (spec/ folder support)
- [ ] `autonomous_agent.py` (--mode, --spec arguments)

### Documentation
- [ ] `CHANGELOG.md` (v2.0, v2.1, v2.2 entries)
- [ ] `VERSION` (2.2.0-dev)
- [ ] Update `README.md` with new features

---

## 🔄 Differences to Account For:

**autonomous-harness:** Uses Claude Agent SDK  
**cursor-harness:** Uses Cursor CLI

**Changes needed:**
- Keep prompts SAME (they're tool-agnostic!)
- Update client code for Cursor API
- Same quality gates, same approach
- Different execution mechanism

---

## 📊 Estimated Time:

- Copying prompts: 15 min
- Updating core files: 30 min
- Testing: 15 min
- Documentation: 15 min

**Total: ~1.5 hours**

---

**Ready to start replication?** 🚀

