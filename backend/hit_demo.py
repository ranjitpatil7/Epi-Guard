from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
r1 = client.post('/api/v1/auth/login', data={'username': 'admin', 'password': 'password123'})
token = r1.json().get('access_token')
print('Token:', token is not None)
r2 = client.post('/api/v1/incidents/demo', headers={'Authorization': f'Bearer {token}'})
print(r2.status_code, r2.json())
