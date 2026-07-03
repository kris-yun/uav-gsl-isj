import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

cmds = [
    # Kill old leftover processes
    'pkill -f gsl_benchmark_runner 2>/dev/null; pkill -f gsl_actionserver_node 2>/dev/null; pkill -f vgr_sim_node 2>/dev/null; sleep 1; echo "cleaned"',
    # Check if ROS2 daemon is running
    'ros2 daemon status 2>/dev/null',
    # Check available topics after cleanup
    'source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && ros2 topic list 2>/dev/null',
    # Check GADEN data path
    'ls /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/gas_simulations/2,4-1_fast/ 2>/dev/null | head -5',
    # Check wind data
    'ls /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/wind_simulations/2,4-1_fast/ 2>/dev/null | head -5',
    # Check occupancy grid
    'head -5 /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/OccupancyGrid3D.csv 2>/dev/null',
    # Check gsl_server config
    'ls ~/ros2_ws/install/gsl_server/share/gsl_server/config/ 2>/dev/null',
    'cat ~/ros2_ws/install/gsl_server/share/gsl_server/config/*.yaml 2>/dev/null | head -30',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f'=== {cmd[:70]} ===')
    print(out[:500] if out else '(empty)')
    if err and 'deprecation' not in err.lower():
        print(f'ERR: {err[:200]}')
    print()
ssh.close()
