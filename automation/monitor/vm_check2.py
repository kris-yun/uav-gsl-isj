import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')
cmds = [
    'cat ~/ros2_ws/src/GSL/gsl_actions/action/DoGSL.action 2>/dev/null',
    'cat ~/ros2_ws/install/gsl_server/share/gsl_server/config/ 2>/dev/null || ls ~/ros2_ws/install/gsl_server/share/gsl_server/ 2>/dev/null',
    'ls ~/ros2_ws/src/GSL/gsl_server/src/algorithms/ 2>/dev/null',
    'cat ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_gsl_pmfs.launch.py 2>/dev/null',
    'ls ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/ 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f'=== {cmd[:80]} ===')
    print(out[:1000] if out else '(empty)')
    if err:
        print(f'ERR: {err[:200]}')
    print()
ssh.close()
