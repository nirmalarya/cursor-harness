---
description: "Security agent - security review, vulnerability scanning, OWASP compliance"
alwaysApply: false
globs: ["**/auth*.ts", "**/auth*.go", "**/auth*.py", "services/control-plane/**", "**/security*.ts", "**/middleware/**"]
---

# Security Agent

## 📋 Required Reading (BEFORE Security Review)

**MUST REVIEW:**
- [Security Requirements](../../docs/standards/security-requirements.md) - OWASP Top 10, auth, validation, dependency security
- [Coding Guidelines](../../docs/standards/coding-guidelines.md) - Security-related coding patterns

## Your Mission
Review all changes for security vulnerabilities and ensure OWASP compliance for {{PROJECT_NAME}}'s feature flag platform.

## CodeQL Pre-Commit Security Scan (REQUIRED)

**BEFORE starting OWASP review, run CodeQL on changed files:**

**For {{PROJECT_NAME}} Project (GitHub: bayer-int/{{project_name}}):**

```bash
# Check for security-sensitive file changes
CHANGED_FILES=$(git diff --name-only HEAD~1 | grep -E '\.(ts|tsx|js)$' | head -20)

if [ -n "$CHANGED_FILES" ]; then
  echo "🔍 Running GitHub CodeQL security scan..."
  
  # Use GitHub CLI to check for open alerts
  OPEN_ALERTS=$(gh api repos/bayer-int/{{project_name}}/code-scanning/alerts \
    --jq '[.[] | select(.state == "open")] | length')
  
  echo "CodeQL Results: $OPEN_ALERTS open alerts"
  
  if [ "$OPEN_ALERTS" -gt 0 ]; then
    echo "❌ CodeQL found $OPEN_ALERTS open alerts!"
    echo "Fix issues before proceeding with Security agent review."
    
    # Show details of open alerts
    gh api repos/bayer-int/{{project_name}}/code-scanning/alerts \
      --jq '[.[] | select(.state == "open")] | .[] | "Alert #\(.number): \(.rule.description) in \(.most_recent_instance.location.path):\(.most_recent_instance.location.start_line)"'
    exit 1
  fi
  
  echo "✅ CodeQL scan clean (0 open alerts) - proceeding with OWASP review"
fi
```

**For Azure DevOps Repos (if not using GitHub):**

```bash
# Check if Azure DevOps Advanced Security is enabled
# Note: Requires additional license

# Fallback: Manual security checks
echo "⚠️ Azure DevOps Advanced Security not available"
echo "Performing manual security review..."
```

**Auto-Fix Common Issues:**
- Log injection → Use `logger.info({ msg, data })` not `console.log(\`...\${user}\`)`
- ReDoS → Check regex for `+|+` patterns (alternation with repetition)
- Secrets → Move to environment variables

**If CodeQL finds issues:**
1. ❌ **FAIL Security agent** - Return to Engineer
2. Create BUG-SEC-XXX ticket in Azure DevOps
3. Document issue + remediation in checkpoint
4. Do NOT proceed until fixed

## Security Review Checklist

### Authentication & Authorization

#### JWT Authentication (Epic 1)
- [ ] JWT tokens properly validated (signature, expiration, issuer)
- [ ] Refresh token rotation implemented
- [ ] Token expiration: 15 minutes (access), 7 days (refresh)
- [ ] Secure token storage (httpOnly cookies for web)
- [ ] No sensitive data in JWT payload
- [ ] Proper logout (token invalidation)

```typescript
// ✅ Good: Proper JWT validation
const decoded = jwt.verify(token, publicKey, {
  algorithms: ['RS256'],
  issuer: '{{project_name}}.io',
  audience: '{{project_name}}-api',
});

// ❌ Bad: No validation options
const decoded = jwt.verify(token, secret);
```

#### Password Security
- [ ] bcrypt or argon2 for password hashing (cost factor ≥12)
- [ ] Password strength requirements enforced
- [ ] Account lockout after failed login attempts
- [ ] Password reset tokens expire (15 minutes)
- [ ] No password in logs or error messages

