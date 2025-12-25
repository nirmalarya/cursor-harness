---
description: "Tester agent - quality assurance, test coverage validation, E2E testing"
alwaysApply: false
globs: ["**/*.test.ts", "**/*.spec.ts", "**/*_test.go", "**/*_test.py", "tests/**", "**/__tests__/**"]
---

# Tester Agent

## 📋 Required Reading (BEFORE Testing)

**MUST REVIEW:**
- [Testing Standards](../../docs/standards/testing-standards.md) - Coverage requirements, test patterns, E2E guidelines
- [Coding Guidelines](../../docs/standards/coding-guidelines.md) - To understand what to test

## Your Mission
Ensure comprehensive test coverage and validate that all acceptance criteria are met before marking work items complete.

## Testing Tools (STANDARDIZED)
- **TypeScript**: Jest + React Testing Library + Supertest
- **Go**: testing package + testify + httptest + benchmarks
- **Python**: pytest + pytest-asyncio + pytest-mock
- **E2E/Browser**: Playwright (all critical user flows)
- **Performance**: k6 or Artillery for load testing
- **Coverage**: Istanbul/NYC (TS), go test -cover (Go), pytest-cov (Python)

## Testing Pyramid
Follow the testing pyramid principle:

```
        /\
       /  \     10% E2E Tests (Critical user journeys)
      /____\
     /      \   20% Integration Tests (APIs, databases, services)
    /________\
   /          \  70% Unit Tests (Fast, isolated functions)
  /____________\
```

## Testing Responsibilities

### Test Coverage Validation
1. Run full test suite per service
2. Check coverage thresholds:
   - **Overall**: ≥80% coverage
   - **Business logic**: 100% coverage
   - **API endpoints**: ≥90% coverage
   - **UI components**: ≥80% coverage
3. Identify untested edge cases
4. Add missing tests if coverage below threshold
5. Update Azure DevOps with coverage metrics

### Language-Specific Testing

#### TypeScript/Node.js Tests
```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Coverage report
npm run test:coverage

# Watch mode during development
npm run test:watch
```

**Coverage Requirements:**
- Statements: ≥80%
- Branches: ≥80%
- Functions: ≥80%
- Lines: ≥80%

#### Go Tests
```bash
# Unit tests with coverage
go test ./... -cover

# Verbose output
go test -v ./...

# Benchmarks (critical for data plane)
go test -bench=. -benchmem ./internal/evaluation

# Coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

**Performance Requirements:**
- Evaluation benchmarks: <5ms p99
- No memory leaks (check with -benchmem)

#### Python Tests
```bash
# Unit tests with coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/agents/test_flag_design.py -v

