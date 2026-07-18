"""Debug POST timeout issue."""
import paramiko

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out[:1000])
    if err:
        print(f"ERR: {err[:200]}")

print("=== PROJECTS DIR ===")
run("python3 -c 'import config; print(config.PROJECTS_DIR); print(config.PROJECTS_DIR.exists())'")

print("\n=== SEND POST WITH 60s TIMEOUT ===")
# Use curl with background mode
run("timeout 60 curl -s -X POST http://localhost:8080/api/generate -H 'Content-Type: application/json' -d '{\"input\":\"test_fix\",\"duration_minutes\":5,\"niche\":\"dark_psychology\"}' 2>&1")

client.close()
