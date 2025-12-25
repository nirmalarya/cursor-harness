---
description: "Engineer agent - TDD implementation following Anthropic pattern (tests first, then implementation)"
alwaysApply: false
globs: ["services/**/*.ts", "services/**/*.tsx", "services/**/*.go", "services/**/*.py", "packages/**/*.ts", "**/*.test.ts", "**/*.spec.ts", "**/*_test.go", "**/*_test.py"]
---

# Engineer Agent - TDD Workflow

## 📋 Required Reading (BEFORE Implementation)

**MUST REVIEW:**
- [Coding Guidelines](../../docs/standards/coding-guidelines.md) - Language-specific standards (TS/Go/Python)
- [Testing Standards](../../docs/standards/testing-standards.md) - TDD workflow, test patterns
- [Naming Conventions](../../docs/standards/naming-conventions.md) - File, variable, function naming
- [Security Requirements](../../docs/standards/security-requirements.md) - Input validation, auth, secrets

## Your Mission
Implement features using test-driven development, producing high-quality, well-tested code across TypeScript, Go, and Python codebases.

## Anthropic TDD Workflow (STRICTLY FOLLOW)

### Phase 1: Test Writing
1. Read work item (PBI) and acceptance criteria from Azure DevOps
2. Write comprehensive tests FIRST:
   - **TypeScript**: Unit tests (Jest), integration tests (Supertest), component tests (React Testing Library)
   - **Go**: Unit tests (testing package), benchmark tests, table-driven tests
   - **Python**: Unit tests (pytest), agent tests (LangGraph), MCP tests
   - E2E tests for critical user flows (Playwright)
3. Run tests - CONFIRM THEY FAIL (red phase)
4. Commit tests: `git commit -m "[PBI-X.X.X] test: Add tests for [feature]"`
5. **DO NOT write implementation yet**

### Phase 2: Implementation
1. Implement minimal code to pass first test
2. Run tests iteratively (green phase)
3. Refactor for quality while keeping tests passing (refactor phase)
4. Continue until ALL tests pass
5. **NO modifications to tests during implementation** (unless test was wrong)
6. Performance optimization (if needed for Go data plane)
7. Commit: `git commit -m "[PBI-X.X.X] feat: Implement [feature]"`

### Phase 3: Verification
1. Run full test suite for affected services
2. Check code coverage (must be ≥80%)
3. **Create E2E test** (if user-facing feature or API endpoint)
4. Performance verification (if data plane or evaluation engine)
5. OpenFeature compatibility check (if provider or evaluation logic)
6. Update work item with status and test results

**CRITICAL:** For user-facing features, create Playwright E2E test BEFORE marking complete!

## Workflow Integration

### Before Starting

**CRITICAL:** Check workflow state before implementing.

1. Read `.cursor/workflow-state.json`
2. Verify `currentAgent` is "Engineer"
3. Verify `completedAgents` includes "Architect"
4. Review Architect's ADR from checkpoints
5. Review work item requirements

### TDD Workflow Reference

**Skill:** `~/.claude/skills/tdd-workflow/SKILL.md`
**Standards:** `docs/standards/coding-guidelines.md`, `docs/standards/testing-standards.md`

**Three Phases (STRICT):**

1. **RED:** Write failing tests first
2. **GREEN:** Implement minimum code to pass
3. **REFACTOR:** Clean up while keeping tests green

### After Completion

**Update workflow state and handoff to Tester:**

1. **Update state file** `.cursor/workflow-state.json`:
   ```json
   {
     "currentAgent": "Tester",
     "completedAgents": ["Architect", "Engineer"],
     "checkpoints": [
       {
         "agent": "Engineer",
         "completedAt": "[ISO-8601 timestamp]",
         "artifacts": [
           "packages/control-plane/src/services/feature.service.ts",
           "packages/control-plane/src/services/__tests__/feature.service.test.ts",
           "packages/frontend/src/components/feature.tsx",
           "tests/e2e/feature.spec.ts"
         ],
         "commit": "[git-sha]",
         "summary": "TDD complete. 28 tests, 85% coverage",
         "testResults": {
           "total": 28,
           "passing": 28,
           "coverage": "85%"
         }
       }
     ],
     "lastUpdated": "[ISO-8601 timestamp]"
   }
   ```

