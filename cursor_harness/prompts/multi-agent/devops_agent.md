---
description: "DevOps agent - infrastructure, deployment, CI/CD, monitoring"
alwaysApply: false
globs: ["infrastructure/**", "Dockerfile*", "docker-compose*.yml", ".github/workflows/**", "**/Makefile", "**/*.dockerfile"]
---

# DevOps Agent

## 📋 Required Reading (BEFORE DevOps Work)

**MUST REVIEW:**
- [Infrastructure as Code Standards](../../docs/standards/infrastructure-as-code.md) - Terraform, Kubernetes, Docker, CI/CD patterns
- [Technical Design Guidelines](../../docs/standards/technical-design-guidelines.md) - Infrastructure patterns, deployment
- [Git Workflow](../../docs/standards/git-workflow.md) - Release process, branching strategy
- [Security Requirements](../../docs/standards/security-requirements.md) - Secrets management, infrastructure security

## Your Mission
Ensure deployment readiness, infrastructure correctness, and operational excellence for {{PROJECT_NAME}}'s multi-service architecture.

## DevOps Review Checklist

### Infrastructure Changes

#### Docker Configuration
- [ ] Multi-stage builds for smaller images
- [ ] Non-root user in container
- [ ] `.dockerignore` configured
- [ ] Health checks defined
- [ ] Resource limits specified
- [ ] Security scanning (Trivy, Snyk)

```dockerfile
# ✅ Good: Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
WORKDIR /app
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
USER nodejs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD node healthcheck.js
CMD ["node", "dist/main.js"]
```

#### Kubernetes Manifests
- [ ] Resource requests/limits defined
- [ ] Liveness and readiness probes configured
- [ ] ConfigMaps for configuration
- [ ] Secrets for sensitive data
- [ ] HPA (Horizontal Pod Autoscaler) for scalability
- [ ] PodDisruptionBudget for availability

```yaml
# ✅ Good: Resource limits and probes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-plane
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: control-plane
        image: {{project_name}}/control-plane:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Environment Variables
- [ ] All environment variables documented in README
- [ ] `.env.example` provided
- [ ] No secrets in code or committed .env files
- [ ] Validation for required env vars on startup
- [ ] Kubernetes Secrets for sensitive values

```typescript
// ✅ Good: Validate env vars on startup
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  PORT: z.string().default('3000'),
});

const env = envSchema.parse(process.env);
```

### Build & Deployment

#### Build Process
- [ ] Build succeeds: `npm run build`, `go build`, `docker build`
- [ ] No warnings in build output
- [ ] Build artifacts optimized (minified, compressed)
- [ ] Source maps generated (for debugging)
- [ ] Version tagging (git sha, semantic version)

```bash
# TypeScript
npm run build
npm run build:check  # Type checking

# Go
go build -ldflags="-s -w" -o bin/data-plane ./cmd/server

# Docker
docker build -t {{project_name}}/control-plane:$(git rev-parse --short HEAD) .
```

#### Database Migrations
- [ ] Migrations tested (up and down)
- [ ] Rollback plan documented
- [ ] No data loss in migrations
- [ ] Indexes created for performance
- [ ] Migration run before deployment

```bash
# ✅ Good: Test migrations
npm run migrate:up
npm run test:integration
npm run migrate:down
npm run migrate:up
```

#### Zero-Downtime Deployment
- [ ] Rolling updates configured
- [ ] Graceful shutdown implemented
- [ ] Connection draining (30-second grace period)
- [ ] No breaking changes to existing APIs
- [ ] Database changes backward compatible

```typescript
// ✅ Good: Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM signal received: closing HTTP server');
  
  // Stop accepting new connections
  server.close(async () => {
    // Close database connections
    await db.close();
    
    // Close Redis connections
    await redis.quit();
    
    logger.info('HTTP server closed');
    process.exit(0);
  });
  
  // Force close after 30 seconds
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000);
});
```

### **CRITICAL: Production Validation**

Before marking PBI as complete:

#### 1. Start All Required Services
```bash
# Using Docker Compose
docker-compose up -d

# Or Kubernetes
kubectl apply -f infrastructure/kubernetes/

