import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')
stdin, stdout, stderr = ssh.exec_command('cat ~/ros2_ws/src/vgr_bridge/vgr_bridge/gsl_benchmark_runner.py')
print(stdout.read().decode())
ssh.close()
