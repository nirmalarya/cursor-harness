# System Instructions for All Agents

These instructions apply to all agents (initializer and coding).

## Tools Available

- `read_file(path)` - Read file contents
- `write_file(path, content)` - Create or overwrite file
- `edit_file(path, old_str, new_str)` - Replace text in file
- `run_command(command)` - Execute shell command

## Quality Standards

### Testing
- Write tests BEFORE implementation (TDD)
- Aim for 80%+ test coverage
- Test happy path and edge cases
- Run tests before marking feature complete

### Code Quality
- No `console.log` or `print` in production code
- Proper error handling (try/catch)
- Clear variable names
- Follow existing code patterns

### Security
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Validate all external inputs
- Use parameterized queries (no SQL injection)

### Commits
```
<type>: <description>

Types: feat, fix, test, refactor, docs, style, chore
Example: feat: add user authentication
```

## Project Standards

**Check for custom standards:**

```bash
# If project has custom standards, use them
if [ -d "docs/standards" ]; then
    cat docs/standards/coding-guidelines.md
    cat docs/standards/testing-standards.md
    cat docs/standards/security-requirements.md
fi
```

If project has `docs/standards/`, follow those.
Otherwise, use the quality standards above.

## Completion

When your assigned work is complete:
1. All tests pass
2. All changes committed
3. Progress file updated
4. Feature/enhancement marked as complete

For coding agents: Update the appropriate list file (feature_list.json, enhancement_list.json, etc).

