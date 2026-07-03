import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Kill any existing processes
ssh.exec_command('pkill -9 -f gsl_actionserver_node; pkill -9 -f vgr_sim_node; pkill -9 -f gsl_benchmark_runner; sleep 2')

# Run PMFS with new parameters
cmd = (
    "cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && "
    "timeout 120 ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py "
    "vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01 "
    "config_id:=2,4-1_fast algorithm:=PMFS "
    "output_csv:=/tmp/gsl_test_pmfs.csv "
    "source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 "
    "start_x:=-0.55 start_y:=2.12 seed:=0 flight_height:=1.0 2>&1"
)

t0 = time.time()
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=130)
output = stdout.read().decode()
elapsed = time.time() - t0

# Show key lines
for line in output.split('\n'):
    if any(kw in line for kw in ['PMFS', 'source', 'Success', 'RESULT', 'Error', 'saved', 'min_dist', 'GAS', 'WIND', 'maxSearch']):
        print(line.strip()[-200:])

print(f"\nElapsed: {elapsed:.0f}s")

# Check result
stdin2, stdout2, stderr2 = ssh.exec_command('cat /tmp/gsl_test_pmfs.csv 2>/dev/null')
result = stdout2.read().decode().strip()
if result:
    print(f"\nResult CSV:\n{result}")

# Cleanup
ssh.exec_command('pkill -9 -f gsl_actionserver_node; pkill -9 -f vgr_sim_node; pkill -9 -f gsl_benchmark_runner')
ssh.close()
