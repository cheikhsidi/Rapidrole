# Test Fixes Needed

## Summary
Tests are running but need updates for newer library versions. 24 tests passing, 37 failing.

## Issues to Fix

### 1. Missing greenlet dependency ✅ FIXED
Added `greenlet` to dev dependencies in pyproject.toml

### 2. AsyncClient API Change (httpx)
**Issue**: `AsyncClient(app=app)` no longer works in newer httpx versions

**Fix**: Use ASGITransport
```python
from httpx import ASGITransport

# Old way:
async with AsyncClient(app=app, base_url="http://test") as client:
    ...

# New way:
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    ...
```

**Files affected**:
- `tests/test_api.py` (all test methods)

### 3. LangChain Mock Issues
**Issue**: Cannot mock `ainvoke` on ChatOpenAI/ChatAnthropic objects (Pydantic v2 protection)

**Fix**: Mock at a different level or use actual test instances
```python
# Instead of mocking llm.ainvoke, mock the entire agent method
with patch.object(agent, "analyze", new_callable=AsyncMock) as mock_analyze:
    ...
```

**Files affected**:
- `tests/test_agents.py` (all agent tests)

### 4. Database Model ID Generation
**Issue**: `user.id is None` - SQLite in-memory doesn't auto-generate IDs without commit

**Fix**: Add session commit in test or use different assertion
```python
session.add(user)
await session.commit()
await session.refresh(user)
assert user.id is not None
```

**Files affected**:
- `tests/test_database.py::test_user_model_creation`

## Quick Wins
The embedding and some database tests are passing (24/61 tests). Focus on:
1. Run `uv sync` to install greenlet
2. Update AsyncClient usage pattern
3. Simplify agent tests to not mock internal LangChain objects

## Running Tests
```bash
# Install dependencies
uv sync

# Run all tests
make test-local

# Run specific test file
uv run pytest tests/test_embeddings.py -v

# Run tests that are passing
uv run pytest tests/test_embeddings.py tests/test_database.py::TestDatabaseModels -v
```
