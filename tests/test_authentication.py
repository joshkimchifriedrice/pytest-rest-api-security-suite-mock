import pytest
from src.api_client import ApiClient

@pytest.fixture
def api_client():
    """Provides unauthenticated API client"""
    return ApiClient(base_url="http://localhost:5000")

def test_successful_authentication(api_client):
    """Test successful authentication with valid credentials"""
    response = api_client.authenticate(username="admin", password="password")
    assert response.status_code == 200
    assert "token" in response.json()

def test_failed_authentication_wrong_password(api_client):
    """Test authentication fails with incorrect password"""
    response = api_client.authenticate(username="admin", password="wrong_password")
    assert response.status_code == 401
    assert "error" in response.json()

def test_failed_authentication_wrong_username(api_client):
    """Test authentication fails with incorrect username"""
    response = api_client.authenticate(username="wrong_user", password="password")
    assert response.status_code == 401
    assert "error" in response.json()

def test_failed_authentication_missing_credentials(api_client):
    """Test authentication fails with empty credentials"""
    response = api_client.authenticate(username="", password="")
    assert response.status_code == 401
    assert api_client.token is None

def test_token_format_is_valid(api_client):
    """Test that authentication returns a valid token format"""
    response = api_client.authenticate(username="admin", password="password")
    assert response.status_code == 200
    token = response.json().get("token")
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

def test_token_stored_in_client(api_client):
    """Test that token is stored in the API client after authentication"""
    response = api_client.authenticate(username="admin", password="password")
    assert response.status_code == 200
    token = response.json().get("token")
    assert api_client.token == token

def test_authentication_returns_error_message(api_client):
    """Test that failed authentication returns a descriptive error message"""
    response = api_client.authenticate(username="invalid_user", password="invalid_password")
    assert response.status_code == 401
    error_message = response.json().get("error")
    assert error_message is not None
    assert isinstance(error_message, str)
    assert len(error_message) > 0