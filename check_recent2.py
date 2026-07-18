import paramiko, json

HOST = "85.239.237.53"
USER = "root"
PASS = "Lu7chLT38HSbcNndP7WA"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, look_for_keys=False, allow_agent=False, timeout=20)

pids = ["f7e2face650e", "784859b6edf5", "1c94d053f66c", "25cc7dc87457"]
for pid in pids:
    stdin, stdout, stderr = client.exec_command("cat /root/nexus/projects/" + pid + "/status.json 2>/dev/null", timeout=10)
    data = stdout.read().decode().strip()
    if data:
        try:
            d = json.loads(data)
            print(f"{pid}: status={d.get('status','?')} stage={d.get('current_stage','?')} topic={d.get('topic','?')[:40]}")
        except Exception as e:
            print(f"{pid}: parse error {e}")
    else:
        print(f"{pid}: not found")

client.close()
