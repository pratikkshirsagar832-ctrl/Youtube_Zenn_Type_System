"""Check .env and test pipeline on Contabo."""
import paramiko

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
        print(out)
    if err:
        print(f"ERR: {err}")
    return out

print("=== ENV CONFIG ===")
run("cd /root/nexus && python3 -c 'import config; print(f\"DEEPSEEK: {bool(config.DEEPSEEK_API_KEY)}\"); print(f\"GROQ: {bool(config.GROQ_API_KEY)}\"); print(f\"PIPER: {config.PIPER_MODEL_PATH}\"); print(f\"CHROME: {config.CHROME_EXECUTABLE}\"); print(f\"READY: {config.is_fully_configured()}\")'")

print("\n=== TESTING DEEPSEEK CONNECTION ===")
run("cd /root/nexus && python3 -c 'import asyncio; from tools.deepseek_client import run_research; r = asyncio.run(run_research(\"why humans fear the dark\", \"dark_psychology\")); print(f\"OK | topic={r.get(\\\"topic\",\\\"?\\\")}\")' 2>&1")

client.close()
