import requests
import json

url = "http://localhost:8001/auth/refresh"
headers = {"Content-Type": "application/json"}
data = {
    "refresh_token": "cc3a971d-f16b-4abf-bfa9-5cdef0447865",  
    "fingerprint": "kkkkkkkk"  
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")