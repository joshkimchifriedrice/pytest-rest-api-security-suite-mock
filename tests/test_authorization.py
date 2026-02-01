import pytest
from src.api_client import ApiClient
import requests

@pytest.fixture
def api_client():
    return ApiClient(base_url="http://localhost:5000")

def test_get_policies_without_token(api_client):
    """Test accessing protected endpoint without authentication"""
    response = api_client.get("/api/policies")
    assert response.status_code == 401
    assert "error" in response.json()

def test_create_policy_without_token(api_client):
    """Test creating policy without authentication"""
    response = api_client.post("/api/policies", json={"name": "Test"})
    assert response.status_code == 401

def test_update_policy_without_token(api_client):
    """Test updating policy without authentication"""
    response = api_client.put("/api/policies/1", json={"action": "deny"})
    assert response.status_code == 401

def test_delete_policy_without_token(api_client):
    """Test deleting policy without authentication"""
    response = api_client.delete("/api/policies/1")
    assert response.status_code == 401

def test_invalid_token_rejected(api_client):
    """Test that invalid token is rejected"""
    api_client.token = "invalid_fake_token_12345"
    response = api_client.get("/api/policies")
    assert response.status_code == 401

def test_malformed_authorization_header(api_client):
    """Test malformed Authorization header without Bearer prefix"""
    # Step 1: Authenticate and verify it works with valid Bearer token
    auth_response = api_client.authenticate(username="admin", password="password")
    assert auth_response.status_code == 200
    assert api_client.token is not None
    
    # Step 2: Make successful request with proper Bearer token
    valid_response = api_client.get("/api/policies")
    assert valid_response.status_code == 200, "Valid Bearer token should work"
    
    # Step 3: Send request without Bearer prefix (bypass api_client to test malformed header)
    # Use the valid token but omit "Bearer " prefix
    malformed_response = requests.get(
        f"{api_client.base_url}/api/policies",
        headers={'Authorization': api_client.token}  # Missing "Bearer " prefix
    )
    assert malformed_response.status_code == 401, "Request without Bearer prefix should fail"