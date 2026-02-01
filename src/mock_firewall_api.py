from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import secrets
import threading

app = Flask(__name__)

# Mock data for policies with ID tracking
policies = {}
next_policy_id = 1
id_lock = threading.Lock()  # Add lock for thread-safe ID generation
policies_lock = threading.Lock()  # Lock for policies dict
active_tokens = {}
tokens_lock = threading.Lock()  # Lock for tokens dict

def verify_token():
    """Verify the Authorization header contains valid token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ')[1]
    
    with tokens_lock:
        # Check if token exists and is not expired
        if token in active_tokens:
            if active_tokens[token]['expires'] > datetime.now():
                return True
            else:
                # Token expired, remove it
                del active_tokens[token]
    return False

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    if data and data.get('username') == 'admin' and data.get('password') == 'password':
        # Generate unique token for this session
        token = secrets.token_urlsafe(32)
        with tokens_lock:
            active_tokens[token] = {
                'username': data.get('username'),
                'expires': datetime.now() + timedelta(hours=1)
            }
        return jsonify({'token': token}), 200
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/policies', methods=['GET'])
def get_policies():
    if not verify_token():
        return jsonify({'error': 'Unauthorized'}), 401
    with policies_lock:
        return jsonify(list(policies.values())), 200

@app.route('/api/policies', methods=['POST'])
def create_policy():
    global next_policy_id
    if not verify_token():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Bad Request'}), 400
    
    # Thread-safe ID generation
    with id_lock:
        policy_id = next_policy_id
        next_policy_id += 1
    
    policy = {'id': policy_id, **data}
    
    with policies_lock:
        policies[policy_id] = policy
    
    return jsonify(policy), 201

@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def get_policy(policy_id):
    if not verify_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    with policies_lock:
        if policy_id not in policies:
            return jsonify({'error': 'Not Found'}), 404
        return jsonify(policies[policy_id]), 200

@app.route('/api/policies/<int:policy_id>', methods=['PUT'])
def update_policy(policy_id):
    if not verify_token():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    
    with policies_lock:
        if policy_id not in policies:
            return jsonify({'error': 'Not Found'}), 404
        
        # Update existing policy, preserve ID
        policies[policy_id].update(data)
        policies[policy_id]['id'] = policy_id
        return jsonify(policies[policy_id]), 200

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    if not verify_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    with policies_lock:
        if policy_id not in policies:
            return jsonify({'error': 'Not Found'}), 404
        del policies[policy_id]
    
    return jsonify({'message': 'Deleted'}), 204

if __name__ == '__main__':
    # Enable threading for Flask development server
    app.run(debug=True, threaded=True)