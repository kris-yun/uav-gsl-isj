import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Get the launch file path
stdin, stdout, stderr = ssh.exec_command('find ~/ros2_ws -name "vgr_gsl_benchmark.launch.py" 2>/dev/null')
launch_path = stdout.read().decode().strip()
print(f"Launch file: {launch_path}")

# Read current content
stdin, stdout, stderr = ssh.exec_command(f'cat {launch_path}')
content = stdout.read().decode()

# Check if it already has maxSearchTime
if 'maxSearchTime' in content:
    print("Already has maxSearchTime")
else:
    # Add GSL server parameters to the launch file
    # Find the gsl_server node and add parameters
    old_server = """        Node(
            package='gsl_server',
            executable='gsl_actionserver_node',
            name='gsl_server',
            output='screen',
            parameters=[{
                'use_sim_time': False,
            }],
        ),"""
    
    new_server = """        # GSL server with configurable parameters
        Node(
            package='gsl_server',
            executable='gsl_actionserver_node',
            name='gsl_server',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'maxSearchTime': 300.0,
                'distanceThreshold': 0.5,
                'ground_truth_x': LaunchConfiguration('source_x'),
                'ground_truth_y': LaunchConfiguration('source_y'),
            }],
        ),"""
    
    content = content.replace(old_server, new_server)
    
    # Write back
    sftp = ssh.open_sftp()
    with sftp.open(launch_path, 'w') as f:
        f.write(content)
    sftp.close()
    print("Launch file updated with GSL server parameters")
    
    # Rebuild vgr_bridge
    stdin, stdout, stderr = ssh.exec_command('cd ~/ros2_ws && source /opt/ros/humble/setup.bash && colcon build --packages-select vgr_bridge --symlink-install 2>&1 | tail -5')
    print(stdout.read().decode()[-500:])

ssh.close()
