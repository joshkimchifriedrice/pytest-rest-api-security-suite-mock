# Mock Firewall API Tests

This project implements a test suite for a mock firewall API, focusing on functionality and security testing relevant to Fortinet products. The mock API simulates the behavior of a real Fortinet API, allowing for comprehensive testing of various features and security measures.

## Project Structure

```
Pytest - REST API Security Suite
├── config
│   ├── __init__.py
│   └── test_config.py
├── src
│   ├── __init__.py
│   ├── api_client.py
│   └── mock_firewall_api.py
├── tests
│   ├── __init__.py
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_integration.py
│   └── test_policies_crud.py
├── pytest.ini
├── README.md
└── requirements.txt
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone https://github.com/joshkimchifriedrice/pytest-rest-api-security-suite-mock.git
   cd pytest-rest-api-security-suite-mock
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment. You can create one using:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Then install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. **Run the mock API:**
   You can start the mock firewall API by running:
   ```
   python src/mock_firewall_api.py
   ```

4. **Run the tests:**
   To execute the test suite, use:
   ```
   pytest
   ```

## Usage Examples

- **Authentication Testing:**
  The `tests/test_authentication.py` file tests the authentication process, ensuring that invalid tokens are handled correctly and valid credentials return proper tokens.

- **Authorization Testing:**
  The `tests/test_authorization.py` file verifies that protected endpoints require authentication, testing scenarios including missing tokens, invalid tokens, and malformed authorization headers.

- **Integration Testing:**
  The `tests/test_integration.py` file tests complete workflows including:
  - Full policy lifecycle (create → read → update → delete)
  - Multiple policy management in sequence
  - User session workflows with authentication and logout
  - Concurrent policy operations with threading
  - Reauthentication after token expiry
  - Request timeout handling

- **Policy CRUD Operations:**
  The `tests/test_policies_crud.py` file verifies that policies can be created, read, updated, and deleted as intended, including data integrity checks and edge cases.

### Authored by:
**Joshua Kim** - [GitHub Profile](https://github.com/joshkimchifriedrice)