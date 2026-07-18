"""Deploy to Contabo: git pull, verify, restart, test."""
import paramiko
import sys

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

# Check processes and services
print("=== NEXUS PROCESSES ===")
run("ps aux | grep -i nexus | grep -v grep")

print("\n=== NODE/NPM ===")
run("node -v && npm -v")

print("\n=== CHROME ===")
run("which chromium-browser || which google-chrome-stable || which chromium || echo NO_CHROME")

print("\n=== CONFIG CHECK ===")
run("cd /root/nexus && python3 -c 'import config; print(\"config OK\"); print(config.REMOTION_PROJECT_PATH)'")

print("\n=== WEB SERVICE ===")
run("systemctl list-units --type=service --state=running | grep -i nexus || echo NO_SERVICE")
run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/ || echo NO_WEB")

print("\n=== REMOTION NPX CHECK ===")
run("cd /root/nexus/remotion-composer && npx --yes remotion --version 2>&1 | tail -3")

client.close()
print("\n=== DONE ===")
