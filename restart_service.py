"""Restart Nexus web service on Contabo."""
import paramiko
import time

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
        print(out[:1000])
    if err:
        print(f"ERR: {err[:200]}")
    return out

print("=== Killing old screen ===")
run("screen -S nexus -X quit 2>&1; sleep 1; echo killed")

print("=== Starting new screen session ===")
cmd = 'screen -dmS nexus bash -c "cd /root/nexus && python3 main.py"'
run(cmd)
time.sleep(2)

print("=== Verify process ===")
run("ps aux | grep 'python3 main.py' | grep -v grep || echo NOT_RUNNING")

print("=== Verify web response ===")
run("curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:8080/ 2>&1 || echo FAIL")

client.close()
print("\n=== RESTART DONE ===")
