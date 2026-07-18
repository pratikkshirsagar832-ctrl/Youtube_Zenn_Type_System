import paramiko, time

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out[:2000])
    if err:
        print(f"ERR: {err[:300]}")

# Check if port 8080 is actually bound
print("=== CHECKING PORT 8080 ===")
run("ss -tlnp | grep 8080")

# Try curl with short timeout
print("\n=== CURL POST ===")
cmd = '''curl -s -X POST http://localhost:8080/api/generate -H "Content-Type: application/json" -d '{"input":"why humans fear the dark","duration_minutes":5,"niche":"dark_psychology"}' --max-time 30 2>&1'''
run(cmd)

client.close()
