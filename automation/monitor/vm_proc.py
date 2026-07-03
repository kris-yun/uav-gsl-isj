import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "ros2|gsl_|vgr_" | grep -v grep')
print(stdout.read().decode())
ssh.close()
