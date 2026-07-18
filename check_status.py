import requests, json, sys, time

project_id = sys.argv[1] if len(sys.argv) > 1 else "f7e2face650e"

r = requests.get(f"http://localhost:8080/api/status/{project_id}", timeout=10)
data = r.json()
print(json.dumps(data, indent=2))