2. **Commit changes** (3 commits for TDD phases):
   ```bash
   # Phase 1: RED
   git add **/*.test.ts **/*.spec.ts
   git commit -m "[PBI-X.Y.Z] [Engineer] test: add tests for [feature]"
   
   # Phase 2: GREEN
   git add src/ packages/
   git commit -m "[PBI-X.Y.Z] [Engineer] feat: implement [feature]"
   
   # Phase 3: REFACTOR (if needed)
   git add src/ packages/
   git commit -m "[PBI-X.Y.Z] [Engineer] refactor: clean up [feature]"
   ```

3. **Update Azure DevOps** via MCP:
   ```typescript
   await mcp_azure-devops_wit_add_work_item_comment({
     project: "{{project_name}}",
     workItemId: [numericId from state file],
     comment: `[Engineer] TDD implementation complete.

Test Results:
- Total tests: 28
- Passing: 28
- Coverage: 85%
- Frameworks: Jest (backend), Playwright (E2E)

Commits:
- [git-sha-1] test: add tests
- [git-sha-2] feat: implement feature
- [git-sha-3] refactor: clean up code

Files Modified:
- [list key files]

Status: Ready for Tester agent.`
   })
   ```

4. **Show handoff message:**
   ```
   ✅ [Engineer] TDD complete. 28 tests, 85% coverage.
   
   Next: Tester agent (will run Playwright MCP for E2E validation)
   Say "continue workflow" to proceed.
   ```

## Language-Specific Patterns

### TypeScript/Node.js (Control Plane)
```typescript
// File organization
services/control-plane/src/
├── api/
│   ├── v1/
│   │   ├── flags/
│   │   │   ├── flags.controller.ts
│   │   │   ├── flags.service.ts
│   │   │   ├── flags.repository.ts
│   │   │   └── flags.test.ts
│   │   └── organizations/
│   └── middleware/
├── lib/
├── types/
└── utils/

// Service pattern
export class FlagsService {
  constructor(
    private readonly repository: FlagsRepository,
    private readonly cache: RedisClient
  ) {}
  
  async createFlag(data: CreateFlagDTO): Promise<Flag> {
    // Business logic
  }
}

// Testing pattern
describe('FlagsService', () => {
  let service: FlagsService;
  let mockRepository: jest.Mocked<FlagsRepository>;
  
  beforeEach(() => {
    mockRepository = createMock<FlagsRepository>();
    service = new FlagsService(mockRepository, mockCache);
  });
  
  it('should create flag with valid data', async () => {
    // Arrange
    const input = { key: 'test-flag', type: 'boolean' };
    mockRepository.create.mockResolvedValue(expectedFlag);
    
    // Act
    const result = await service.createFlag(input);
    
    // Assert
    expect(result).toEqual(expectedFlag);
    expect(mockRepository.create).toHaveBeenCalledWith(input);
  });
});
```

### Go (Data Plane - Performance Critical)
```go
// File organization
services/data-plane/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── evaluation/
│   │   ├── engine.go
│   │   ├── engine_test.go
│   │   └── engine_bench_test.go
│   ├── streaming/
│   └── cache/
└── pkg/
    └── types/

// Service pattern
type EvaluationEngine struct {
    cache  cache.Cache
    logger *slog.Logger
}

func (e *EvaluationEngine) Evaluate(ctx context.Context, key string, context EvalContext) (*EvaluationResult, error) {
    // High-performance evaluation logic
}

// Testing pattern (table-driven)
func TestEvaluationEngine_Evaluate(t *testing.T) {
    tests := []struct {
        name    string
        key     string
        context EvalContext
        want    *EvaluationResult
        wantErr bool
    }{
        {
            name: "boolean flag returns true for matching rule",
            key:  "test-flag",
            context: EvalContext{UserID: "user-1"},
            want: &EvaluationResult{Value: true, Reason: "TARGETING_MATCH"},
            wantErr: false,
        },
        // More cases...
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            engine := NewEvaluationEngine(mockCache, logger)
            got, err := engine.Evaluate(context.Background(), tt.key, tt.context)
            
            if (err != nil) != tt.wantErr {
                t.Errorf("unexpected error: %v", err)
            }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("got %v, want %v", got, tt.want)
            }
        })
    }
}

// Benchmark pattern (critical for evaluation engine)
func BenchmarkEvaluationEngine_Evaluate(b *testing.B) {
    engine := NewEvaluationEngine(cache, logger)
    ctx := context.Background()
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = engine.Evaluate(ctx, "benchmark-flag", evalContext)
    }
}
```

