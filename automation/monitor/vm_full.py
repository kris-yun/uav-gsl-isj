import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Kill everything first
ssh.exec_command('pkill -f gsl_actionserver_node; pkill -f vgr_sim_node; pkill -f gsl_benchmark_runner; sleep 1')

# Run with full output capture
cmd = """cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && \
timeout 25 ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py \
vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios \
config_id:=2,4-1_fast \
algorithm:=PMFS \
output_csv:=/tmp/gsl_baselines/smoke2.csv \
source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
start_x:=-0.55 start_y:=2.12 \
seed:=0 flight_height:=1.0 2>&1"""

print("Running with 25s timeout...")
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=35)
output = stdout.read().decode()
print(output[-4000:])
ssh.close()
