import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.111.128", username="zyc", password="123456")

# Check running processes
cmds = [
    "ps aux | grep -E 'ros2|gsl|vgr|gmrf' | grep -v grep",
    "ls -la /dev/shm/ | head -20",
    "df -h /dev/shm",
]

for cmd in cmds:
    print(f">>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    if err:
        print(f"STDERR: {err}")
    print()

ssh.close()
