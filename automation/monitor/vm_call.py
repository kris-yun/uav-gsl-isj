import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    'cat ~/ros2_ws/src/GSL/gsl_server/src/aux_nodes/gsl_server_call.cpp',
    # Check how PMFS handles steps/termination
    'find ~/ros2_ws/src/GSL/gsl_server/src -path "*PMFS*" -name "*.cpp" 2>/dev/null | head -5',
    # Check GSL server main file for parameter declarations
    'grep -n "declare_parameter\|get_parameter\|maxSteps\|maxSteps\|maxTime\|budget" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/GSLServer.cpp 2>/dev/null | head -20',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:65]} ===')
    print(out[:2000] if out else '(empty)')
    print()
ssh.close()
