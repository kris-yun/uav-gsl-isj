import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')
cmds = [
    # Full benchmark launch file
    'cat ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_gsl_benchmark.launch.py',
    # Check available algorithms in GSL server
    'grep -r "PMFS\|GrGSL\|surge_cast\|spiral\|particle_filter" ~/ros2_ws/src/GSL/ --include="*.cpp" -l 2>/dev/null | head -10',
    # Check GSL server main for algorithm dispatch
    'grep -r "gsl_method\|algorithm\|PMFS\|GrGSL\|surge" ~/ros2_ws/src/GSL/gsl_server/src/ --include="*.cpp" -l 2>/dev/null | head -5',
    # Check if GADEN Python is available on VM
    'python3 -c "import gadentools; print(gadentools.__file__)" 2>/dev/null || echo "gadentools not found"',
    # Check vgr_sim_node installed
    'which vgr_sim_node 2>/dev/null || find ~/ros2_ws/install/vgr_bridge -name vgr_sim_node 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:80]} ===')
    print(out[:2000] if out else '(empty)')
    print()
ssh.close()
