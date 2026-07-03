import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    # GSL server main - how it handles goals
    'cat ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/gsl_server.cpp',
    # PMFS state machine - how it decides to stop
    'find ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS -name "*.cpp" -o -name "*.h" 2>/dev/null',
    # How does PMFS declare success?
    'grep -rn "declareSuccess\|succeeded\|finish\|end\|STOP\|MovingState\|StopAndMeasure" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/ --include="*.cpp" --include="*.h" 2>/dev/null | head -20',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:65]} ===')
    print(out[:2000] if out else '(empty)')
    print()
ssh.close()
