import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Write a new launch file with GSL server parameters
new_launch = r'''
"""Launch file for VGR GSL benchmark with GSL server parameters."""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('vgr_data_path', default_value=''),
        DeclareLaunchArgument('config_id', default_value='2,4-1_fast'),
        DeclareLaunchArgument('algorithm', default_value='PMFS'),
        DeclareLaunchArgument('output_csv', default_value='/tmp/gsl_result.csv'),
        DeclareLaunchArgument('source_x', default_value='-0.40'),
        DeclareLaunchArgument('source_y', default_value='-2.90'),
        DeclareLaunchArgument('source_z', default_value='-0.30'),
        DeclareLaunchArgument('start_x', default_value='-5.0'),
        DeclareLaunchArgument('start_y', default_value='-5.0'),
        DeclareLaunchArgument('seed', default_value='0'),
        DeclareLaunchArgument('budget_fraction', default_value='1.0'),
        DeclareLaunchArgument('flight_height', default_value='1.0'),

        # VGR UAV simulator
        Node(
            package='vgr_bridge',
            executable='vgr_sim_node',
            name='vgr_uav_sim',
            output='screen',
            parameters=[{
                'vgr_data_path': LaunchConfiguration('vgr_data_path'),
                'config_id': LaunchConfiguration('config_id'),
                'flight_height': LaunchConfiguration('flight_height'),
                'start_x': LaunchConfiguration('start_x'),
                'start_y': LaunchConfiguration('start_y'),
            }],
        ),

        # GSL server with proper parameters
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
        ),

        # Benchmark runner (delayed start)
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='vgr_bridge',
                    executable='gsl_benchmark_runner',
                    name='gsl_benchmark_runner',
                    output='screen',
                    parameters=[{
                        'algorithm': LaunchConfiguration('algorithm'),
                        'output_csv': LaunchConfiguration('output_csv'),
                        'source_x': LaunchConfiguration('source_x'),
                        'source_y': LaunchConfiguration('source_y'),
                        'source_z': LaunchConfiguration('source_z'),
                        'seed': LaunchConfiguration('seed'),
                        'budget_fraction': LaunchConfiguration('budget_fraction'),
                        'config_id': LaunchConfiguration('config_id'),
                        'timeout_sec': 360.0,
                    }],
                ),
            ],
        ),
    ])
'''

# Write the file using echo
import pipes
escaped = new_launch.replace("'", "'\\''")
cmd = f"cat > ~/ros2_ws/src/vgr_bridge/launch/vgr_gsl_benchmark.launch.py << 'LAUNCH_EOF'\n{new_launch}\nLAUNCH_EOF"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.read()
stderr_out = stderr.read().decode()
if stderr_out:
    print(f"Write err: {stderr_out[:200]}")
else:
    print("Launch file written")

# Also copy to build and install dirs
copy_cmds = [
    f"cp ~/ros2_ws/src/vgr_bridge/launch/vgr_gsl_benchmark.launch.py ~/ros2_ws/build/vgr_bridge/launch/",
    f"cp ~/ros2_ws/src/vgr_bridge/launch/vgr_gsl_benchmark.launch.py ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/",
]
for c in copy_cmds:
    ssh.exec_command(c)

# Rebuild
stdin, stdout, stderr = ssh.exec_command('cd ~/ros2_ws && source /opt/ros/humble/setup.bash && colcon build --packages-select vgr_bridge --symlink-install 2>&1 | tail -5')
print(stdout.read().decode()[-500:])

ssh.close()
