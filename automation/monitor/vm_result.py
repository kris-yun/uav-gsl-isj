import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    'cat /tmp/gsl_baselines/smoke_fixed.csv 2>/dev/null',
    'ls -la /tmp/gsl_baselines/ 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:60]} ===')
    print(out[:1000] if out else '(empty)')
    print()
ssh.close()
