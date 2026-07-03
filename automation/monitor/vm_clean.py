import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Kill everything aggressively
cmds = [
    'pkill -9 -f gsl_benchmark_runner',
    'pkill -9 -f gsl_actionserver_node',
    'pkill -9 -f vgr_sim_node',
    'pkill -9 -f ros2.launch',
    'pkill -9 -f vgr_gsl',
    'sleep 2',
    'ps aux | grep -E "gsl_|vgr_|ros2" | grep -v grep | wc -l',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    if out: print(f'{cmd[:40]} -> {out}')

# Verify clean
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "gsl_|vgr_" | grep -v grep')
remaining = stdout.read().decode().strip()
print(f'\nRemaining processes:\n{remaining if remaining else "(none)"}')
ssh.close()
