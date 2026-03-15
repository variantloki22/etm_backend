import requests

url = "http://localhost:8000/api/etm/transactions/"
data = {
    "category": "Adult",
    "ticket_count": 2,
    "latitude": 12.9716,
    "longitude": 77.5946,
    "route": "335E",
    "timestamp": "2026-03-15T15:00:00Z"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
