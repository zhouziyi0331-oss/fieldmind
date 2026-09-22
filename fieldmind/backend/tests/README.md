# Test Configuration for FieldMind Backend

## Overview
This directory contains all tests for the FieldMind backend application.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_cache_service.py
│   ├── test_document_processor.py
│   ├── test_data_quality.py
│   └── test_knowledge_graph.py
├── integration/             # Integration tests
│   ├── test_api_projects.py
│   ├── test_api_dashboard.py
│   └── test_api_collaboration.py
└── performance/             # Performance tests
    └── test_query_performance.py
```

## Running Tests

### Install test dependencies
```bash
pip install pytest pytest-cov pytest-asyncio httpx
```

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run specific test file
```bash
pytest tests/unit/test_cache_service.py -v
```

### Run specific test function
```bash
pytest tests/unit/test_cache_service.py::test_cache_get_set -v
```

### Run tests matching a pattern
```bash
pytest -k "cache" -v
```

## Test Categories

### Unit Tests
Test individual functions and classes in isolation.
- Mock external dependencies
- Fast execution (<1s per test)
- High coverage target (>80%)

### Integration Tests
Test API endpoints and database interactions.
- Use test database
- Test real request/response flow
- Medium execution time (1-5s per test)

### Performance Tests
Test query performance and system load.
- Benchmark critical operations
- Ensure performance targets met
- Run separately from unit tests

## Test Database

Integration tests use a separate test database:
- SQLite in-memory for fast tests
- Automatically created and cleaned up
- Fixtures in `conftest.py` manage lifecycle

## Coverage Goals

| Module | Target Coverage |
|--------|----------------|
| Services | >80% |
| API Endpoints | >70% |
| Models | >60% |
| Utils | >90% |
| Overall | >70% |

## Writing Tests

### Use descriptive names
```python
def test_cache_should_return_none_for_missing_key():
    pass
```

### Follow AAA pattern
```python
def test_example():
    # Arrange
    cache = CacheService()
    
    # Act
    result = cache.get("key")
    
    # Assert
    assert result is None
```

### Use fixtures for setup
```python
@pytest.fixture
def sample_project(db_session):
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()
    return project
```

## Continuous Integration

Tests run automatically on:
- Every commit (via pre-commit hook)
- Every pull request (via GitHub Actions)
- Before deployment

## Troubleshooting

### Tests fail with import errors
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend/src"
```

### Database connection errors
Check that test database is properly isolated and cleaned up.

### Slow tests
Use `pytest --durations=10` to find slowest tests.
