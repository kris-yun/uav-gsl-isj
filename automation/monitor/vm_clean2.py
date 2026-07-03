import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    # Kill ALL ros2 related processes
    'pkill -9 -f ros2',
    'pkill -9 -f gsl_',
    'pkill -9 -f vgr_',
    'pkill -9 -f ros2cli',
    'sleep 2',
    # Kill ros2 daemon
    'ros2 daemon stop 2>/dev/null',
    'sleep 1',
    # Clean shared memory
    'rm -rf /dev/shm/fastrtps_* 2>/dev/null',
    'rm -rf /tmp/robotics_* 2>/dev/null',
    # Verify clean
    'ps aux | grep -E "gsl_|vgr_|ros2" | grep -v grep | wc -l',
    # Restart daemon
    'ros2 daemon start 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    if out: print(f'{cmd[:40]} -> {out}')

print("\nVM cleaned")
ssh.close()