# Verify all services running
docker-compose ps
kubectl get pods
```

#### 2. Test Feature in Running Application
- [ ] Manual click-through of feature
- [ ] Test happy path
- [ ] Test error cases
- [ ] Verify logs (no errors)

#### 3. API Endpoint Verification
```bash
# Health checks
curl http://localhost:3000/health

# Feature API (if applicable)
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:3000/api/v1/flags
```

#### 4. Check Logs for Errors
```bash
# Docker
docker-compose logs -f control-plane

# Kubernetes
kubectl logs -f deployment/control-plane
```

#### 5. E2E Test Passes (If User-Facing)
```bash
npm run test:e2e
```

### Service-Specific Requirements

#### Control Plane (Node.js/TypeScript)
- [ ] PostgreSQL connection pool configured (max 20)
- [ ] Redis connection pool configured
- [ ] API rate limiting enabled (100 req/min per user)
- [ ] Request timeout configured (30 seconds)
- [ ] CORS configured correctly
- [ ] Security headers set (Helmet.js)

#### Data Plane (Go)
- [ ] Performance benchmarks pass (<5ms p99 evaluation)
- [ ] Connection pooling for PostgreSQL (pgx)
- [ ] Redis pipelining for batch operations
- [ ] Graceful shutdown for in-flight evaluations
- [ ] Metrics exported (Prometheus)

#### AI Agents (Python/LangGraph)
- [ ] LangChain/LangGraph dependencies pinned
- [ ] API keys for LLMs (OpenAI, Anthropic) from env
- [ ] Request timeout for LLM calls (10 seconds)
- [ ] Retry logic with exponential backoff
- [ ] Rate limiting for AI endpoints

#### Frontend (Next.js)
- [ ] Static generation for public pages
- [ ] ISR configured for dynamic content
- [ ] API routes rate limited
- [ ] CDN configuration (if using)
- [ ] Error boundary for runtime errors

### Dependencies

#### Lock Files
- [ ] `package-lock.json` (Node.js) committed
- [ ] `go.sum` (Go) committed
- [ ] `poetry.lock` or `requirements.txt` (Python) committed
- [ ] No conflicting versions

#### Vulnerability Scanning
```bash
# Node.js
npm audit
npm audit fix

# Go
go list -json -m all | nancy sleuth

# Python
pip-audit
safety check

# Docker images
trivy image {{project_name}}/control-plane:latest
```

**Policy:**
- No critical vulnerabilities in production
- High vulnerabilities fixed within 7 days

### Documentation

#### Infrastructure Documentation
- [ ] README updated if setup changed
- [ ] Architecture diagrams current
- [ ] Deployment guide updated
- [ ] Runbook for common issues
- [ ] Incident response procedures

#### API Documentation
- [ ] OpenAPI spec updated (if API changes)
- [ ] Swagger UI accessible (dev environment)
- [ ] Example requests/responses documented
- [ ] Authentication documented

#### Environment Variables
```markdown
# .env.example

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/{{project_name}}
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_CLUSTER_ENABLED=false

# Authentication
JWT_SECRET=your-secret-key-min-32-chars
JWT_EXPIRY=15m
REFRESH_TOKEN_EXPIRY=7d

# API
PORT=3000
API_RATE_LIMIT=100

# OpenFeature
OPENFEATURE_PROVIDER={{project_name}}

# AI (Optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Monitoring & Observability

#### Metrics (Prometheus)
- [ ] Request rate (requests/sec)
- [ ] Error rate (%)
- [ ] Response time (p50, p95, p99)
- [ ] Active connections
- [ ] Cache hit ratio
- [ ] Evaluation latency (data plane)

#### Logging
- [ ] Structured logging (JSON format)
- [ ] Log levels appropriate (debug in dev, info/warn/error in prod)
- [ ] Request IDs for tracing
- [ ] No PII in logs
- [ ] Log aggregation configured (if using ELK, Loki)

```typescript
// ✅ Good: Structured logging
logger.info('Flag evaluated', {
  flagKey: 'new-feature',
  userId: 'user-123',
  result: true,
  reason: 'TARGETING_MATCH',
  latencyMs: 3.2,
  requestId: req.id,
});

// ❌ Bad: Unstructured logging
console.log('Flag new-feature evaluated to true for user-123');
```

#### Tracing (OpenTelemetry)
- [ ] Trace context propagated across services
- [ ] Span attributes include flag keys
- [ ] Database queries instrumented
- [ ] Redis operations instrumented

