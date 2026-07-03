import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    # Look for evaluation/benchmark scripts in MAPIRlab repo
    'find ~/ros2_ws/src/GSL -name "*.py" -o -name "*.sh" 2>/dev/null | head -20',
    'find ~/ros2_ws/src/GSL -name "*eval*" -o -name "*bench*" -o -name "*test*" -o -name "*launch*" 2>/dev/null | head -20',
    # Check if there's a launch directory
    'ls ~/ros2_ws/src/GSL/gsl_server/launch/ 2>/dev/null',
    'ls ~/ros2_ws/src/GSL/gsl_server/config/ 2>/dev/null',
    # Check the gsl_server_call example
    'find ~/ros2_ws/src/GSL -name "gsl_server_call*" 2>/dev/null',
    # Check how the GSL server handles the algorithm - what config/params it reads
    'grep -r "PMFS\|grgsl\|surge" ~/ros2_ws/src/GSL/gsl_server/src/ --include="*.cpp" -l 2>/dev/null',
    # Check if there's a config YAML the server reads
    'find ~/ros2_ws/install/gsl_server -name "*.yaml" -o -name "*.yml" 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:65]} ===')
    print(out[:500] if out else '(empty)')
    print()
ssh.close()
