# Testing Standards

## Test Coverage Requirements

- **Minimum:** 80% line coverage
- **Target:** 90%+ for critical paths
- **100%:** For security-sensitive code

## Test Types

### 1. Unit Tests

**Purpose:** Test individual functions/classes in isolation

**When:** For all business logic

**Example (Python):**
```python
def test_calculate_discount():
    """Test discount calculation for different amounts."""
    assert calculate_discount(100, 0.1) == 10
    assert calculate_discount(0, 0.1) == 0
    assert calculate_discount(100, 0) == 0

def test_calculate_discount_invalid():
    """Test discount calculation with invalid inputs."""
    with pytest.raises(ValueError):
        calculate_discount(-100, 0.1)
    with pytest.raises(ValueError):
        calculate_discount(100, 1.5)
```

### 2. Integration Tests

**Purpose:** Test multiple components working together

**When:** For API endpoints, database operations, external services

**Example (TypeScript):**
```typescript
describe('User API', () => {
  it('should create and retrieve user', async () => {
    const user = await api.createUser({ name: 'Test' });
    const retrieved = await api.getUser(user.id);
    expect(retrieved).toEqual(user);
  });
});
```

### 3. End-to-End Tests

**Purpose:** Test complete user workflows

**When:** For critical user journeys

**Example (Puppeteer):**
```javascript
test('User can login and view dashboard', async () => {
  await page.goto('http://localhost:3000/login');
  await page.type('#email', 'test@example.com');
  await page.type('#password', 'password');
  await page.click('#login-button');
  await page.waitForSelector('#dashboard');
  expect(await page.title()).toBe('Dashboard');
});
```

## Test Structure

### Arrange-Act-Assert (AAA)

```python
def test_user_registration():
    # Arrange
    email = "test@example.com"
    password = "SecurePass123"
    
    # Act
    user = register_user(email, password)
    
    # Assert
    assert user.email == email
    assert user.is_active
    assert user.password_hash != password  # Should be hashed
```

### Given-When-Then (BDD)

```python
def test_shopping_cart():
    # Given: User has items in cart
    cart = ShoppingCart()
    cart.add_item(Item(price=10))
    cart.add_item(Item(price=20))
    
    # When: User applies discount code
    cart.apply_discount("SAVE10")
    
    # Then: Total reflects discount
    assert cart.total() == 27  # 30 - 10%
```

## Test Naming

**Pattern:** `test_<function>_<scenario>_<expected>`

**Examples:**
```python
test_login_valid_credentials_returns_token()
test_login_invalid_password_raises_error()
test_login_nonexistent_user_returns_none()
test_calculate_total_empty_cart_returns_zero()
test_calculate_total_with_discount_applies_percentage()
```

## Test Organization

### Directory Structure

```
project/
├── src/
│   ├── auth.py
│   ├── cart.py
│   └── payment.py
└── tests/
    ├── unit/
    │   ├── test_auth.py
    │   ├── test_cart.py
    │   └── test_payment.py
    ├── integration/
    │   └── test_checkout_flow.py
    └── e2e/
        └── test_user_journey.py
```

## What to Test

### ✅ DO Test:

- **Business logic:** Core functionality
- **Edge cases:** Empty inputs, null values, max values
- **Error conditions:** Invalid inputs, failures
- **Security:** Authentication, authorization, input validation
- **Critical paths:** User registration, checkout, payments

### ❌ DON'T Test:

- **Third-party libraries:** Trust they're tested
- **Simple getters/setters:** Unless they have logic
- **Generated code:** Like database models
- **UI styling:** Unless it affects functionality

## Test Independence

**Each test should:**
- Run independently
- Not depend on other tests
- Clean up after itself
- Use test fixtures/factories

**Example:**
```python
@pytest.fixture
def clean_database():
    """Provide clean database for each test."""
    setup_test_db()
    yield
    teardown_test_db()

def test_create_user(clean_database):
    """Test runs with fresh database."""
    user = create_user("test@example.com")
    assert user.id is not None
```

## Mocking

**Use mocks for:**
- External APIs
- Slow operations (database, file I/O)
- Non-deterministic behavior (time, random)

**Example (Python):**
```python
from unittest.mock import patch

@patch('requests.get')
def test_fetch_weather(mock_get):
    """Test weather fetching without actual HTTP call."""
    mock_get.return_value.json.return_value = {"temp": 72}
    
    weather = fetch_weather("Seattle")
    
    assert weather.temperature == 72
    mock_get.assert_called_once()
```

## Coverage Tools

### Python
```bash
pytest --cov=src --cov-report=html
```

### TypeScript/JavaScript
```bash
jest --coverage
```

### Go
```bash
go test -cover ./...
go test -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Performance Testing

**For critical paths:**
```python
import pytest

@pytest.mark.performance
def test_search_performance():
    """Search should complete within 100ms."""
    import time
    start = time.time()
    
    results = search("query")
    
    duration = time.time() - start
    assert duration < 0.1, f"Search took {duration}s (>100ms)"
```

## Continuous Integration

**Tests should:**
- Run on every commit
- Block merge if failing
- Report coverage
- Be fast (<5 minutes for unit tests)

**Example (GitHub Actions):**
```yaml
name: Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest --cov=src
      - name: Check coverage
        run: |
          coverage report --fail-under=80
```

---

**Write tests first (TDD). Keep them fast. Keep them green!** ✅

