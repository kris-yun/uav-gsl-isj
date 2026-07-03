import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    'ls -la /tmp/gsl_baselines/ 2>/dev/null',
    'cat /tmp/gsl_baselines/House01_PMFS_s0.csv 2>/dev/null | head -5',
    'ps aux | grep -E "gsl_|vgr_|ros2" | grep -v grep | head -10',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f'=== {cmd[:60]} ===')
    print(out[:500] if out else '(empty)')
    if err: print(f'ERR: {err[:200]}')
    print()
ssh.close()
