"""Step 1: Upload vgr_bridge package to VM via paramiko SSH."""
import paramiko
import os
import sys

VM_IP = "192.168.111.128"
VM_USER = "zyc"
VM_PASS = "123456"

LOCAL_BRIDGE = os.path.join(
    r"D:\ZYC\A-gas\workspace\rearch\gsl_budgeted_declaration\scripts\vgr_bridge"
)

VM_WS = "/home/zyc/ros2_ws/src"
VM_BRIDGE = f"{VM_WS}/vgr_bridge"


def ssh_cmd(ssh, cmd, timeout=60):
    """Run command and return (exit_code, stdout, stderr)."""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    return exit_code, stdout.read().decode(), stderr.read().decode()


def sftp_mkdir(sftp, path):
    """Create directory recursively."""
    parts = path.strip("/").split("/")
    current = ""
    for part in parts:
        current += "/" + part
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def upload_dir(sftp, local_dir, remote_dir):
    """Upload a local directory to remote via SFTP."""
    sftp_mkdir(sftp, remote_dir)
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"
        if os.path.isfile(local_path):
            print(f"  upload: {item}")
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            upload_dir(sftp, local_path, remote_path)


def main():
    print(f"Connecting to {VM_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VM_IP, username=VM_USER, password=VM_PASS, timeout=10)
    print("Connected.")

    # Step 1a: Check existing state
    print("\n--- Checking VM state ---")
    rc, out, err = ssh_cmd(ssh, "ls ~/ros2_ws/src/")
    print(f"ros2_ws/src contents: {out.strip()}")

    rc, out, err = ssh_cmd(ssh, "source /opt/ros/humble/setup.bash && ros2 pkg list 2>/dev/null | grep -E 'gsl|olfaction|nav2' | head -20")
    print(f"Relevant ROS2 packages:\n{out.strip()}")

    rc, out, err = ssh_cmd(ssh, "pip3 list 2>/dev/null | grep -i gaden")
    print(f"GADEN Python: {out.strip() or 'NOT FOUND'}")

    # Step 1b: Upload vgr_bridge package
    print(f"\n--- Uploading vgr_bridge to {VM_BRIDGE} ---")
    sftp = ssh.open_sftp()

    # Remove old version if exists
    rc, _, _ = ssh_cmd(ssh, f"rm -rf {VM_BRIDGE}")

    upload_dir(sftp, LOCAL_BRIDGE, VM_BRIDGE)
    sftp.close()

    # Verify upload
    rc, out, err = ssh_cmd(ssh, f"find {VM_BRIDGE} -type f | sort")
    print(f"\nUploaded files:\n{out.strip()}")

    # Step 1c: Build with colcon
    print("\n--- Building vgr_bridge with colcon ---")
    rc, out, err = ssh_cmd(
        ssh,
        "cd ~/ros2_ws && source /opt/ros/humble/setup.bash && "
        "colcon build --packages-select vgr_bridge --symlink-install 2>&1",
        timeout=120,
    )
    print(f"Build exit code: {rc}")
    if out:
        # Show last 30 lines
        lines = out.strip().split("\n")
        for line in lines[-30:]:
            print(f"  {line}")
    if err:
        print(f"STDERR:\n{err[-500:]}")

    # Step 1d: Verify build
    rc, out, err = ssh_cmd(ssh, "ls ~/ros2_ws/install/vgr_bridge/share/vgr_bridge/launch/ 2>/dev/null")
    print(f"\nLaunch files installed: {out.strip()}")

    rc, out, err = ssh_cmd(ssh, "ls ~/ros2_ws/install/vgr_bridge/lib/vgr_bridge/ 2>/dev/null")
    print(f"Executables installed: {out.strip()}")

    ssh.close()
    print("\n=== Step 1 Complete ===")


if __name__ == "__main__":
    main()
