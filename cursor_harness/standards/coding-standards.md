# Coding Standards

Generic coding standards for cursor-harness v3.0.

Projects can override by providing their own `docs/standards/` directory.

## General Principles

### 1. Code Quality

- **Readable:** Code should be self-documenting
- **Simple:** Prefer simple over clever
- **Consistent:** Follow project conventions
- **Tested:** Minimum 80% coverage

### 2. Naming Conventions

**Files:**
- Python: `snake_case.py`
- TypeScript/JavaScript: `kebab-case.ts`, `PascalCase.tsx` (components)
- Go: `snake_case.go`

**Variables/Functions:**
- Python: `snake_case`
- TypeScript/JavaScript: `camelCase`
- Go: `camelCase`

**Constants:**
- All languages: `UPPER_SNAKE_CASE`

**Classes:**
- All languages: `PascalCase`

### 3. Documentation

**Python:**
```python
def calculate_total(items: list[Item]) -> float:
    """
    Calculate total price of items.
    
    Args:
        items: List of items to total
    
    Returns:
        Total price as float
    
    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    return sum(item.price for item in items)
```

**TypeScript:**
```typescript
/**
 * Calculate total price of items.
 * 
 * @param items - Array of items to total
 * @returns Total price as number
 * @throws {Error} If items array is empty
 */
function calculateTotal(items: Item[]): number {
  if (items.length === 0) {
    throw new Error("Items array cannot be empty");
  }
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

**Go:**
```go
// CalculateTotal calculates the total price of items.
//
// Returns an error if the items slice is empty.
func CalculateTotal(items []Item) (float64, error) {
    if len(items) == 0 {
        return 0, errors.New("items slice cannot be empty")
    }
    total := 0.0
    for _, item := range items {
        total += item.Price
    }
    return total, nil
}
```

### 4. Error Handling

**Always handle errors explicitly:**

Python:
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

TypeScript:
```typescript
try {
  const result = await riskyOperation();
} catch (error) {
  logger.error('Operation failed', error);
  throw error;
}
```

Go:
```go
result, err := riskyOperation()
if err != nil {
    log.Printf("Operation failed: %v", err)
    return err
}
```

### 5. Testing

**Structure:**
- Test files next to source files
- One test file per source file
- Clear test names describing what's tested

**Coverage:**
- Minimum 80% line coverage
- Test happy path and edge cases
- Test error conditions

**Example (Python):**
```python
def test_calculate_total_success():
    """Test total calculation with valid items."""
    items = [Item(price=10), Item(price=20)]
    assert calculate_total(items) == 30

def test_calculate_total_empty():
    """Test total calculation with empty list."""
    with pytest.raises(ValueError, match="cannot be empty"):
        calculate_total([])
```

### 6. Code Structure

**Functions:**
- Single responsibility
- Max ~50 lines
- Clear, descriptive names
- Document complex logic

**Classes:**
- Single responsibility
- Encapsulate related behavior
- Clear interface (public methods)
- Document purpose

**Files:**
- Related code together
- Max ~500 lines
- Clear module boundaries

## Language-Specific Standards

### Python

- Use type hints: `def func(x: int) -> str:`
- Use f-strings: `f"Value: {x}"`
- Follow PEP 8
- Use `black` for formatting
- Use `pylint` for linting

### TypeScript/JavaScript

- Use TypeScript for type safety
- Avoid `any` type
- Use `const` by default, `let` when needed, never `var`
- Use async/await over callbacks
- Use ESLint + Prettier

### Go

- Use `gofmt` for formatting
- Use `go vet` for linting
- Follow effective Go guidelines
- Handle all errors
- Use meaningful variable names

## Security

### Never Commit:
- API keys
- Passwords
- Private keys
- Tokens
- Connection strings

### Use Environment Variables:
```python
import os
API_KEY = os.getenv("API_KEY")
```

### Validate Inputs:
```python
def process_email(email: str):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError("Invalid email")
```

### Use Parameterized Queries:
```python
# ✅ Good
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ❌ Bad
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

## Git Commits

**Format:**
```
<type>: <description>

[optional body]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `test` - Add/update tests
- `refactor` - Code refactoring
- `docs` - Documentation
- `style` - Formatting
- `chore` - Maintenance

**Examples:**
```
feat: add user authentication
fix: handle null values in parser
test: add edge cases for validation
refactor: simplify error handling
```

---

**These are defaults. Projects can override with their own standards!**