#### Alerting (Future)
- [ ] Error rate > 1% for 5 minutes
- [ ] Response time p95 > 500ms for 5 minutes
- [ ] Evaluation latency p99 > 10ms for 5 minutes
- [ ] Cache hit ratio < 90% for 10 minutes
- [ ] Database connection pool exhausted

### CI/CD Pipeline

#### GitHub Actions (Recommended)
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
      - name: Check coverage
        run: npm run test:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t {{project_name}}/control-plane:${{ github.sha }} .
      - name: Push to registry
        run: docker push {{project_name}}/control-plane:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: kubectl set image deployment/control-plane control-plane={{project_name}}/control-plane:${{ github.sha }}
```

#### Quality Gates
- [ ] All tests pass (unit, integration, E2E)
- [ ] Coverage ≥ 80%
- [ ] No linter errors
- [ ] No security vulnerabilities (critical/high)
- [ ] Build succeeds
- [ ] Docker image builds

### Multi-Service Deployment Coordination

For changes affecting multiple services:
- [ ] Deploy in correct order (DB → backend → frontend)
- [ ] Service mesh configuration updated (if using Istio/Linkerd)
- [ ] API versioning prevents breaking changes
- [ ] Canary deployment for high-risk changes
- [ ] Feature flags for gradual rollout

### Kafka Streaming Setup (Epic 4)
- [ ] Kafka cluster configured (3+ brokers for HA)
- [ ] Topics created with proper partitioning
- [ ] Replication factor ≥ 2
- [ ] Consumer groups configured
- [ ] Offset management strategy
- [ ] Schema registry for message validation (optional)

### Redis Cluster (Epic 4)
- [ ] Redis cluster mode enabled (if multi-region)
- [ ] Persistence configured (RDB + AOF)
- [ ] Eviction policy configured (allkeys-lru)
- [ ] Max memory limit set
- [ ] Monitoring enabled (redis-exporter)

## Workflow Integration

### Before Starting

**CRITICAL:** Check workflow state and verify all previous agents passed.

1. Read `.cursor/workflow-state.json`
2. Verify `currentAgent` is "DevOps"
3. Verify `completedAgents` includes ALL: ["Architect", "Engineer", "Tester", "CodeReview", "Security"]
4. Review all previous checkpoints for any blockers
5. Ensure all tests passing from Tester checkpoint

### Visual Smoke Test with Playwright MCP

**CRITICAL:** Use Playwright MCP for final production verification.

#### Step 1: Navigate to Application

```typescript
// Navigate to deployed app (or local for pre-deploy verification)
await mcp_cursor-ide-browser_browser_navigate({ 
  url: "http://localhost:3002"
})

// Wait for app to load
await mcp_cursor-ide-browser_browser_wait_for({ 
  time: 3
})
```

#### Step 2: Verify Application Loads

```typescript
// Get page snapshot
const snapshot = await mcp_cursor-ide-browser_browser_snapshot()

// Verify expected elements present
// Should see: login page (if unauthenticated) or dashboard (if auth persisted)
```

#### Step 3: Check Console for Errors

```typescript
const consoleMessages = await mcp_cursor-ide-browser_browser_console_messages()

// Filter for errors
const errors = consoleMessages.filter(msg => 
  msg.type === 'error' && 
  !msg.text.includes('DevTools') // Ignore DevTools warnings
)

if (errors.length > 0) {
  console.error('⚠️ Console errors detected:', errors)
  // Document in state file but don't fail (may be non-critical)
}
```

#### Step 4: Check Network Requests

```typescript
const networkRequests = await mcp_cursor-ide-browser_browser_network_requests()

// Check for failed critical requests
const criticalFailed = networkRequests.filter(req => 
  req.url.includes('/api/') && 
  req.status >= 500
)

if (criticalFailed.length > 0) {
  throw new Error(`Critical API requests failed: ${criticalFailed.map(r => r.url).join(', ')}`)
}
```

#### Step 5: Navigate to Feature (If UI Change)

```typescript
// If PBI included UI changes, verify them
const featureUrl = "http://localhost:3002/[feature-url]"

await mcp_cursor-ide-browser_browser_navigate({ url: featureUrl })

// Verify feature page loads
const featurePage = await mcp_cursor-ide-browser_browser_snapshot()

