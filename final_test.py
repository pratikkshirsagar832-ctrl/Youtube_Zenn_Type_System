"""Pull, restart, and trigger test on Contabo."""
import paramiko, time

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
    if out: print(out[:1000])
    if err: print(f"ERR: {err[:200]}")

print("=== PULL ===")
run("cd /root/nexus && git pull 2>&1")

print("\n=== RESTART ===")
run("fuser -k 8080/tcp 2>&1; sleep 2")
run("screen -S nexus -X quit 2>&1; sleep 1")
run('screen -dmS nexus bash -c "cd /root/nexus && python3 main.py" 2>&1')
time.sleep(4)

print("\n=== VERIFY ===")
run("curl -s http://localhost:8080/api/health --max-time 5")

print("\n=== TRIGGER ===")
run("timeout 30 curl -s -X POST http://localhost:8080/api/generate -H 'Content-Type: application/json' -d '{\"input\":\"why humans fear the dark\",\"duration_minutes\":5,\"niche\":\"dark_psychology\"}' 2>&1")

client.close()
print("\nDONE")
