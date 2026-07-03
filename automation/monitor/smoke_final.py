import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Verify clean
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "gsl_|vgr_|ros2" | grep -v grep | wc -l')
count = stdout.read().decode().strip()
print(f"Existing ROS2 processes: {count}")

# Clean if needed
if int(count) > 0:
    ssh.exec_command('pkill -9 -f ros2; pkill -9 -f gsl_; pkill -9 -f vgr_; rm -rf /dev/shm/fastrtps_*; sleep 2')
    print("Cleaned")

# Smoke test: PMFS House01 seed 0
cmd = (
    "cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && "
    "timeout 90 ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py "
    "vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01 "
    "config_id:=2,4-1_fast algorithm:=PMFS "
    "output_csv:=/tmp/gsl_test.csv "
    "source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 "
    "start_x:=-0.55 start_y:=2.12 seed:=0 flight_height:=1.0 2>&1"
)

print("Smoke test: PMFS House01 s0...")
t0 = time.time()
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=100)
output = stdout.read().decode()
elapsed = time.time() - t0

# Extract key info
for line in output.split('\n'):
    if any(kw in line for kw in ['PMFS completed', 'Result saved', 'min_dist', 'Success', 'Error=', 'FOUND', 'timed']):
        print(f"  {line.strip()[-150:]}")

print(f"Elapsed: {elapsed:.0f}s")

# Check result
stdin2, stdout2, stderr2 = ssh.exec_command('cat /tmp/gsl_test.csv 2>/dev/null')
result = stdout2.read().decode().strip()
if result:
    print(f"\nResult:\n{result}")

# Cleanup
ssh.exec_command('pkill -9 -f ros2; pkill -9 -f gsl_; pkill -9 -f vgr_; rm -rf /dev/shm/fastrtps_*')
ssh.close()
