"""Trigger video pipeline from within Contabo."""
import paramiko

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd: str):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out[:3000])
    if err:
        print(f"ERR: {err[:300]}")

# Trigger generation using Python from the server
script = (
    "import requests, json, sys, time; "
    "r = requests.post('http://localhost:8080/api/generate', "
    "json={'input': 'why humans fear the dark', 'duration_minutes': 5, 'niche': 'dark_psychology'}, "
    "timeout=30); "
    "print(f'STATUS: {r.status_code}'); "
    "print(f'BODY: {r.text}'); "
)

print("=== TRIGGERING GENERATION ===")
run("python3 -c \"" + script.replace("'", "'\\''") + "\" 2>&1")

client.close()
