"""Check latest project status on Contabo."""
import paramiko, json

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

stdin, stdout, stderr = client.exec_command("ls -1t /root/nexus/projects/ | head -5", timeout=10)
pids = stdout.read().decode().strip().split("\n")
print("Recent projects:", pids)

for pid in pids[:3]:
    pid = pid.strip()
    if not pid:
        continue
    stdin, stdout, stderr = client.exec_command("cat /root/nexus/projects/" + pid + "/status.json", timeout=10)
    data = stdout.read().decode().strip()
    if data:
        try:
            d = json.loads(data)
            print(f"\n{pid}:")
            print(f"  status={d.get('status')}  stage={d.get('current_stage')}  progress={d.get('progress')}")
            print(f"  topic={d.get('topic','')[:60]}")
            err = d.get("error", "")
            if err:
                print(f"  error={err[:200]}")
        except:
            print(f"  (invalid json)")

client.close()
