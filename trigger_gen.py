import requests, json, sys
r = requests.post("http://localhost:8080/api/generate",
    json={"input": "why humans fear the dark", "duration_minutes": 5, "niche": "dark_psychology"},
    timeout=30)
print(r.status_code)
print(r.text)
