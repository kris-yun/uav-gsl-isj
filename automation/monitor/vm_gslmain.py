import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    # Find the main GSL server file
    'find ~/ros2_ws/src/GSL/gsl_server/src -name "GSLServer*" -o -name "gsl_server*" | grep -v aux | head -5',
    # Check for maxSteps in the source
    'grep -rn "maxSteps\|maxStep\|max_step\|stepLimit\|step_limit\|maxIterations" ~/ros2_ws/src/GSL/gsl_server/src/ --include="*.cpp" --include="*.h" 2>/dev/null | head -20',
    # Check how PMFS decides to stop
    'grep -rn "declareSuccess\|declare_source\|FOUND\|found_source\|RESULT\|result" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/ --include="*.cpp" --include="*.h" 2>/dev/null | head -20',
    # Check common GSL parameters
    'grep -rn "declare_parameter" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/ --include="*.cpp" 2>/dev/null | head -30',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:65]} ===')
    print(out[:1000] if out else '(empty)')
    print()
ssh.close()