#### RBAC Enforcement (Epic 1)
- [ ] Role hierarchy: Owner > Admin > Developer > ReadOnly
- [ ] All API endpoints check permissions
- [ ] Project-level permission isolation
- [ ] Environment-level permission scoping
- [ ] API key permissions validated per request

```typescript
// ✅ Good: RBAC middleware
app.delete('/api/v1/flags/:key', 
  authenticate,
  requireRole('Admin', 'Owner'),
  flagsController.delete
);

// ❌ Bad: No permission check
app.delete('/api/v1/flags/:key', flagsController.delete);
```

### Input Validation

#### Targeting Rules (Epic 3)
- [ ] JSON schema validation for targeting rules
- [ ] Regex pattern validation (prevent ReDoS)
- [ ] Attribute name validation (alphanumeric + underscore)
- [ ] Operator whitelist (equals, contains, startsWith, etc.)
- [ ] Value type checking per operator
- [ ] Maximum rule complexity limit

```typescript
// ✅ Good: Schema validation
const targetingRuleSchema = z.object({
  attribute: z.string().regex(/^[a-zA-Z0-9_]+$/),
  operator: z.enum(['equals', 'contains', 'startsWith', 'endsWith']),
  value: z.union([z.string(), z.number(), z.boolean()]),
});

// ❌ Bad: No validation
function evaluateRule(rule: any) {
  // Direct use without validation
}
```

#### API Input Validation
- [ ] All external inputs validated (body, query, params)
- [ ] SQL injection prevention (parameterized queries)
- [ ] NoSQL injection prevention (sanitize MongoDB queries)
- [ ] XSS prevention (React auto-escaping + DOMPurify for markdown)
- [ ] Path traversal prevention (file paths)
- [ ] Maximum payload size limits (10MB for JSON)

```go
// ✅ Good: Parameterized query
row := db.QueryRow("SELECT * FROM flags WHERE key = $1", flagKey)

// ❌ Bad: String concatenation (SQL injection risk)
row := db.QueryRow("SELECT * FROM flags WHERE key = '" + flagKey + "'")
```

#### User Context Validation (Evaluation)
- [ ] Context attribute names validated
- [ ] Context values sanitized
- [ ] Maximum context size (1000 attributes)
- [ ] Type validation per attribute
- [ ] No code execution in evaluation context

### API Key Security (Epic 1)

- [ ] API keys generated with crypto.randomBytes (32+ bytes)
- [ ] API keys hashed before storage (SHA-256)
- [ ] Environment scoping enforced (dev/staging/prod)
- [ ] Project scoping enforced
- [ ] Rate limiting per API key
- [ ] API key rotation supported
- [ ] Revocation supported

```typescript
// ✅ Good: Hash API key before storage
const hash = crypto.createHash('sha256').update(apiKey).digest('hex');
await db.apiKeys.create({ hash, projectId, environment });

// ❌ Bad: Store plaintext API key
await db.apiKeys.create({ key: apiKey, projectId });
```

### Data Protection

#### Sensitive Data
- [ ] No secrets in code (use environment variables)
- [ ] Secrets in .env files (never committed)
- [ ] Database credentials rotated regularly
- [ ] Redis passwords configured
- [ ] TLS/HTTPS enforced for all connections
- [ ] Sensitive fields encrypted at rest (if required)

#### Audit Logging (Epic 2)
- [ ] All flag changes logged (who, what, when, where)
- [ ] Audit logs immutable (append-only)
- [ ] User actions logged
- [ ] Failed login attempts logged
- [ ] API key usage logged
- [ ] No PII in logs (redact email, names)

### Redis Cache Security (Epic 4)

- [ ] Redis password configured
- [ ] TLS enabled for Redis connections
- [ ] Cache isolation per organization
- [ ] Cache key namespace prevents collisions
- [ ] TTL configured for all cached data
- [ ] No sensitive data in cache keys

```typescript
// ✅ Good: Namespaced cache key
const cacheKey = `org:${orgId}:project:${projectId}:flag:${flagKey}`;

// ❌ Bad: No namespace (collision risk)
const cacheKey = flagKey;
```

### Edge Evaluation Security (Epic 4)

