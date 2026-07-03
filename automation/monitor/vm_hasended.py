import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    # Find HasEnded implementation
    'grep -rn "HasEnded\|hasEnded\|has_ended\|ended" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/ --include="*.cpp" --include="*.h" 2>/dev/null | head -20',
    # Find the Algorithm base class
    'find ~/ros2_ws/src/GSL/gsl_server/src -name "Algorithm*" -o -name "algorithm*" 2>/dev/null',
    # Check GrGSL termination
    'grep -rn "HasEnded\|declareSuccess\|finish\|end_search" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/GrGSL/ --include="*.cpp" --include="*.h" 2>/dev/null | head -10',
    # Check common base
    'grep -rn "HasEnded\|ended\|result" ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/Common/ --include="*.cpp" --include="*.h" 2>/dev/null | head -20',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:65]} ===')
    print(out[:1500] if out else '(empty)')
    print()
ssh.close()