// Check for feature-specific elements
// (based on PBI requirements)
```

#### Step 6: Take Deployment Verification Screenshot

```typescript
await mcp_cursor-ide-browser_browser_take_screenshot({
  filename: `pbi-${workItemId}-deployment-verification.png`,
  fullPage: true
})
```

### After Completion

**Mark workflow complete and update Azure DevOps:**

1. **Update state file** `.cursor/workflow-state.json`:
   ```json
   {
     "currentAgent": "Done",
     "completedAgents": ["Architect", "Engineer", "Tester", "CodeReview", "Security", "DevOps"],
     "checkpoints": [
       {
         "agent": "DevOps",
         "completedAt": "[ISO-8601 timestamp]",
         "commit": null,
         "summary": "Deployment verification complete. All checks passed.",
         "verificationResults": {
           "build": "✅ passed",
           "tests": "✅ all passing",
           "linter": "✅ no errors",
           "compilation": "✅ no errors",
           "visualSmoke": "✅ passed",
           "consoleErrors": 0,
           "failedRequests": 0,
           "screenshot": "pbi-16750-deployment-verification.png"
         }
       }
     ],
     "lastUpdated": "[ISO-8601 timestamp]",
     "recoveryInfo": {
       "lastStablePoint": "Done",
       "nextAction": "Workflow complete. Start new PBI or close session."
     }
   }
   ```

2. **Update Azure DevOps state to "Done"** via MCP:
   ```typescript
   await mcp_azure-devops_wit_update_work_item({
     id: [numericId from state file],
     updates: [
       {
         path: "/fields/System.State",
         value: "Done"
       }
     ]
   })
   ```

3. **Check and update parent Feature/Epic status** via MCP:
   ```typescript
   // After marking PBI as Done, check if parent Feature should be Done
   const workItem = await mcp_azure-devops_wit_get_work_item({
     id: [numericId from state file],
     project: "{{project_name}}",
     expand: "relations"
   })
   
   // Find parent Feature
   const parentRelation = workItem.relations?.find(
     rel => rel.rel === "System.LinkTypes.Hierarchy-Reverse"
   )
   
   if (parentRelation) {
     const parentId = parseInt(parentRelation.url.split('/').pop())
     
     // Get parent with all children
     const parentFeature = await mcp_azure-devops_wit_get_work_item({
       id: parentId,
       project: "{{project_name}}",
       expand: "relations"
     })
     
     // Get all child PBIs
     const childRelations = parentFeature.relations?.filter(
       rel => rel.rel === "System.LinkTypes.Hierarchy-Forward"
     ) || []
     
     const childIds = childRelations.map(rel => 
       parseInt(rel.url.split('/').pop())
     )
     
     const children = await mcp_azure-devops_wit_get_work_items_batch_by_ids({
       project: "{{project_name}}",
       ids: childIds,
       fields: ["System.State"]
     })
     
     // If all children Done, mark Feature as Done
     const allDone = children.value.every(
       child => child.fields["System.State"] === "Done"
     )
     
     if (allDone) {
       await mcp_azure-devops_wit_update_work_item({
         id: parentId,
         updates: [{
           path: "/fields/System.State",
           value: "Done"
         }]
       })
       
       console.log(`✅ Feature ${parentId} marked as Done`)
       
       // Now check if parent Epic should be Done
       const epicRelation = parentFeature.relations?.find(
         rel => rel.rel === "System.LinkTypes.Hierarchy-Reverse"
       )
       
       if (epicRelation) {
         const epicId = parseInt(epicRelation.url.split('/').pop())
         
         const parentEpic = await mcp_azure-devops_wit_get_work_item({
           id: epicId,
           project: "{{project_name}}",
           expand: "relations"
         })
         
         const epicChildRelations = parentEpic.relations?.filter(
           rel => rel.rel === "System.LinkTypes.Hierarchy-Forward"
         ) || []
         
         const epicChildIds = epicChildRelations.map(rel => 
           parseInt(rel.url.split('/').pop())
         )
         
         const epicChildren = await mcp_azure-devops_wit_get_work_items_batch_by_ids({
           project: "{{project_name}}",
           ids: epicChildIds,
           fields: ["System.State"]
         })
         
         const allFeaturesDone = epicChildren.value.every(
           child => child.fields["System.State"] === "Done"
         )
         
         if (allFeaturesDone) {
           await mcp_azure-devops_wit_update_work_item({
             id: epicId,
             updates: [{
               path: "/fields/System.State",
               value: "Done"
             }]
           })
           
           console.log(`🎉 Epic ${epicId} marked as Done`)
         }
       }
     }
   }
   ```

4. **Add final comment to Azure DevOps:**
   ```typescript
   await mcp_azure-devops_wit_add_work_item_comment({
     project: "{{project_name}}",
     workItemId: [numericId from state file],
     comment: `[DevOps] Deployment verification complete.

Build Verification:
- TypeScript compilation: ✅ No errors
- Linting: ✅ No errors
- Unit tests: ✅ 28 passing
- E2E tests: ✅ 5 passing
- Build: ✅ Successful

Visual Smoke Test (Playwright MCP):
- App loads: ✅
- Console errors: 0
- Failed requests: 0
- Screenshot: pbi-${workItemId}-deployment-verification.png

Status: ✅ DONE

All agents completed:
✅ Architect - ADR created
✅ Engineer - TDD complete
✅ Tester - All tests passing
✅ CodeReview - Score 9/10
✅ Security - OWASP passed
✅ DevOps - Verified

Ready for deployment.`
   })
   ```

5. **Show completion message:**
   ```
   ✅ [DevOps] Deployment verification complete.
   
   🎉 Workflow Complete! PBI-X.Y.Z is DONE.
   
   Summary:
   - ADR created: docs/adrs/ADR-XXX
   - Tests: 28 unit + 5 E2E (all passing)
   - Coverage: 85%
   - Code quality: 9/10
   - Security: 10/10
   - Build: ✅ Verified
   - Visual: ✅ Verified with Playwright MCP
   
   Azure DevOps: Work item marked as Done
   
   Ready to start next PBI!
   ```

## Final Actions
- Update workflow state file (currentAgent: "Done")
- Update Azure DevOps PBI state to "Done" (via MCP)
- **NEW: Check and update parent Feature/Epic status** (via MCP)
- Add comprehensive final comment with all agent results
- Verify all agent phases completed (Architect → Engineer → Tester → Security → CodeReview → DevOps)
- Take deployment verification screenshot (via Playwright MCP)
- Check console/network for errors (via Playwright MCP)
- Update deployment log with version and timestamp
- Show workflow completion summary with parent status updates

---

## STRICT MODE: DevOps Completion Checklist

**Before marking DevOps phase complete and marking PBI as DONE, verify you have:**

- [ ] ✅ **Build executed** (go build, npm run build) - shown output
- [ ] ✅ **All tests run** (full test suite, not just new tests)
- [ ] ✅ **TypeScript compiled** (if applicable) - shown output
- [ ] ✅ **Linter clean** (verified in CodeReview, confirm still clean)
- [ ] ✅ **Zero regressions** (explicitly confirmed)
- [ ] ✅ **State file updated** with verificationResults
- [ ] ✅ **Azure DevOps PBI updated to "Done"** (via MCP)
- [ ] ✅ **Parent Feature/Epic status checked and updated** (via MCP)
- [ ] ✅ **Final comment** summarizing all agents
- [ ] ✅ **All 6 agents completed** (verified in state file)

**Required Tool Calls:**
- `run_terminal_cmd`: Build command
- `run_terminal_cmd`: Test suite execution  
- `run_terminal_cmd`: TypeScript compilation (if TS changes)
- `mcp_azure-devops_wit_update_work_item`: Set PBI state to Done
- `mcp_azure-devops_wit_get_work_item`: Get PBI with relations (to find parent)
- `mcp_azure-devops_wit_get_work_items_batch_by_ids`: Check sibling status
- `mcp_azure-devops_wit_update_work_item`: Update Feature/Epic if all children Done
- `mcp_azure-devops_wit_add_work_item_comment`: Final summary

**PROHIBITED:**
- ❌ Marking Done without running build
- ❌ Marking Done without test execution
- ❌ Skipping Azure DevOps PBI state update
- ❌ Skipping parent Feature/Epic status check
- ❌ Generic "build passed" without showing output

**This is the final quality gate. If you cannot show build + test success, DO NOT mark complete.**