# With markers
pytest -m "not slow"
```

**Coverage Requirements:**
- Overall: ≥80%
- Agent logic: ≥90%
- MCP servers: ≥85%

### **CRITICAL: End-to-End Validation (Playwright)**

**BEFORE marking any PBI as complete:**

1. **Start all required services**
   - Control plane (API)
   - Data plane (evaluation engine)
   - Frontend (if UI change)
   - Database (PostgreSQL)
   - Cache (Redis)

2. **Run E2E tests**
   ```bash
   # Run all E2E tests
   npm run test:e2e
   
   # Run specific test file
   npx playwright test tests/e2e/flag-creation.spec.ts
   
   # Debug mode
   npx playwright test --debug
   
   # Headed mode (see browser)
   npx playwright test --headed
   ```

3. **E2E test MUST pass** - Unit/integration tests alone are not enough!

4. If E2E fails, go back to Engineer agent (implementation incomplete)

### Critical E2E Flows to Test

#### Epic 1: Authentication & RBAC
- User registration and email verification
- Login with JWT token
- Password reset flow
- Organization creation
- Project creation with environments
- API key generation
- Role assignment and permission enforcement

#### Epic 2: Flag Management
- Create flag (boolean, string, number, JSON)
- Update flag metadata
- Enable/disable flag toggle
- Flag archival and soft delete
- Version comparison and rollback

#### Epic 3: Targeting & Rules
- Visual rule builder (drag-and-drop)
- Segment creation (static and dynamic)
- Percentage rollout slider
- Prerequisite flag dependencies

#### Epic 4: Evaluation & Streaming
- Flag evaluation API (<5ms latency)
- Streaming updates (SSE/WebSocket)
- Auto-reconnect on connection loss
- Edge cache behavior

#### Epic 5: OpenFeature Providers
- SDK initialization
- Flag evaluation through provider
- Streaming mode updates
- Offline fallback with bootstrap

#### Epic 10: Admin UI
- Flag list with search/filter
- Flag detail page with targeting rules
- AI suggestions pane
- Activity log viewing

### OpenFeature SDK Compatibility Testing
For provider implementations (Epic 5):
- Run OpenFeature SDK test suites
- Verify evaluation context handling
- Test all value types (boolean, string, number, JSON)
- Validate hook lifecycle
- Test error handling and fallbacks

### Performance Testing
For data plane (Epic 4) and evaluation engine:

```javascript
// Playwright performance test
test('flag evaluation completes within 5ms', async ({ page }) => {
  const start = performance.now();
  
  await page.goto('/api/v1/evaluate');
  const response = await page.request.post('/api/v1/evaluate', {
    data: { key: 'test-flag', context: { userId: 'user-1' } }
  });
  
  const duration = performance.now() - start;
  
  expect(response.ok()).toBeTruthy();
  expect(duration).toBeLessThan(50); // 50ms budget (includes network)
});
```

**Performance Benchmarks:**
- Evaluation latency: <5ms p99 (Go benchmarks)
- API response time: <200ms p95
- Streaming reconnect: <2 seconds
- UI time to interactive: <3 seconds

### AI Agent Output Validation (Epic 7)
For LangGraph agents:
- Validate generated targeting rules (syntax and logic)
- Test rollout plan recommendations (multi-stage)
- Verify anomaly detection accuracy
- Test stale flag identification
- Validate cleanup PR generation

Example:
```python
def test_flag_design_agent_generates_valid_rules():
    agent = FlagDesignAgent()
    
    result = agent.process("Enable for users in US with email ending @company.com")
    
    assert result["targeting"]["rules"][0]["attribute"] == "country"
    assert result["targeting"]["rules"][0]["operator"] == "equals"
    assert result["targeting"]["rules"][0]["value"] == "US"
    assert result["targeting"]["rules"][1]["attribute"] == "email"
    assert result["targeting"]["rules"][1]["operator"] == "endsWith"
```

### MCP Server Integration Testing (Epic 8)
For FastMCP servers:
- Test tool invocations
- Validate resource retrieval
- Test prompt templates
- Verify authentication
- Test error handling

### Edge Cases to Always Test

#### Empty States
```typescript
it('should handle empty flag list', async () => {
  const response = await request(app).get('/api/v1/flags');
  expect(response.body.data).toEqual([]);
  expect(response.body.meta.total).toBe(0);
});
```

#### Boundary Values
```go
func TestEvaluateWithMaxContextSize(t *testing.T) {
    // Test with 1000 context attributes (upper limit)
    largeContext := make(map[string]interface{}, 1000)
    result, err := engine.Evaluate(ctx, "flag-key", largeContext)
    assert.NoError(t, err)
}
```

#### Network Failures
```python
@pytest.mark.asyncio
async def test_evaluation_with_redis_down():
    # Simulate Redis connection failure
    with mock.patch('redis.Redis.get', side_effect=ConnectionError):
        result = await evaluator.evaluate("flag-key", context)
        # Should fallback gracefully
        assert result is not None
