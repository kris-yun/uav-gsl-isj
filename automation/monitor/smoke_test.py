import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')

# Upload the runner script
sftp = ssh.open_sftp()
with sftp.open('/tmp/run_baseline.sh', 'w') as f:
    with open('D:/ZYC/A-gas/experiments/official_baselines/run_baseline.sh') as lf:
        f.write(lf.read())
sftp.close()

# Make executable
ssh.exec_command('chmod +x /tmp/run_baseline.sh')

# Create output dir
ssh.exec_command('mkdir -p /tmp/gsl_baselines')

# Run smoke test: PMFS on House01, seed 0
cmd = """cd ~/ros2_ws && bash /tmp/run_baseline.sh \
House01 PMFS \
-0.55 2.12 \
-0.4 -2.9 -0.3 \
2,4-1_fast \
0 \
/tmp/gsl_baselines/House01_PMFS_s0.csv 2>&1"""

print("Starting smoke test: PMFS on House01, seed 0...")
print(f"CMD: {cmd[:200]}...")
t0 = time.time()

stdin, stdout, stderr = ssh.exec_command(cmd, timeout=240)
output = stdout.read().decode()
elapsed = time.time() - t0

print(f"\nElapsed: {elapsed:.0f}s")
print(f"Output (last 1500 chars):")
print(output[-1500:])

# Check if result exists
stdin2, stdout2, stderr2 = ssh.exec_command('ls -la /tmp/gsl_baselines/House01_PMFS_s0.csv 2>/dev/null')
print(f"\nFile check: {stdout2.read().decode().strip()}")

ssh.close()
