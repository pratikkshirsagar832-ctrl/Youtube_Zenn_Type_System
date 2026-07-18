"""Check status of recent projects."""
import paramiko

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out[:1500])
    if err:
        print(f"ERR: {err[:200]}")

for pid in ["f7e2face650e", "784859b6edf5", "1c94d053f66c", "25cc7dc87457"]:
    print(f"\n=== {pid} ===")
    run(f"cat /root/nexus/projects/{pid}/status.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f\"status={d.get(\\\"status\\\",\\\"?\\\")} stage={d.get(\\\"current_stage\\\",\\\"?\\\")} progress={d.get(\\\"progress\\\",\\\"?\\\")}\"); print(f\"topic={d.get(\\\"topic\\\",\\\"?\\\")}\")' 2>&1")

client.close()
