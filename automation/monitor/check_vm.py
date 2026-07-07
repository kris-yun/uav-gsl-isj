import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc', password='123456')
cmds = [
    'ls ~/ros2_ws/install/ 2>/dev/null | head -20',
    'ls ~/ros2_ws/src/ 2>/dev/null | head -20',
    'source /opt/ros/humble/setup.bash && ros2 pkg list 2>/dev/null | grep -i gsl',
    'find ~/ros2_ws -name gsl_actionserver_node 2>/dev/null',
    'ls /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/ 2>/dev/null',
    'ls /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/gas_simulations/ 2>/dev/null',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f'CMD: {cmd[:80]}')
    print(f'  OUT: {out[:300] if out else "(empty)"}')
    if err:
        print(f'  ERR: {err[:200]}')
    print()
ssh.close()
