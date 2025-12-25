# Test Quality Standards

**ALL tests must meet these standards (Puppeteer or API)**

---

## ✅ HIGH QUALITY TEST - Characteristics:

### 1. Tests Complete Workflow
```python
# ❌ BAD: Tests one action in isolation
puppeteer_click('button#save')

# ✅ GOOD: Tests complete user journey
puppeteer_navigate('http://localhost:3000')
puppeteer_click('a[href="/login"]')
puppeteer_type('#email', 'test@example.com')
puppeteer_type('#password', 'password123')
puppeteer_click('button[type=submit]')
puppeteer_wait_for(text='Dashboard')  # Verify success!
```

### 2. Verifies Data Persistence
```python
# ❌ BAD: No persistence check
create_diagram()
# Test ends - never verifies data saved!

# ✅ GOOD: Verifies persistence
diagram_id = create_diagram()
puppeteer_navigate(f'http://localhost:3000/canvas/{diagram_id}')
# Reload page
puppeteer_navigate(f'http://localhost:3000/canvas/{diagram_id}')
puppeteer_wait_for(text='Expected Content')  # Still there!
```

### 3. Has Clear Assertions
```python
# ❌ BAD: No verification
puppeteer_click('button#save')
# No check if save succeeded!

# ✅ GOOD: Multiple assertions
puppeteer_click('button#save')
puppeteer_wait_for(text='Saved successfully')  # Success message
verify_in_database(diagram_id)  # Data in DB
verify_no_console_errors()  # No errors
```

### 4. Tests Error Cases
```python
# ❌ BAD: Only happy path
login('valid@example.com', 'password')

# ✅ GOOD: Tests failures too
# Happy path
login('valid@example.com', 'password')
verify_success()

# Error cases
login('invalid@example.com', 'wrong')
verify_error_message('Invalid credentials')

login('', '')
verify_error_message('Email required')
```

### 5. Uses Real Data (Not Mocked)
```python
# ❌ BAD: Everything mocked
mock_database.return_value = {'id': 1}
mock_api.return_value = 200

# ✅ GOOD: Real services
response = requests.post('http://localhost:8080/api/diagrams', ...)
# Actual API call!
# Actual database!
# Real integration!
```

---

## 📊 Quality Assessment Rubric:

**Score each test 1-5:**

**5/5 - EXCELLENT:**
- Complete workflow ✅
- Persistence tested ✅
- Error cases ✅
- Real services ✅
- Multiple assertions ✅

**3-4/5 - GOOD:**
- Complete workflow ✅
- Persistence tested ✅
- Missing error cases ⚠️
- Real services ✅
- Some assertions ⚠️

**2/5 - PARTIAL:**
- Partial workflow ⚠️
- No persistence ❌
- No error cases ❌
- Real services ✅
- Few assertions ⚠️

**1/5 - LOW:**
- Single action ❌
- No persistence ❌
- No error cases ❌
- Mocked services ❌
- No assertions ❌

---

## 🎯 Conversion with Quality Improvement:

**Original Playwright test (2/5 quality):**
```python
# test_save.py (Playwright - LOW quality)
async def test_save():
    page = await browser.new_page()
    await page.goto('http://localhost:3000/canvas/123')
    await page.click('button#save')
    # That's it! No verification!
```

**Converted + IMPROVED (5/5 quality):**
```python
# test_save.py (Puppeteer - HIGH quality)
def test_save_diagram():
    # 1. Setup: Create test user and diagram
    user = create_test_user()
    login_with_puppeteer(user.email, user.password)
    
    # 2. Create diagram
    puppeteer_click('button#create-diagram')
    puppeteer_type('#title', 'Test Diagram')
    puppeteer_click('button#create')
    diagram_id = extract_id_from_url()
    
    # 3. Draw on canvas
    puppeteer_click('[data-testid=rectangle-tool]')
    puppeteer_click_at(100, 100)  # Draw shape
    
    # 4. Save
    puppeteer_click('button#save')
    puppeteer_wait_for(text='Saved successfully')  # ✅ Success message
    
    # 5. VERIFY PERSISTENCE (critical!)
    puppeteer_navigate(f'http://localhost:3000/canvas/{diagram_id}')  # Reload!
    verify_shape_exists_at(100, 100)  # ✅ Drawing still there!
    
    # 6. Verify in database
    verify_diagram_in_db(diagram_id)  # ✅ Data persisted!
    
    # 7. Verify no errors
    verify_no_console_errors()  # ✅ Clean console!
    
    print("✅ Save diagram - COMPREHENSIVE TEST PASSED")
```

**Same feature, but test is now 5x better!**

---

## 🎊 So The Agent Will:

**Not just convert syntax!**

**It will:**
1. ✅ Read Playwright test
2. ✅ Assess its quality
3. ✅ **IMPROVE** it while converting:
   - Add persistence checks
   - Add error cases
   - Add complete workflows
   - Add more assertions
4. ✅ Convert to Puppeteer
5. ✅ RUN the improved test
6. ✅ Only mark passing if HIGH quality test passes!

**Result: Better tests + Puppeteer standardization!** 🎯

---

**This ensures quality improvement, not just tool migration!** ✨

**Start it now - agent will improve test quality while converting!** 🚀
