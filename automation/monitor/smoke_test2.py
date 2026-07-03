import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Upload runner script with utf-8 encoding
sftp = ssh.open_sftp()
with sftp.open('/tmp/run_baseline.sh', 'w') as f:
    with open('D:/ZYC/A-gas/experiments/official_baselines/run_baseline.sh', encoding='utf-8') as lf:
        f.write(lf.read())
sftp.close()
ssh.exec_command('chmod +x /tmp/run_baseline.sh')
ssh.exec_command('mkdir -p /tmp/gsl_baselines')

# Run smoke test: PMFS on House01, seed 0
cmd = """cd ~/ros2_ws && source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash && \
ros2 launch vgr_bridge vgr_gsl_benchmark.launch.py \
vgr_data_path:=/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios \
config_id:=2,4-1_fast \
algorithm:=PMFS \
output_csv:=/tmp/gsl_baselines/House01_PMFS_s0.csv \
source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
start_x:=-0.55 start_y:=2.12 \
seed:=0 flight_height:=1.0 &
sleep 90 && ls -la /tmp/gsl_baselines/House01_PMFS_s0.csv 2>/dev/null && echo DONE"""

print("Starting smoke test: PMFS on House01, seed 0...")
t0 = time.time()
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
output = stdout.read().decode()
elapsed = time.time() - t0
print(f"Elapsed: {elapsed:.0f}s")
print(output[-1500:])
ssh.close()
