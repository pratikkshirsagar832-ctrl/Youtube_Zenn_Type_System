"""Check projects directory on Contabo."""
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
        print(out[:1000])
    if err:
        print(f"ERR: {err[:200]}")

run("ls -la /root/nexus/projects/ 2>&1 | head -10")
print("---")
run("find /root/nexus/projects -name status.json 2>/dev/null | head -5")
print("---")
run("cat /root/nexus/projects/f7e2face650e/status.json 2>/dev/null | python3 -m json.tool 2>&1 | head -10")

client.close()
