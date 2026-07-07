"""Smoke test: launch vgr_sim_node + gsl_actionserver_node + benchmark runner on VM."""
import paramiko
import sys
import time

VM_IP = "192.168.111.128"
VM_USER = "zyc"
VM_PASS = "123456"

VGR_DATA = "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01"
SOURCE_X, SOURCE_Y, SOURCE_Z = "-0.40", "-2.90", "-0.30"
CONFIG_ID = "2,4-1_fast"
START_X, START_Y = "-5.0", "-5.0"


def ssh_cmd(ssh, cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    rc = stdout.channel.recv_exit_status()
    return rc, stdout.read().decode(), stderr.read().decode()


def main():
    algorithm = sys.argv[1] if len(sys.argv) > 1 else "PMFS"
    timeout_sec = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    print(f"Connecting to {VM_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VM_IP, username=VM_USER, password=VM_PASS, timeout=10)
    print("Connected.\n")

    # Kill any existing GSL processes
    print("--- Cleaning up existing processes ---")
    ssh_cmd(ssh, "pkill -f gsl_actionserver_node 2>/dev/null; pkill -f vgr_sim_node 2>/dev/null; pkill -f gsl_benchmark_runner 2>/dev/null")
    time.sleep(1)

    # Build the smoke test script for the VM
    output_csv = f"/tmp/gsl_smoke_{algorithm}.csv"
    bashrc = "source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash"

    smoke_script = f"""#!/bin/bash
set -e
{bashrc}

echo "[1/3] Starting vgr_sim_node..."
ros2 run vgr_bridge vgr_sim_node --ros-args \\
  -p vgr_data_path:={VGR_DATA} \\
  -p config_id:={CONFIG_ID} \\
  -p flight_height:=1.0 \\
  -p start_x:={START_X} \\
  -p start_y:={START_Y} \\
  -p step_size:=0.3 \\
  -p move_delay:=0.02 &
SIM_PID=$!
echo "  vgr_sim_node PID: $SIM_PID"

sleep 3

echo "[2/3] Starting gsl_actionserver_node..."
ros2 run gsl_server gsl_actionserver_node &
GSL_PID=$!
echo "  gsl_actionserver PID: $GSL_PID"

sleep 5

echo "[3/3] Starting gsl_benchmark_runner ({algorithm})..."
ros2 run vgr_bridge gsl_benchmark_runner --ros-args \\
  -p algorithm:={algorithm} \\
  -p output_csv:={output_csv} \\
  -p source_x:={SOURCE_X} \\
  -p source_y:={SOURCE_Y} \\
  -p source_z:={SOURCE_Z} \\
  -p timeout_sec:={float(timeout_sec)} \\
  -p seed:=0 \\
  -p config_id:={CONFIG_ID}

echo "Benchmark done. Cleaning up..."
kill $SIM_PID $GSL_PID 2>/dev/null || true

echo ""
echo "=== Results ==="
cat {output_csv} 2>/dev/null || echo "No result CSV"
"""

    # Upload script
    sftp = ssh.open_sftp()
    with sftp.open("/tmp/smoke.sh", "w") as f:
        f.write(smoke_script)
    sftp.close()
    ssh_cmd(ssh, "chmod +x /tmp/smoke.sh")
    print("Smoke script uploaded to /tmp/smoke.sh")

    # Execute
    print(f"\n--- Running smoke test (algorithm={algorithm}, timeout={timeout_sec}s) ---\n")

    stdin, stdout, stderr = ssh.exec_command(
        "bash /tmp/smoke.sh",
        timeout=timeout_sec + 60,
        get_pty=True,
    )

    for line in iter(stdout.readline, ""):
        print(line.rstrip())

    rc = stdout.channel.recv_exit_status()
    print(f"\nExit code: {rc}")

    # Read results
    rc2, out, _ = ssh_cmd(ssh, f"cat {output_csv} 2>/dev/null")
    if out.strip():
        print(f"\n--- Result CSV ---\n{out.strip()}")
    else:
        print("\nNo result CSV found.")

    ssh.close()
    print("\n=== Smoke test complete ===")


if __name__ == "__main__":
    main()
