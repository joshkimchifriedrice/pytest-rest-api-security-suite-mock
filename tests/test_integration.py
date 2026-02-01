import pytest
from src.api_client import ApiClient
import threading
import requests

@pytest.fixture
def api_client():
    return ApiClient(base_url="http://localhost:5000")

@pytest.fixture
def authenticated_client(api_client):
    """Provides an authenticated API client"""
    api_client.authenticate(username="admin", password="password")
    return api_client

@pytest.fixture
def sample_policy():
    """Provides sample policy data for testing"""
    return {
        "name": "Test Policy",
        "port": 443,
        "action": "allow",
        "source": "10.0.0.0/24",
        "destination": "any"
    }

def test_complete_policy_lifecycle(authenticated_client, sample_policy):
    """Test complete workflow: authenticate -> create -> read -> update -> delete"""
    # Create policy
    create_response = authenticated_client.post("/api/policies", json=sample_policy)
    assert create_response.status_code == 201
    policy_id = create_response.json()['id']
    assert create_response.json()["name"] == sample_policy["name"]
    
    # Read - Get specific policy
    get_response = authenticated_client.get(f"/api/policies/{policy_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == policy_id
    assert get_response.json()["name"] == sample_policy["name"]
    
    # Update policy
    update_data = {"action": "deny", "port": 80}
    update_response = authenticated_client.put(f"/api/policies/{policy_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["action"] == "deny"
    assert update_response.json()["port"] == 80
    assert update_response.json()["name"] == sample_policy["name"]  # Original field preserved
    
    # Verify update persisted
    verify_response = authenticated_client.get(f"/api/policies/{policy_id}")
    assert verify_response.status_code == 200
    assert verify_response.json()["action"] == "deny"
    assert verify_response.json()["port"] == 80
    
    # Delete policy
    delete_response = authenticated_client.delete(f"/api/policies/{policy_id}")
    assert delete_response.status_code == 204
    
    # Verify deletion
    deleted_response = authenticated_client.get(f"/api/policies/{policy_id}")
    assert deleted_response.status_code == 404

def test_multiple_policies_management(authenticated_client, sample_policy):
    """Test managing multiple policies in sequence"""
    # Create multiple policies
    policies_to_create = [
        {**sample_policy, "name": "Allow_HTTPS", "port": 443},
        {**sample_policy, "name": "Allow_HTTP", "port": 80},
        {**sample_policy, "name": "Deny_SSH", "port": 22, "action": "deny"}
    ]
    
    created_ids = []
    for policy_data in policies_to_create:
        response = authenticated_client.post("/api/policies", json=policy_data)
        assert response.status_code == 201
        created_ids.append(response.json()['id'])
    
    # Verify all created
    all_policies_response = authenticated_client.get("/api/policies")
    assert all_policies_response.status_code == 200
    all_policies = all_policies_response.json()
    assert len(all_policies) >= 3
    
    # Verify each policy exists with correct data
    for i, policy_id in enumerate(created_ids):
        policy_response = authenticated_client.get(f"/api/policies/{policy_id}")
        assert policy_response.status_code == 200
        assert policy_response.json()["name"] == policies_to_create[i]["name"]
    
    # Update middle policy
    update_response = authenticated_client.put(f"/api/policies/{created_ids[1]}", json={"action": "deny"})
    assert update_response.status_code == 200
    assert update_response.json()["action"] == "deny"
    
    # Delete first policy
    delete_response = authenticated_client.delete(f"/api/policies/{created_ids[0]}")
    assert delete_response.status_code == 204
    
    # Verify first policy deleted but others remain
    assert authenticated_client.get(f"/api/policies/{created_ids[0]}").status_code == 404
    assert authenticated_client.get(f"/api/policies/{created_ids[1]}").status_code == 200
    assert authenticated_client.get(f"/api/policies/{created_ids[2]}").status_code == 200

def test_user_session_workflow(api_client, sample_policy):
    """Test complete user session from login to logout operations"""
    # Step 1: Authenticate
    auth_response = api_client.authenticate(username="admin", password="password")
    assert auth_response.status_code == 200
    assert "token" in auth_response.json()
    assert api_client.token is not None
    
    # Step 2: Perform authenticated operations
    # Create a policy
    create_response = api_client.post("/api/policies", json=sample_policy)
    assert create_response.status_code == 201
    policy_id = create_response.json()['id']
    
    # Read policies
    get_response = api_client.get("/api/policies")
    assert get_response.status_code == 200
    policies = get_response.json()
    assert any(p['id'] == policy_id for p in policies)
    
    # Update policy
    update_response = api_client.put(f"/api/policies/{policy_id}", json={"action": "deny"})
    assert update_response.status_code == 200
    
    # Delete policy
    delete_response = api_client.delete(f"/api/policies/{policy_id}")
    assert delete_response.status_code == 204
    
    # Step 3: Simulate logout by clearing token
    api_client.token = None
    
    # Step 4: Verify unauthorized access after token cleared
    unauthorized_response = api_client.get("/api/policies")
    assert unauthorized_response.status_code == 401

def test_concurrent_policy_operations(api_client, sample_policy):
    """Test simultaneous policy creation with threading"""
    # Authenticate once, reuse token
    api_client.authenticate(username="admin", password="password")
    
    results = []
    threads = []
    
    def create_policy(policy_name, port):
        """Function to run in thread"""
        policy_data = {**sample_policy, "name": policy_name, "port": port}
        response = api_client.post("/api/policies", json=policy_data)
        results.append({
            'name': policy_name,
            'status_code': response.status_code,
            'response': response.json()
        })
    
    # Create 20 threads that will try to create policies simultaneously
    for i in range(20):
        thread = threading.Thread(
            target=create_policy,
            args=(f"Concurrent_Policy_{i}", 9000 + i)
        )
        threads.append(thread)
    
    # Start all threads at once (as close to simultaneous as possible)
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all creations succeeded
    assert len(results) == 20
    for result in results:
        assert result['status_code'] == 201
        assert 'id' in result['response']
    
    # Verify all policies have unique IDs (no race condition)
    policy_ids = [r['response']['id'] for r in results]
    assert len(policy_ids) == len(set(policy_ids)), "Duplicate IDs found - race condition!"
    
    # Verify all policies exist in database
    all_policies = api_client.get("/api/policies").json()
    created_ids = {p['id'] for p in all_policies}
    for policy_id in policy_ids:
        assert policy_id in created_ids

def test_reauthentication_after_token_expiry(api_client, sample_policy):
    """Test that user can reauthenticate and continue operations"""
    # First authentication
    auth_response1 = api_client.authenticate(username="admin", password="password")
    assert auth_response1.status_code == 200
    first_token = api_client.token
    assert first_token is not None
    
    # Create a policy with first token
    create_response = api_client.post("/api/policies", json=sample_policy)
    assert create_response.status_code == 201
    policy_id = create_response.json()['id']
    
    # Simulate token expiry by clearing token
    api_client.token = None
    
    # Verify unauthorized access
    unauthorized_response = api_client.get("/api/policies")
    assert unauthorized_response.status_code == 401
    
    # Reauthenticate
    auth_response2 = api_client.authenticate(username="admin", password="password")
    assert auth_response2.status_code == 200
    second_token = api_client.token
    assert second_token is not None
    # Token should be different (in real system with unique tokens)
    assert second_token != first_token
    
    # Verify access restored with new token
    get_response = api_client.get("/api/policies")
    assert get_response.status_code == 200
    
    # Can perform operations with new token
    update_response = api_client.put(f"/api/policies/{policy_id}", json={"action": "deny"})
    assert update_response.status_code == 200
    
    # Clean up
    delete_response = api_client.delete(f"/api/policies/{policy_id}")
    assert delete_response.status_code == 204

def test_request_timeout_handling():
    """Test that HTTP requests timeout after configured duration"""
    # Create client with very short timeout
    client = ApiClient(base_url="http://httpbin.org")
    client.timeout = 2  # 2 second timeout
    
    # Test with endpoint that deliberately delays longer than timeout
    with pytest.raises(requests.exceptions.Timeout):
        # httpbin.org/delay/5 waits 5 seconds before responding
        # Should timeout after 2 seconds
        client.get("/delay/5")

def test_timeout_with_unresponsive_server():
    """Test timeout with a non-existent server"""
    client = ApiClient(base_url="http://10.255.255.1")
    
    with pytest.raises((requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        client.get("/api/policies")
