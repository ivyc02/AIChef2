import requests
import json
import sys

def test_url(url, json_data=None):
    print(f"Testing {url}...")
    try:
        if json_data:
            response = requests.post(url, json=json_data, timeout=5)
        else:
            response = requests.get(url, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                print("Response:", json.dumps(response.json(), ensure_ascii=False)[:200])
            except:
                print("Response (text):", response.text[:200])
        else:
            print("Error Response:", response.text)
    except Exception as e:
        print(f"Connection Failed to {url}: {e}")

print("--- Health Check ---")
test_url("http://127.0.0.1:8000/")

print("\n--- Search Check ---")
test_url("http://127.0.0.1:8000/api/search", {"query": "test", "limit": 1})
