# cursor-harness v3.0 - Design Document

## The Problem with v2.x

**We over-engineered!**

```
v2.x complexity:
- Multi-agent orchestration (6 agents)
- Complex workflow state management
- Session management
- Progress tracking
- Loop detection
- Browser cleanup
- Infrastructure validation
- Stream parsing
- 200+ files, 10K+ lines

Result: Slow, unreliable, hard to debug
```

## The Anthropic Demo Insight

**Their demo works because it's SIMPLE:**

```python
# anthropic/autonomous-coding (simplified)
def run_autonomous_coding():
    messages = [system_prompt, user_task]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4",
            messages=messages,
            tools=[ReadTool, WriteTool, EditTool, BashTool]
        )
        
        if response.stop_reason == "end_turn":
            break
        
        for tool_use in response.tool_uses:
            result = execute_tool(tool_use)
            messages.append(tool_result)
```

**~200 lines total. Simple, reliable, works!**

## v3.0 Design: Simple Core + Powerful Features

### Core Loop (300 lines)

```python
class CursorHarness:
    def __init__(self, project_dir, mode, spec):
        self.project_dir = Path(project_dir)
        self.mode = mode  # greenfield, enhancement, bugfix, backlog
        self.spec = spec
        self.state = self._load_or_create_state()
        
    def run(self):
        """Main autonomous loop - SIMPLE like Anthropic."""
        
        # 1. Setup (once)
        self._validate_and_fix_infrastructure()
        self._initialize_session()
        
        # 2. Main loop
        while not self._is_complete():
            work_item = self._get_next_work()
            
            if not work_item:
                break  # All done!
            
            # Execute work
            success = self._execute_work(work_item)
            
            # Validate
            if success and self._validate_work(work_item):
                self._mark_complete(work_item)
            else:
                self._handle_failure(work_item)
        
        # 3. Final validation
        self._run_final_validation()
        
        print("✅ Project complete!")
    
    def _execute_work(self, work_item):
        """Execute work using cursor-agent CLI."""
        
        # Build prompt
        prompt = self._build_prompt(work_item)
        
        # Run cursor-agent
        result = subprocess.run(
            ["cursor-agent", "--prompt", prompt],
            cwd=self.project_dir,
            capture_output=True,
            timeout=self._get_timeout()
        )
        
        return result.returncode == 0
```

**Simple loop. Clear flow. Easy to debug.**

## Mode Adapters

**Different modes = different work sources:**

### Greenfield Mode
```python
# modes/greenfield.py
class GreenfieldMode:
    def get_next_work(self):
        """Get next feature from feature_list.json."""
        features = load_json("feature_list.json")
        return next(f for f in features if not f["passing"])
    
    def is_complete(self):
        features = load_json("feature_list.json")
        return all(f["passing"] for f in features)
```

### Enhancement Mode
```python
# modes/enhancement.py
class EnhancementMode:
    def get_next_work(self):
        """Get next enhancement from spec."""
        # Parse spec for features to add
        return next_enhancement_from_spec()
    
    def is_complete(self):
        return all_enhancements_implemented()
```

### Backlog Mode
```python
# modes/backlog.py
class BacklogMode:
    def __init__(self, org, project):
        self.ado = AzureDevOpsClient(org, project)
    
    def get_next_work(self):
        """Get next PBI from Azure DevOps."""
        pbis = load_json(".cursor/backlog-state.json")
        return next(p for p in pbis if not p["processed"])
    
    def is_complete(self):
        pbis = load_json(".cursor/backlog-state.json")
        return all(p["processed"] for p in pbis)
```

## Validation Layer

**Real validation - not just "agent said done":**

