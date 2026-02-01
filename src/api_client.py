import requests

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def authenticate(self, username, password):
        """Authenticate and store token if successful"""
        response = requests.post(
            f"{self.base_url}/api/authenticate",
            json={'username': username, 'password': password}
        )
        if response.status_code == 200 and response.json().get('token'):
            self.token = response.json()['token']
        return response

    def get(self, endpoint):
        """Make GET request"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
        return response

    def post(self, endpoint, json=None):
        """Make POST request"""
        headers = self._get_headers()
        response = requests.post(f"{self.base_url}{endpoint}", json=json, headers=headers)
        return response
    
    def put(self, endpoint, json=None):
        """Make PUT request"""
        headers = self._get_headers()
        response = requests.put(f"{self.base_url}{endpoint}", json=json, headers=headers)
        return response
    
    def delete(self, endpoint):
        """Make DELETE request"""
        headers = self._get_headers()
        response = requests.delete(f"{self.base_url}{endpoint}", headers=headers)
        return response

    def _get_headers(self):
        """Build request headers with auth token if available"""
        headers = {}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        return headers