import pytest
from src.api_client import ApiClient

@pytest.fixture
def api_client():
    """Provides authenticated API client"""
    client = ApiClient(base_url="http://localhost:5000")
    client.authenticate(username="admin", password="password")
    return client

@pytest.fixture
def sample_policy():
    """Provides sample policy data"""
    return {
        "name": "Test Policy",
        "port": 8080,
        "action": "allow",
        "source": "10.0.0.0/24",
        "destination": "any"
    }

@pytest.fixture
def created_policy(api_client, sample_policy):
    """Creates a policy and returns the response"""
    response = api_client.post("/api/policies", json=sample_policy)
    return response

@pytest.fixture
def created_policy_id(created_policy):
    """Creates a policy and returns the ID"""
    return created_policy.json()['id']

# Tests
def test_create_policy_success(api_client):
    """Test successful creation of a policy with valid data"""
    response = api_client.post("/api/policies", json={"name": "Test Policy", "port": 7000, "action": "allow"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Policy"
    assert "id" in response.json()

def test_create_policy_missing_name(api_client):
    """Test that missing 'name' field results in 400 Bad Request"""
    response = api_client.post("/api/policies", json={"port": 7000, "action": "allow"})
    # Ensure that missing 'name' field results in 400 Bad Request
    assert response.status_code == 400
    assert "error" in response.json()

def test_create_policy_with_additional_fields(api_client, sample_policy):
    """Create policy with extra fields not defined in the schema, should be accepted"""
    policy_with_extras = {**sample_policy, "custom_field": "value", "priority": 10}
    response = api_client.post("/api/policies", json=policy_with_extras)
    assert response.status_code == 201
    assert response.json()["custom_field"] == "value"
    assert response.json()["priority"] == 10
    assert "id" in response.json()

def test_get_all_policies_empty(api_client):
    """Test getting all policies when none exist"""
    all_policies = api_client.get("/api/policies").json()
    for policy in all_policies:
        api_client.delete(f"/api/policies/{policy['id']}")
    # Now test getting all policies when none exist
    response = api_client.get("/api/policies")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_get_data_integrity(api_client, created_policy):
    """Test that retrieved policy data matches created policy data"""
    response = api_client.get("/api/policies")
    assert response.status_code == 200
    policies = response.json()
    assert len(policies) >= 1
    
    created_policy_data = created_policy.json()
    created_id = created_policy_data['id']
    
    # Find the created policy in the list
    matching_policy = next((p for p in policies if p["id"] == created_id), None)
    assert matching_policy is not None, f"Policy with ID {created_id} not found in list"
    
    # Verify data integrity for all fields
    assert matching_policy["name"] == created_policy_data["name"]
    assert matching_policy["port"] == created_policy_data["port"]
    assert matching_policy["action"] == created_policy_data["action"]
    assert matching_policy["source"] == created_policy_data["source"]
    assert matching_policy["destination"] == created_policy_data["destination"]

def test_update_policy_success(api_client, created_policy_id):
    """Test successful update of an existing policy"""
    update_data = {"action": "deny", "port": 9090}
    response = api_client.put(f"/api/policies/{created_policy_id}", json=update_data)
    # Verify update was successful
    assert response.status_code == 200
    assert response.json()["action"] == "deny"
    assert response.json()["port"] == 9090
    assert response.json()["id"] == created_policy_id

def test_update_policy_not_found(api_client):
    """Attempt to update a non-existent policy"""
    response = api_client.put("/api/policies/999", json={"action": "deny"})
    assert response.status_code == 404
    assert "error" in response.json()

def test_delete_policy_success(api_client, created_policy_id):
    """Test successful deletion of an existing policy"""
    response = api_client.delete(f"/api/policies/{created_policy_id}")
    assert response.status_code == 204
    
    # Verify the policy no longer exists
    get_response = api_client.get(f"/api/policies/{created_policy_id}")
    assert get_response.status_code == 404

def test_delete_policy_not_found(api_client):
    """Attempt to delete a non-existent policy"""
    response = api_client.delete("/api/policies/999")
    assert response.status_code == 404

def test_delete_policy_invalid_id(api_client):
    """Attempt to delete a policy with invalid ID format"""
    response = api_client.delete("/api/policies/-1")
    assert response.status_code == 404

def test_multiple_policies_unique_ids(api_client, sample_policy):
    """Test that multiple policies get unique IDs"""
    response1 = api_client.post("/api/policies", json={**sample_policy, "name": "Policy 1"})
    response2 = api_client.post("/api/policies", json={**sample_policy, "name": "Policy 2"})
    response3 = api_client.post("/api/policies", json={**sample_policy, "name": "Policy 3"})
    
    # Extract IDs
    id1 = response1.json()['id']
    id2 = response2.json()['id']
    id3 = response3.json()['id']
    
    # All IDs should be unique
    assert id1 != id2 != id3
    assert len({id1, id2, id3}) == 3

def test_delete_middle_policy_ids_persist(api_client, sample_policy):
    """Test that deleting a policy doesn't affect other IDs"""
    r1 = api_client.post("/api/policies", json={**sample_policy, "name": "Policy 1"})
    r2 = api_client.post("/api/policies", json={**sample_policy, "name": "Policy 2"})
    r3 = api_client.post("/api/policies", json={**sample_policy, "name": "Policy 3"})
    
    id1, id2, id3 = r1.json()['id'], r2.json()['id'], r3.json()['id']
    
    # Delete middle policy
    api_client.delete(f"/api/policies/{id2}")
    
    # Other policies should still be accessible by their original IDs
    assert api_client.get(f"/api/policies/{id1}").status_code == 200
    assert api_client.get(f"/api/policies/{id2}").status_code == 404  # Deleted
    assert api_client.get(f"/api/policies/{id3}").status_code == 200