```python
# validators/work_validator.py
class WorkValidator:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.e2e_tester = E2ETester(project_dir)
        self.secrets_scanner = SecretsScanner(project_dir)
        self.quality_checker = QualityChecker(project_dir)
    
    def validate(self, work_item) -> ValidationResult:
        """Comprehensive validation."""
        
        results = []
        
        # 1. Code exists
        if not self._code_created_for(work_item):
            results.append(ValidationFailure("No code created"))
        
        # 2. Tests exist and pass
        test_result = self._run_tests()
        if not test_result.passed:
            results.append(ValidationFailure(f"Tests failed: {test_result}"))
        
        # 3. E2E validation (if user-facing)
        if self._is_user_facing(work_item):
            e2e_result = self.e2e_tester.test(work_item)
            if not e2e_result.passed:
                results.append(ValidationFailure(f"E2E failed: {e2e_result}"))
        
        # 4. No secrets exposed
        secrets = self.secrets_scanner.scan()
        if secrets:
            results.append(ValidationFailure(f"Secrets exposed: {secrets}"))
        
        # 5. Quality checks
        quality = self.quality_checker.check()
        if quality.coverage < 80:
            results.append(ValidationFailure(f"Coverage {quality.coverage}% < 80%"))
        
        return ValidationResult(
            passed=len(results) == 0,
            failures=results
        )
```

## Infrastructure Self-Healing

**Auto-fix issues, don't just report them:**

```python
# infra/healer.py
class InfrastructureHealer:
    def validate_and_fix(self):
        """Validate infrastructure and auto-fix issues."""
        
        fixes = []
        
        # Docker services
        if not self._docker_running():
            print("🔧 Starting Docker services...")
            self._run("docker compose up -d")
            fixes.append("Started Docker")
        
        # Database migrations
        if self._needs_migrations():
            print("🔧 Running database migrations...")
            self._run("alembic upgrade head")
            fixes.append("Applied migrations")
        
        # MinIO buckets
        if self._minio_buckets_missing():
            print("🔧 Creating MinIO buckets...")
            self._create_buckets()
            fixes.append("Created buckets")
        
        if fixes:
            print(f"✅ Auto-fixed: {', '.join(fixes)}")
        
        return True
```

## Loop Detection

**Prevent infinite loops:**

```python
# infra/loop_detector.py
class LoopDetector:
    def __init__(self, timeout_minutes=60):
        self.start_time = time.time()
        self.timeout = timeout_minutes * 60
        self.file_reads = defaultdict(int)
        self.last_progress = time.time()
    
    def check(self, event: str, data: dict) -> bool:
        """Returns True if loop detected."""
        
        # Timeout
        if time.time() - self.start_time > self.timeout:
            return True
        
        # Repeated file reads
        if event == "file_read":
            self.file_reads[data["path"]] += 1
            if self.file_reads[data["path"]] > 10:
                return True
        
        # No progress
        if event == "progress":
            self.last_progress = time.time()
        
        if time.time() - self.last_progress > 600:  # 10 min
            return True
        
        return False
```

## Comparison Table

| Feature | Anthropic Demo | v2.x | v3.0 |
|---------|----------------|------|------|
| **Lines of code** | ~200 | ~10,000 | ~2,000 |
| **Core complexity** | Simple | Very complex | Simple |
| **Greenfield** | ✅ | ✅ | ✅ |
| **Brownfield** | ❌ | ✅ | ✅ |
| **Enhancement** | ❌ | ✅ | ✅ |
| **Backlog** | ❌ | ✅ | ✅ |
| **E2E Testing** | ❌ | ⚠️ (buggy) | ✅ |
| **Security Scanning** | ❌ | ❌ | ✅ |
| **Self-Healing** | ❌ | ✅ | ✅ |
| **Loop Detection** | ❌ | ✅ | ✅ |
| **Reliability** | ✅ (simple) | ❌ (complex) | ✅ (simple+tested) |
| **Debuggable** | ✅ | ❌ | ✅ |

## Success Criteria

**v3.0 is ready when:**

1. ✅ Can build greenfield app (like Anthropic demo)
2. ✅ Can enhance existing app (brownfield)
3. ✅ Can process Azure DevOps backlog
4. ✅ E2E tests catch CSS errors (unlike v1.0)
5. ✅ Secrets scanning catches exposed keys (unlike v1.0)
6. ✅ Runs 24+ hours without loops (unlike v2.x)
7. ✅ Clear, debuggable code (unlike v2.x)

## Development Approach

**Incremental, tested, always working:**

```
Day 1: Core loop + greenfield mode
       → Test on hello-world app
       → MUST WORK before Day 2!

Day 2: Enhancement + backlog modes
       → Test on Togglr, AutoGraph
       → MUST WORK before Day 3!

Day 3: Infrastructure healing
       → Test with Docker down, DB broken
       → MUST WORK before Day 4!

... etc
```

**Never move forward with broken code!**

---

**This is how we build reliable software!** 🎯

