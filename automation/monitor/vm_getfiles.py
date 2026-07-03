import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')
cmds = [
    'cat ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_gsl_pmfs.launch.py',
    'cat ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_gsl_benchmark.launch.py',
    'cat ~/ros2_ws/src/vgr_bridge/vgr_bridge/vgr_sim_node.py 2>/dev/null || find ~/ros2_ws -name vgr_sim_node.py 2>/dev/null | head -3',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    print(f'=== {cmd[:60]} ===')
    print(out[:2000] if out else '(empty)')
    print()
ssh.close()