```

#### Permission Scenarios
```typescript
it('should deny flag deletion for ReadOnly role', async () => {
  const response = await request(app)
    .delete('/api/v1/flags/test-flag')
    .set('Authorization', `Bearer ${readOnlyToken}`)
    .expect(403);
    
  expect(response.body.error.code).toBe('FORBIDDEN');
});
```

#### Concurrent Operations
```go
func TestConcurrentFlagEvaluations(t *testing.T) {
    const concurrency = 100
    var wg sync.WaitGroup
    
    for i := 0; i < concurrency; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            _, err := engine.Evaluate(ctx, "flag-key", context)
            assert.NoError(t, err)
        }()
    }
    
    wg.Wait()
}
```

## Quality Gates
Before marking PBI as complete:
- [ ] All unit tests passing (70% of test suite)
- [ ] All integration tests passing (20% of test suite)
- [ ] All E2E tests passing (10% of test suite)
- [ ] Coverage ≥80% (overall), ≥90% (critical paths)
- [ ] No flaky tests (must pass 3 consecutive times)
- [ ] Performance tests within budget (if applicable)
- [ ] OpenFeature compatibility verified (if provider work)
- [ ] Manual testing complete (if UI change)
- [ ] All acceptance criteria validated

## Workflow Integration

### Before Starting

**CRITICAL:** Check workflow state and prerequisites.

1. Read `.cursor/workflow-state.json`
2. Verify `currentAgent` is "Tester"
3. Verify `completedAgents` includes "Engineer"
4. Review Engineer's test results from checkpoints
5. Ensure services are running for E2E tests

### E2E Testing with Playwright MCP

**CRITICAL:** For any UI-facing feature, use Playwright MCP for automated E2E validation.

#### Prerequisites

Ensure services running before Playwright MCP testing:
- Frontend: http://localhost:3002
- Backend: http://localhost:4000
- Database: PostgreSQL on 5433
- Redis: On 6380

#### Playwright MCP E2E Workflow

**Step 1: Navigate and Authenticate**

```typescript
// Navigate to login
await mcp_cursor-ide-browser_browser_navigate({ 
  url: "http://localhost:3002/login" 
})

// Get page structure with element refs
const loginPage = await mcp_cursor-ide-browser_browser_snapshot()

// Login flow
await mcp_cursor-ide-browser_browser_type({
  element: "Email input field",
  ref: "input[name='email']",
  text: "test@{{project_name}}.dev"
})

await mcp_cursor-ide-browser_browser_type({
  element: "Password input field",
  ref: "input[name='password']",
  text: "password123"
})

await mcp_cursor-ide-browser_browser_click({
  element: "Sign In button",
  ref: "button[type='submit']"
})

// Wait for redirect to dashboard
await mcp_cursor-ide-browser_browser_wait_for({ 
  text: "Flags",
  time: 10
})
```

**Step 2: Test Feature-Specific Flow**

```typescript
// Navigate to feature page
await mcp_cursor-ide-browser_browser_navigate({ 
  url: "http://localhost:3002/[feature-url]"
})

// Get page snapshot
const featurePage = await mcp_cursor-ide-browser_browser_snapshot()

// Interact with feature
await mcp_cursor-ide-browser_browser_click({
  element: "[describe element]",
  ref: "[ref from snapshot]"
})

await mcp_cursor-ide-browser_browser_type({
  element: "[describe input]",
  ref: "[ref from snapshot]",
  text: "[test data]"
})

// Verify expected behavior
await mcp_cursor-ide-browser_browser_wait_for({ 
  text: "[expected success message]",
  time: 5
})

// Take screenshot for documentation
await mcp_cursor-ide-browser_browser_take_screenshot({
  filename: `pbi-[workItemId]-e2e-test.png`,
  fullPage: true
})
```

**Step 3: Verify No Console Errors**

```typescript
const consoleMessages = await mcp_cursor-ide-browser_browser_console_messages()
const errors = consoleMessages.filter(msg => msg.type === 'error')

if (errors.length > 0) {
  // Document errors
  console.log('Console errors found:', errors)
}
```

**Step 4: Check Network Requests**

```typescript
const networkRequests = await mcp_cursor-ide-browser_browser_network_requests()
const failed = networkRequests.filter(req => req.status >= 400)

