import subprocess, sys
SSH = r"C:\Windows\System32\OpenSSH\ssh.exe"
HOST = "zyc@192.168.111.128"
timeout = int(sys.argv[1])
cmd = sys.argv[2]
r = subprocess.run([SSH, "-o", "StrictHostKeyChecking=no", "-o", "ControlMaster=no", "-o", "ConnectTimeout=10", HOST, cmd], capture_output=True, timeout=timeout, errors='replace')
try:
    print(r.stdout[-2000:] if len(r.stdout) > 2000 else r.stdout)
except:
    pass
try:
    if r.stderr: print("STDERR:", r.stderr[-500:])
except:
    pass
