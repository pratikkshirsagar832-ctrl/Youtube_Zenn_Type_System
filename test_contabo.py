"""Run end-to-end pipeline test on Contabo."""
import paramiko
import sys

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

def run(cmd: str, timeout_sec: int = 60) -> str:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout_sec)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"ERR: {err}")
    return out

print("=== Running test_end_to_end.py ===")
run("cd /root/nexus && python3 test_end_to_end.py 2>&1", timeout_sec=120)

client.close()
print("\n=== TEST DONE ===")
