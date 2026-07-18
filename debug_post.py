import requests, json, sys, time

# Test POST to the API
try:
    r = requests.post("http://localhost:8080/api/generate",
        json={"input": "test123", "duration_minutes": 5, "niche": "dark_psychology"},
        timeout=30)
    print("STATUS:", r.status_code)
    print("BODY:", r.text[:500])
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200])
