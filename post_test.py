import requests, sys
r = requests.post("http://localhost:8080/api/generate",
    json={"input": "why humans fear the dark", "duration_minutes": 5, "niche": "dark_psychology"},
    timeout=10)
print("OK", r.status_code)
print(r.text[:300])
