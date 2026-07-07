"""SSH into the ROS2 VM and gather GSL action server info."""

import paramiko
import sys

VM_HOST = "192.168.111.128"
VM_USER = "zyc"
VM_PASS = "123456"

COMMANDS = [
    (
        "=== 1. DoGSL.action content ===",
        "cat ~/ros2_ws/install/gsl_server/share/gsl_server/action/DoGSL.action 2>/dev/null || "
        "find ~/ros2_ws -name 'DoGSL.action' -exec cat {} \\; 2>/dev/null || echo 'NOT FOUND'",
    ),
    (
        "=== 2. Action files in gsl_server ===",
        "ls -la ~/ros2_ws/install/gsl_server/share/gsl_server/action/ 2>/dev/null || echo 'Directory not found'",
    ),
    (
        "=== 3. Lib binaries in gsl_server ===",
        "ls -la ~/ros2_ws/install/gsl_server/lib/gsl_server/ 2>/dev/null || echo 'Directory not found'",
    ),
    (
        "=== 4. ros2 action list ===",
        "bash -c 'source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash 2>/dev/null && ros2 action list'",
    ),
    (
        "=== 5. ros2 interface show DoGSL ===",
        "bash -c 'source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash 2>/dev/null && ros2 interface show gsl_actions/action/DoGSL 2>&1 || ros2 interface show gsl_server/action/DoGSL 2>&1 || echo \"interface not found\"'",
    ),
    (
        "=== 6. ros2 param list /gsl_actionserver_node ===",
        "bash -c 'source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash 2>/dev/null && ros2 param list /gsl_actionserver_node 2>&1 || echo \"node not running or not found\"'",
    ),
    (
        "=== 7. GADEN/GSL yaml configs ===",
        "find ~/ros2_ws -name '*.yaml' -path '*gsl*' 2>/dev/null | head -20; "
        "find ~/ros2_ws -name '*.yaml' -path '*gaden*' 2>/dev/null | head -20; "
        "echo '--- yaml search done ---'",
    ),
]


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {VM_HOST} as {VM_USER} ...")
    try:
        client.connect(VM_HOST, username=VM_USER, password=VM_PASS, timeout=15)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    print("Connected.\n")

    for title, cmd in COMMANDS:
        print(title)
        print(f"$ {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        if out.strip():
            print(out)
        if err.strip():
            print(f"[stderr] {err}")
        print()

    client.close()
    print("Done.")


if __name__ == "__main__":
    main()
