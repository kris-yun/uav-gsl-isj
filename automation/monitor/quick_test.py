import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

vgr_path = "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01"
cmd = (f"cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && "
       f"timeout 120 ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py "
       f"vgr_data_path:={vgr_path} "
       f"config_id:=2,4-1_fast "
       f"algorithm:=PMFS "
       f"output_csv:=/tmp/gsl_baselines/House01_PMFS_s0.csv "
       f"source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 "
       f"start_x:=-0.55 start_y:=2.12 "
       f"seed:=0 flight_height:=1.0 2>&1")

t0 = time.time()
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=140)
output = stdout.read().decode()
elapsed = time.time() - t0

# Check result
stdin2, stdout2, stderr2 = ssh.exec_command('cat /tmp/gsl_baselines/House01_PMFS_s0.csv 2>/dev/null')
result = stdout2.read().decode().strip()

print(f"Elapsed: {elapsed:.0f}s")
print(f"Result: {result[-300:]}")

# Cleanup
ssh.exec_command('pkill -9 -f gsl_actionserver_node; pkill -9 -f vgr_sim_node; pkill -9 -f gsl_benchmark_runner')
ssh.close()