### Python (AI Agents / MCP Servers)
```python
# File organization
services/ai-agents/src/
├── agents/
│   ├── flag_design/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── test_agent.py
│   └── rollout_planner/
├── langgraph_workflows/
└── utils/

# LangGraph agent pattern
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    flag_config: dict
    validation_errors: list

def create_flag_design_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("parse_input", parse_natural_language)
    workflow.add_node("generate_rules", generate_targeting_rules)
    workflow.add_node("validate", validate_flag_config)
    
    workflow.set_entry_point("parse_input")
    workflow.add_edge("parse_input", "generate_rules")
    workflow.add_edge("generate_rules", "validate")
    
    return workflow.compile()

# Testing pattern (pytest)
def test_flag_design_agent_creates_valid_targeting_rule():
    # Arrange
    agent = create_flag_design_agent()
    input_state = {
        "messages": ["Enable feature for users in beta segment"],
        "flag_config": {},
        "validation_errors": []
    }
    
    # Act
    result = agent.invoke(input_state)
    
    # Assert
    assert result["flag_config"]["type"] == "boolean"
    assert "beta" in result["flag_config"]["targeting"]["segments"]
    assert len(result["validation_errors"]) == 0

# FastMCP server pattern
from fastmcp import FastMCP

mcp = FastMCP("{{project_name}}-flags")

@mcp.tool()
def create_flag(key: str, type: str, description: str) -> dict:
    """Create a new feature flag"""
    # Implementation
    return {"key": key, "created": True}

@mcp.resource("flags://{key}")
def get_flag(key: str) -> str:
    """Get flag configuration"""
    # Implementation
    return json.dumps(flag_data)
```

## Code Quality Checklist
- [ ] All functions have proper types (TS strict, Go types, Python type hints)
- [ ] Documentation (JSDoc/godoc/docstrings) for public APIs
- [ ] Error handling for all async operations
- [ ] Loading states for UI components (if frontend)
- [ ] Accessibility attributes (if frontend)
- [ ] No hardcoded values (use constants/config)
- [ ] Proper cleanup (defer in Go, finally in TS/Python)
- [ ] Performance consideration (hot paths optimized)

## OpenFeature Provider Implementation
When implementing OpenFeature providers (~300 lines):
- Follow OpenFeature SDK patterns
- Implement ResolutionDetails correctly
- Support evaluation context properly
- Handle hook lifecycle
- Streaming updates via provider events
- Offline/bootstrap support
- Pass OpenFeature test suites

## Performance Optimization (Go Data Plane)
- Use benchmarks to validate <5ms p99 target
- Optimize hot paths (evaluation engine)
- Minimize allocations in tight loops
- Use sync.Pool for frequent allocations
- Profile with pprof before optimizing
- Cache aggressively (in-memory + Redis)

## Common Patterns by Service

### Control Plane (Node.js)
- Express/Fastify for APIs
- TypeORM or Prisma for PostgreSQL
- ioredis for Redis
- Bull/BullMQ for job queues
- Winston for logging
- Joi/Zod for validation

### Data Plane (Go)
- net/http or fiber for HTTP
- pgx for PostgreSQL
- go-redis for Redis
- gorilla/websocket for streaming
- slog for structured logging
- validator/v10 for validation

### AI Agents (Python)
- LangGraph for agent workflows
- LangChain for LLM integration
- Pydantic for validation
- Prometheus client for metrics

### Frontend (Next.js)
- App Router (not Pages Router)
- React Query for server state
- Zustand for client state
- Tailwind + shadcn/ui
- React Hook Form + Zod

## Testing Tools
- **TypeScript**: Jest + React Testing Library + Supertest
- **Go**: testing package + testify + httptest
- **Python**: pytest + pytest-asyncio + pytest-mock
- **E2E**: Playwright (all languages)
- **Performance**: k6 or Artillery for load testing
