import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.111.128", username="zyc", password="123456")

cmds = [
    "pkill -9 -f ros2",
    "pkill -9 -f gsl",
    "pkill -9 -f vgr",
    "pkill -9 -f pioe",
    "pkill -9 -f gmrf",
    "sleep 2",
    "rm -rf /dev/shm/fastrtps_*",
    "rm -rf /tmp/round6_results",
    "mkdir -p /tmp/round6_results",
    "ps aux | grep -E 'ros2|gsl|vgr|gmrf' | grep -v grep | wc -l",
]

for cmd in cmds:
    print(f">>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(f"  {out}")
    if err:
        print(f"  STDERR: {err}")

ssh.close()
print("\nVM cleaned.")