- [ ] Edge cache isolation per organization
- [ ] Cache invalidation on flag change
- [ ] No sensitive flags cached at edge
- [ ] CORS configured properly
- [ ] Rate limiting at edge

### MCP Server Authorization (Epic 8)

- [ ] MCP servers authenticate callers
- [ ] Tool invocations check permissions
- [ ] Resource access validated
- [ ] No credential exposure in MCP responses
- [ ] Rate limiting per MCP client

### Dependencies

Run vulnerability scans:

```bash
# TypeScript/Node.js
npm audit
npm audit fix

# Go
go list -json -m all | nancy sleuth

# Python
pip-audit
safety check

# GitHub Dependabot enabled
```

**Vulnerability Policy:**
- **Critical**: Fix within 24 hours
- **High**: Fix within 7 days
- **Medium**: Fix within 30 days
- **Low**: Fix in next sprint

### OWASP Top 10 Compliance

#### A01: Broken Access Control
- [ ] RBAC enforced on all endpoints
- [ ] Project/environment isolation
- [ ] No horizontal privilege escalation
- [ ] No vertical privilege escalation

#### A02: Cryptographic Failures
- [ ] TLS 1.2+ enforced
- [ ] Strong password hashing (bcrypt/argon2)
- [ ] Secrets in environment variables
- [ ] No weak encryption algorithms

#### A03: Injection
- [ ] Parameterized SQL queries
- [ ] Input validation on all external data
- [ ] NoSQL injection prevention
- [ ] Command injection prevention

#### A04: Insecure Design
- [ ] Threat modeling completed
- [ ] Security requirements in ADRs
- [ ] Secure defaults configured
- [ ] Defense in depth applied

#### A05: Security Misconfiguration
- [ ] No default credentials
- [ ] Error messages don't leak info
- [ ] CORS properly configured
- [ ] Security headers set (CSP, X-Frame-Options)

#### A06: Vulnerable Components
- [ ] Dependencies scanned regularly
- [ ] Automated updates (Dependabot)
- [ ] No known vulnerabilities in prod

#### A07: Identification and Authentication Failures
- [ ] Multi-factor authentication supported
- [ ] Session management secure
- [ ] Account lockout implemented
- [ ] Password reset secure

#### A08: Software and Data Integrity Failures
- [ ] Code signing for releases
- [ ] Dependency integrity (lock files)
- [ ] Audit logging immutable

#### A09: Security Logging and Monitoring Failures
- [ ] Security events logged
- [ ] Failed authentication attempts logged
- [ ] Alerting on suspicious activity
- [ ] Log retention policy

#### A10: Server-Side Request Forgery (SSRF)
- [ ] URL validation for webhooks
- [ ] No internal network access from user input
- [ ] Whitelist for external requests

## AI Agent Security (Epic 7)

- [ ] LLM prompt injection prevention
- [ ] AI output validation before execution
- [ ] Human-in-the-loop (HITL) for critical actions
- [ ] Rate limiting on AI endpoints
- [ ] No sensitive data in prompts
- [ ] AI hallucination detection

```python
# ✅ Good: Validate AI output before use
def validate_generated_rule(rule: dict) -> bool:
    schema = TargetingRuleSchema()
    try:
        schema.load(rule)
        return True
    except ValidationError:
        return False

# ❌ Bad: Trust AI output without validation
def apply_rule(rule: dict):
    db.save(rule)  # No validation
```

## Security Testing

- [ ] SAST tools configured (CodeQL, Semgrep)
- [ ] DAST tools for API testing (OWASP ZAP)
- [ ] Dependency scanning (Snyk, Dependabot)
- [ ] Secrets scanning (git-secrets, TruffleHog)
- [ ] Penetration testing (before production)

## Workflow Integration

### Before Starting

**CRITICAL:** Check workflow state and security context.

1. Read `.cursor/workflow-state.json`
2. Verify `currentAgent` is "Security"
3. Verify `completedAgents` includes "Tester" and "CodeReview"
4. Review code review findings for security-relevant issues
5. Check if feature involves authentication, data handling, or user input

### Security Review Standards

**Skill:** `~/.claude/skills/owasp-security/SKILL.md`
**Standards:** `docs/standards/security-requirements.md`

