# Testing Guide for TM1 Backup Service

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

Or install individually:
```bash
pip install pytest pytest-cov pytest-mock
```

## Running Tests

### Run All Tests
```bash
pytest test_app.py -v
```

### Run Specific Test Class
```bash
pytest test_app.py::TestBackupService -v
```

### Run Specific Test
```bash
pytest test_app.py::TestBackupService::test_backup_success -v
```

### Run with Coverage Report
```bash
pytest test_app.py -v --cov=app --cov-report=html
```

This creates an HTML coverage report in `htmlcov/index.html`

### Run with Coverage in Terminal
```bash
pytest test_app.py -v --cov=app --cov-report=term-missing
```

### Run Tests and Stop on First Failure
```bash
pytest test_app.py -v -x
```

### Run Tests with Detailed Output
```bash
pytest test_app.py -v -s
```

## Test Coverage

The test suite covers:

### 1. Path Resolution (`TestPathResolution`)
- ✓ Frozen app path resolution
- ✓ Script path resolution

### 2. Version Management (`TestVersionAndYearRetrieval`)
- ✓ Reading version from file
- ✓ Handling missing version file
- ✓ Invalid version file format
- ✓ Reading year from file
- ✓ Handling missing/empty year file

### 3. Path Validation (`TestPathValidation`)
- ✓ Valid paths
- ✓ Missing source directory
- ✓ Source is file, not directory
- ✓ Missing destination directory
- ✓ Missing log directory
- ✓ Missing 7-Zip executable

### 4. Backup Service (`TestBackupService`)
- ✓ Initialization with default parameters
- ✓ Initialization with custom parameters
- ✓ Command building without feeders
- ✓ Command building with feeders
- ✓ Command building for ZIP format
- ✓ Successful backup operation
- ✓ 7-Zip failure handling
- ✓ Backup file not created handling
- ✓ Cleanup of old backup files
- ✓ Keeping files under retention limit
- ✓ Log file cleanup (old files)
- ✓ Log file cleanup (recent files)

### 5. Main Function (`TestMainFunction`)
- ✓ Successful execution
- ✓ Path validation failure
- ✓ Backup operation failure
- ✓ Feeders option handling
- ✓ ZIP format option handling
- ✓ Invalid parameter handling

### 6. Logging (`TestLogging`)
- ✓ Log handler creation
- ✓ File and console output

### 7. Integration Tests (`TestIntegration`)
- ✓ Full backup workflow

## Test Organization

Tests are organized by functionality:

```
test_app.py
├── TestPathResolution       # Path handling tests
├── TestVersionAndYearRetrieval  # Version/year file tests
├── TestBackupError          # Exception tests
├── TestPathValidation       # Input validation tests
├── TestBackupService        # Core backup functionality
├── TestMainFunction         # Main entry point tests
├── TestLogging             # Logging setup tests
└── TestIntegration         # End-to-end tests
```

## Mocking Strategy

The tests use mocking to avoid:
- Creating actual backup files
- Running real 7-Zip compression
- Making filesystem modifications
- Executing subprocess calls

Key mocks used:
- `subprocess.run` - Simulates 7-Zip execution
- `os.path.exists` - Controls file existence checks
- `os.path.getsize` - Controls file size reporting
- `BackupService` - Tests main function without actual backups

## Expected Test Results

When all tests pass, you should see output like:

```
test_app.py::TestPathResolution::test_resolve_paths_frozen_app PASSED     [  3%]
test_app.py::TestPathResolution::test_resolve_paths_script PASSED        [  6%]
...
================================ 35 passed in 2.45s ================================
```

## Coverage Goals

Target coverage: **>90%**

Key areas to maintain coverage:
- Path validation (100%)
- Backup operations (>95%)
- Error handling (100%)
- Command building (100%)
- Cleanup operations (>90%)

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest test_app.py -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Adding New Tests

When adding new functionality to `app.py`:

1. **Create a test class** for the new feature
2. **Write tests for happy path** (expected behavior)
3. **Write tests for error conditions** (edge cases)
4. **Mock external dependencies** (filesystem, subprocess)
5. **Run coverage check** to ensure new code is tested
6. **Update this guide** with new test descriptions

### Example Template

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_success(self):
        """Test successful feature execution."""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_feature_failure(self):
        """Test feature failure handling."""
        # Arrange
        # Act
        # Assert
        pass
```

## Troubleshooting

### Tests Fail on Import
```bash
# Make sure app.py is in the Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Coverage Not Working
```bash
# Install coverage plugin
pip install pytest-cov

# Verify installation
pytest --version
```

### Tests Run Slowly
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest test_app.py -n auto
```

### Mocking Issues
```bash
# Make sure unittest.mock is available (Python 3.3+)
python --version

# For older Python versions
pip install mock
```

## Best Practices

1. **Keep tests independent** - Each test should run in isolation
2. **Use fixtures** - Share setup code with pytest fixtures
3. **Name tests clearly** - Use descriptive test names
4. **Test one thing** - Each test should verify one behavior
5. **Mock external calls** - Don't depend on external systems
6. **Clean up** - Use tmp_path fixture for temporary files
7. **Run tests often** - Before commits and during development

## Quick Commands Reference

```bash
# Run all tests
pytest test_app.py -v

# Run with coverage
pytest test_app.py --cov=app --cov-report=html

# Run specific test class
pytest test_app.py::TestBackupService -v

# Run in watch mode (requires pytest-watch)
ptw test_app.py

# Generate coverage badge
coverage-badge -o coverage.svg -f
```