import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Kill everything
ssh.exec_command('pkill -f gsl_actionserver_node; pkill -f vgr_sim_node; pkill -f gsl_benchmark_runner; sleep 1')

# Run with FIXED path - point to House01 directory directly
cmd = """cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && \
timeout 60 ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py \
vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01 \
config_id:=2,4-1_fast \
algorithm:=PMFS \
output_csv:=/tmp/gsl_baselines/smoke_fixed.csv \
source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
start_x:=-0.55 start_y:=2.12 \
seed:=0 flight_height:=1.0 2>&1"""

print("Running with FIXED path (60s timeout)...")
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=75)
output = stdout.read().decode()
print(output[-5000:])
ssh.close()
