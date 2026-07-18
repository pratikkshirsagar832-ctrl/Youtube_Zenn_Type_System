"""Kill all stale Python/uvicorn processes and restart Nexus cleanly."""
import paramiko
import time

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd: str, timeout_sec=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout_sec)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out[:2000])
    if err:
        print(f"ERR: {err[:300]}")
    return out

# Kill ALL python processes on port 8080
print("=== KILLING ALL ON 8080 ===")
run("fuser -k 8080/tcp 2>&1; sleep 2; echo DONE")

# Verify port is free
print("\n=== VERIFY PORT FREE ===")
run("ss -tlnp | grep 8080 || echo PORT_FREE")

# Kill old screen sessions
print("\n=== KILL OLD SCREENS ===")
run("screen -ls 2>&1 | grep nexus | awk '{print $1}' | xargs -I{} screen -S {} -X quit 2>&1; sleep 1; echo SCREENS_KILLED")

# Start fresh
print("\n=== STARTING FRESH ===")
run('screen -dmS nexus bash -c "cd /root/nexus && python3 main.py" 2>&1')
time.sleep(4)

# Verify
print("\n=== VERIFY ===")
run("ps aux | grep 'python3 main' | grep -v grep")
run("curl -s http://localhost:8080/api/health --max-time 5")

# Test POST
print("\n=== TEST POST ===")
run("curl -s -X POST http://localhost:8080/api/generate -H 'Content-Type: application/json' -d '{\"input\":\"why humans fear the dark\",\"duration_minutes\":5,\"niche\":\"dark_psychology\"}' --max-time 15 2>&1")

client.close()
print("\nDONE")