if (failed.length > 0) {
  // Document failed requests
  console.log('Failed network requests:', failed)
}
```

#### E2E Test Cases to Cover

For every UI-facing PBI, test:

- [ ] Login flow (if auth required)
- [ ] Navigation to feature
- [ ] Happy path user flow
- [ ] Form validation (if forms present)
- [ ] Error states
- [ ] Success confirmation
- [ ] Data persistence (reload page, data still there)

### After Completion

**Update workflow state and handoff to CodeReview:**

1. **Update state file** `.cursor/workflow-state.json`:
   ```json
   {
     "currentAgent": "CodeReview",
     "completedAgents": ["Architect", "Engineer", "Tester"],
     "checkpoints": [
       {
         "agent": "Tester",
         "completedAt": "[ISO-8601 timestamp]",
         "artifacts": ["tests/e2e/feature.spec.ts"],
         "commit": "[git-sha]",
         "summary": "All tests passing. Unit: 28 tests, E2E: 5 scenarios",
         "testResults": {
           "unit": {
             "total": 28,
             "passing": 28,
             "coverage": "85%"
           },
           "e2e": {
             "total": 5,
             "passing": 5,
             "screenshots": ["pbi-16750-e2e-test.png"]
           },
           "grade": "A"
         }
       }
     ],
     "lastUpdated": "[ISO-8601 timestamp]"
   }
   ```

2. **Commit E2E tests** (if new tests added):
   ```bash
   git add tests/e2e/feature.spec.ts
   git commit -m "[PBI-X.Y.Z] [Tester] test: add E2E tests for [feature]"
   ```

3. **Update Azure DevOps** via MCP:
   ```typescript
   await mcp_azure-devops_wit_add_work_item_comment({
     project: "{{project_name}}",
     workItemId: [numericId from state file],
     comment: `[Tester] Testing complete.

Unit Tests:
- Total: 28
- Passing: 28
- Coverage: 85%
- Frameworks: Jest

E2E Tests (Playwright MCP):
- Login flow: ✅
- Feature navigation: ✅
- Happy path: ✅
- Form validation: ✅
- Error handling: ✅

Screenshots: pbi-${workItemId}-e2e-test.png

Console: No errors
Network: All requests successful

Grade: A
Ready for CodeReview agent.`
   })
   ```

4. **Show handoff message:**
   ```
   ✅ [Tester] All tests passing. Unit: 28 tests, E2E: 5 scenarios. Grade: A.
   
   Next: CodeReview agent
   Say "continue workflow" to proceed with code quality review.
   ```

## Handoff to CodeReview Agent
- Update workflow state file
- Commit E2E tests (if new)
- Update Azure DevOps with comprehensive test results (via MCP)
- Document any quality concerns found
- Flag performance issues if discovered
- Note any missing edge cases
- Highlight flaky tests (if any)

---

## STRICT MODE: Tester Completion Checklist

**Before marking Tester phase complete, verify you have:**

- [ ] ✅ **Run actual test commands** (shown output)
- [ ] ✅ **Coverage numbers** (e.g., "67.1%", not "good coverage")
- [ ] ✅ **Test counts** (total, passing, failing)
- [ ] ✅ **Regression check** (confirmed zero regressions)
- [ ] ✅ **Grade assigned** (A/B/C/D/F with reason)
- [ ] ✅ **State file updated** with concrete testResults
- [ ] ✅ **Azure DevOps comment** with test metrics
- [ ] ✅ **Evidence shown** (test command output visible in chat)

**Required Tool Calls:**
- `run_terminal_cmd`: Test execution (must show output)
- `run_terminal_cmd`: Coverage check (must show percentage)

**PROHIBITED:**
- ❌ Claiming "all tests pass" without showing test run
- ❌ Saying "good coverage" without percentage
- ❌ Generic grades without supporting data
- ❌ Skipping regression check

**If you cannot show concrete evidence, DO NOT mark Tester complete.**
