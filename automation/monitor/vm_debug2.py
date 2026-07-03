import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Start the launch in background and capture output
cmd = """cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && \
timeout 30 ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py \
vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios \
config_id:=2,4-1_fast \
algorithm:=PMFS \
output_csv:=/tmp/gsl_baselines/smoke_debug.csv \
source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
start_x:=-0.55 start_y:=2.12 \
seed:=0 flight_height:=1.0 2>&1 | tail -100"""

print("Running launch with 30s timeout...")
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=45)
output = stdout.read().decode()
print(output[-3000:])
ssh.close()
