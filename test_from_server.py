"""Check server logs and try to generate a test video via the Python requests from SERVER side."""
import paramiko

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd: str) -> str:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out[:2000])
    if err:
        print(f"ERR: {err[:300]}")
    return out

# Check current processes
print("=== PROCESSES ===")
run("ps aux | grep -E 'screen|python3|main.py' | grep -v grep")

# Hit the local API from the server itself
print("\n=== LOCAL API CALL (from server) ===")
run("curl -s -X POST http://localhost:8080/api/generate -H 'Content-Type: application/json' -d '{\"input\":\"why humans fear the dark\",\"duration_minutes\":5,\"niche\":\"dark_psychology\"}' --max-time 10 2>&1")

# Check if there's a project already created
print("\n=== PROJECTS ===")
run("curl -s http://localhost:8080/api/projects --max-time 5 2>&1 | python3 -m json.tool 2>&1 | head -20")

client.close()
