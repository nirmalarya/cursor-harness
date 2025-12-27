# cursor-harness Version Comparison

## Summary

| Version | Lines | Reliability | Speed | Features | Status |
|---------|-------|-------------|-------|----------|--------|
| **v2.3.0** (autonomous-harness) | 2.5K | ✅ Proven (658 features) | Fast | Greenfield only | Stable |
| **v2.5.0** (cursor-harness) | 10K+ | ❌ Loops/stalls | Very slow (2-4h/PBI) | All modes, multi-agent | Complex |
| **v3.0.0** (this) | 1.1K | ✅ Simple design | TBD | All modes, simple | Alpha |

## v2.3.0 (autonomous-harness) - Stable

**Use for:** Production greenfield projects

```bash
cd /Users/nirmalarya/Workspace/autonomous-harness
git checkout v2.3.0
python agent.py greenfield ./my-app --spec spec.txt
```

**Strengths:**
- ✅ Proven reliable (658 AutoGraph features)
- ✅ Simple architecture
- ✅ Fast execution
- ✅ Works with Claude SDK

**Limitations:**
- ❌ No E2E testing (missed CSS errors)
- ❌ No secrets scanning (exposed keys)
- ❌ Greenfield only

## v2.5.0 (cursor-harness) - Experimental

**Use for:** Azure DevOps backlog (if patient)

```bash
cd /Users/nirmalarya/Workspace/cursor-harness
git checkout v2.5.0
cursor-harness backlog ./project --org MyOrg --project MyProject
```

**Strengths:**
- ✅ Multi-agent workflow
- ✅ All modes (greenfield, enhancement, backlog)
- ✅ Self-healing infrastructure
- ✅ Azure DevOps integration

**Limitations:**
- ❌ Over-engineered (10K+ lines)
- ❌ Very slow (2-4 hours per PBI)
- ❌ Gets stuck in loops
- ❌ Hard to debug

## v3.0.0 (cursor-harness-v3) - Alpha

**Use for:** Testing new approach

```bash
cd /Users/nirmalarya/Workspace/cursor-harness-v3
python3 cli.py greenfield ./my-app --spec spec.txt
```

**Strengths:**
- ✅ Simple core (1.1K lines)
- ✅ All modes
- ✅ Secrets scanner
- ✅ Test runner
- ✅ Loop detection (max 3 retries)
- ✅ Easy to understand/debug

**Current State:**
- ⚠️  Cursor CLI integration pending
- ⚠️  Manual mode available (shows prompts, you implement)
- ⚠️  Needs real-world testing

## Recommendation Matrix

| Use Case | Recommended Version |
|----------|-------------------|
| **New greenfield project** | v2.3.0 (proven) |
| **Brownfield enhancement** | v2.5.0 (slow but works) |
| **Azure DevOps backlog** | v2.5.0 (if patient) |
| **Want simple/debuggable** | v3.0.0 (alpha, testing) |
| **Production use** | v2.3.0 + add E2E/secrets scanning |

## Migration Path

### Short-term (This Week)
1. Use v2.3.0 for greenfield
2. Add E2E testing to v2.3.0 (Puppeteer)
3. Add secrets scanner to v2.3.0
4. = Production-ready v2.4.0

### Mid-term (Next Week)
1. Test v3.0.0 on small projects
2. Add cursor CLI integration to v3.0.0
3. Validate on Togglr/AutoGraph
4. = v3.0.0 stable

### Long-term (Next Month)
1. Deprecate v2.5.0 (too complex)
2. Merge v2.3.0 improvements into v3.0.0
3. Make v3.0.0 the primary version
4. = One simple, reliable harness

## Key Insight

**Anthropic's demo works because it's simple!**

- v2.3.0: Simple, works (but missing features)
- v2.5.0: Complex, unreliable (over-engineered)
- v3.0.0: Simple + features (right approach)

**Always prefer simple + working over complex + broken!**

