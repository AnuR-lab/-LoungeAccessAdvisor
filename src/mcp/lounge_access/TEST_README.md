# Unit Tests for LoungeAccessAdvisor API Client

This directory contains comprehensive unit tests for the `get_user` method and other functionality in the LoungeAccessClient.

## Test Files

- **`test_api_client.py`** - Comprehensive unit tests for API client methods (users + lounges)
- **`test_lounge_service.py`** - Unit tests for the LoungeService class
- **`test_lounge_functionality.py`** - Simplified business logic tests (no AWS dependencies)
- **`test_lambda_handler.py`** - Unit tests for Lambda handler (existing)
- **`run_tests.py`** - Test runner script for all tests
- **`pytest.ini`** - Pytest configuration

## Running Tests

### Option 1: Quick Business Logic Tests (Recommended for Development)
```bash
cd src/mcp/lounge_access
python3 test_lounge_functionality.py
```
*This runs comprehensive tests without requiring AWS credentials or DynamoDB setup.*

### Option 2: Using the full test runner script
```bash
cd src/mcp/lounge_access
python3 run_tests.py
```
*Note: Requires AWS credentials to be configured for DynamoDB tests.*

### Option 3: Using unittest directly
```bash
cd src/mcp/lounge_access
python3 -m unittest test_api_client.py -v
python3 -m unittest test_lounge_service.py -v
```

### Option 4: Using pytest (if installed)
```bash
cd src/mcp/lounge_access
pip install pytest
pytest test_api_client.py -v
pytest test_lounge_service.py -v
```

### Option 5: Running specific test classes
```bash
python3 -m unittest test_api_client.TestLoungeAccessClientLoungeOperations -v
python3 -m unittest test_lounge_service.TestLoungeServiceGetLoungesByAirport -v
```

## Test Coverage

The tests cover the following scenarios:

### 👤 **User Profile Tests (`get_user`):**
#### ✅ **Success Cases:**
- Normal user retrieval with valid data
- User retrieval with partial data
- Multiple sequential calls

#### ❌ **Error Cases:**
- User not found (returns None)
- Empty string user_id
- None as user_id parameter
- Whitespace-only user_id
- Special characters in user_id
- Very long user_id
- Service exceptions

### 🏨 **Lounge Operations Tests:**
#### ✅ **Success Cases:**
- `get_lounges_by_airport` - Retrieve all lounges at an airport
- `get_lounge_by_id` - Get specific lounge details
- `search_lounges_by_access_provider` - Filter by access provider
- `get_lounges_with_amenity` - Filter by amenities
- `create_sample_lounges` - Create test data

#### ❌ **Error Cases:**
- Empty/None airport codes and parameters
- Invalid data types (numbers, lists, etc.)
- Whitespace-only inputs
- Missing required fields in data
- Service exceptions

#### � **Search & Filter Tests:**
- Case-insensitive searches
- Partial string matching
- Access provider filtering
- Amenity filtering
- No matches handling

### �🔧 **Integration Cases:**
- Service delegation
- Method integration
- Initialization testing
- Multiple operation workflows

## Test Structure

Each test class focuses on a specific area:

1. **`TestLoungeAccessClientGetUser`** - Comprehensive get_user testing
2. **`TestLoungeAccessClientCreateSampleUsers`** - create_sample_users testing  
3. **`TestLoungeAccessClientInitialization`** - Constructor testing
4. **`TestLoungeAccessClientIntegration`** - Integration scenarios

## Mocking Strategy

The tests use `unittest.mock` to:
- Mock the `UserProfileService` to avoid DynamoDB calls
- Test error conditions and edge cases
- Verify method calls and parameters
- Isolate the API client logic

## Example Test Output

```
test_get_user_success (test_api_client.TestLoungeAccessClientGetUser) ... ok
test_get_user_not_found (test_api_client.TestLoungeAccessClientGetUser) ... ok
test_get_user_empty_string (test_api_client.TestLoungeAccessClientGetUser) ... ok
test_get_user_service_exception (test_api_client.TestLoungeAccessClientGetUser) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.025s

OK
```

## Adding New Tests

To add new tests for `get_user`:

1. Add new test methods to the appropriate test class
2. Follow the naming convention: `test_get_user_<scenario>`
3. Use the AAA pattern (Arrange, Act, Assert)
4. Mock external dependencies
5. Test both success and failure scenarios

## Coverage Goals

- **Line Coverage**: > 95%
- **Branch Coverage**: > 90%
- **Function Coverage**: 100%

Run with coverage:
```bash
pip install coverage
coverage run -m unittest test_api_client.py
coverage report
coverage html
```