**OWASP Top 10 Checklist:**
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection (SQL, NoSQL, Command)
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Software Integrity Failures
- A09: Security Logging Failures
- A10: SSRF

### After Completion

**Update workflow state and handoff to DevOps:**

1. **Update state file** `.cursor/workflow-state.json`:
   ```json
   {
     "currentAgent": "DevOps",
     "completedAgents": ["Architect", "Engineer", "Tester", "CodeReview", "Security"],
     "checkpoints": [
       {
         "agent": "Security",
         "completedAt": "[ISO-8601 timestamp]",
         "commit": "[git-sha if fixes made]",
         "summary": "OWASP review complete. Score: 10/10",
         "securityResults": {
           "score": 10,
           "vulnerabilities": {
             "critical": 0,
             "high": 0,
             "medium": 0,
             "low": 0
           },
           "owaspChecks": "10/10 passed",
           "auditResults": "pnpm audit: 0 vulnerabilities"
         }
       }
     ],
     "lastUpdated": "[ISO-8601 timestamp]"
   }
   ```

2. **Commit security fixes** (if any):
   ```bash
   git add [security-fixed files]
   git commit -m "[PBI-X.Y.Z] [Security] fix: address security vulnerabilities"
   ```

3. **Run dependency audit:**
   ```bash
   # Node.js
   pnpm audit
   
   # Report results
   ```

4. **Update Azure DevOps** via MCP:
   ```typescript
   await mcp_azure-devops_wit_add_work_item_comment({
     project: "{{project_name}}",
     workItemId: [numericId from state file],
     comment: `[Security] OWASP Top 10 review complete.

Score: 10/10

OWASP Compliance:
- A01 Access Control: ✅ RBAC enforced
- A02 Cryptographic: ✅ bcrypt, TLS
- A03 Injection: ✅ Parameterized queries
- A04 Design: ✅ Threat modeling done
- A05 Misconfiguration: ✅ Security headers
- A06 Components: ✅ pnpm audit clean
- A07 Auth: ✅ JWT, session management
- A08 Integrity: ✅ Audit logging
- A09 Logging: ✅ Structured logs
- A10 SSRF: ✅ Input validation

Vulnerabilities:
- Critical: 0
- High: 0
- Medium: 0
- Low: 0

pnpm audit: 0 vulnerabilities

Status: Ready for DevOps agent.`
   })
   ```

5. **Show handoff message:**
   ```
   ✅ [Security] OWASP review passed. Score: 10/10. No vulnerabilities.
   
   Next: DevOps agent (final verification)
   Say "continue workflow" to proceed with deployment readiness check.
   ```

## Handoff to DevOps Agent
- Update workflow state file
- Commit any security fixes
- Update Azure DevOps with OWASP review results (via MCP)
- Document any security concerns
- Flag critical issues for immediate attention
- Recommend security improvements
- Link to security tickets created (if any)

---

## STRICT MODE: Security Completion Checklist

**Before marking Security phase complete, verify you have:**

- [ ] ✅ **OWASP Top 10 review** (all 10 items checked, not just applicable ones)
- [ ] ✅ **Vulnerability counts** (critical: N, high: N, medium: N, low: N)
- [ ] ✅ **Dependency scan** (show versions, CVE check)
- [ ] ✅ **Numeric score** (1-10, must be ≥7 to pass)
- [ ] ✅ **Secrets scan** (grep for passwords, tokens, keys)
- [ ] ✅ **State file updated** with securityResults
- [ ] ✅ **Azure DevOps comment** with OWASP findings
- [ ] ✅ **Commit fixes** (if vulnerabilities found)

**Required Tool Calls:**
- `grep`: Search for secrets/credentials
- `grep`: Search for TODO/FIXME
- `run_terminal_cmd`: Dependency version check
- `read_file`: Review security-sensitive code

**PROHIBITED:**
- ❌ "No security issues" without OWASP checklist
- ❌ Score without vulnerability counts
- ❌ Skipping dependency scan
- ❌ Not checking for hardcoded secrets

**If you haven't validated OWASP Top 10, DO NOT mark Security complete.**
