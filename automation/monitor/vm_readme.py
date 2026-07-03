import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    'cat ~/ros2_ws/src/GSL/README.md 2>/dev/null | head -100',
    # Check if there's a step limit or timeout config
    'grep -r "timeout\|max_step\|budget\|max_iter" ~/ros2_ws/src/GSL/gsl_server/src/ --include="*.h" -l 2>/dev/null',
    'grep -r "timeout\|max_step\|budget\|max_iter\|maxSeconds\|time_limit" ~/ros2_ws/src/GSL/gsl_server/src/ --include="*.cpp" --include="*.h" 2>/dev/null | head -20',
    # Check GSL action definition for budget field
    'cat ~/ros2_ws/src/GSL/gsl_actions/action/DoGSL.action',
    # Check benchmark runner timeout setting
    'grep -n "timeout" ~/ros2_ws/src/vgr_bridge/vgr_bridge/gsl_benchmark_runner.py 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:70]} ===')
    print(out[:1500] if out else '(empty)')
    print()
ssh.close()
