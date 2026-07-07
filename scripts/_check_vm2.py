"""
Check GSL action server ROS2 topic expectations on remote VM (192.168.111.128).
Phase 2: deeper exploration based on Phase 1 findings (no include/ or launch/ at expected paths).
Source lives at ~/ros2_ws/src/GSL/gsl_server/src/gsl_server/
"""

import paramiko
import sys

VM_HOST = "192.168.111.128"
VM_USER = "zyc"
VM_PASS = "123456"

# Base dir discovered in Phase 1
SRC = "~/ros2_ws/src/GSL/gsl_server/src/gsl_server"

COMMANDS = [
    # ---- directory structure ----
    ("A. GSL top-level tree",
     f"find ~/ros2_ws/src/GSL -maxdepth 3 -type d | sort"),

    ("B. gsl_server src tree (dirs only)",
     f"find {SRC} -type d | sort"),

    # ---- find ALL header files ----
    ("C. all .hpp files",
     f"find {SRC} -name '*.hpp' | sort"),

    # ---- find ALL .cpp files ----
    ("D. all .cpp files",
     f"find {SRC} -name '*.cpp' | sort"),

    # ---- find launch / config / yaml anywhere in GSL ----
    ("E. all yaml/xml/launch.py in GSL repo",
     "find ~/ros2_ws/src/GSL -name '*.yaml' -o -name '*.xml' -o -name '*.launch.py' | sort"),

    # ---- topic subscriptions: create_subscription calls ----
    ("F. create_subscription in all hpp/cpp",
     f"grep -rn 'create_subscription' {SRC}/ --include='*.hpp' --include='*.cpp' | head -40"),

    # ---- topic subscriptions: subscription variable names ----
    ("G. subscription / sub_ variables",
     f"grep -rn 'Subscription\\|subscription\\|sub_' {SRC}/ --include='*.hpp' --include='*.cpp' | head -40"),

    # ---- publishers: create_publisher / publish( ----
    ("H. create_publisher / publish calls",
     f"grep -rn 'create_publisher\\|->publish(' {SRC}/ --include='*.hpp' --include='*.cpp' | head -40"),

    # ---- action client/server ----
    ("I. action client/server (Nav2Goal / action)",
     f"grep -rn 'action_client\\|ActionClient\\|send_goal\\|NavigateToPose\\|action_server\\|FollowTopic' "
     f"{SRC}/ --include='*.hpp' --include='*.cpp' | head -30"),

    # ---- gas / wind / odometry topic strings ----
    ("J. hardcoded topic string literals",
     f"grep -rn '\"/.*\"' {SRC}/ --include='*.hpp' --include='*.cpp' | "
     f"grep -i 'gas\\|wind\\|odometry\\|pose\\|cmd_vel\\|concentration\\|anemometer' | head -30"),

    # ---- Parameter declarations (rclcpp params) ----
    ("K. declare_parameter / get_parameter",
     f"grep -rn 'declare_parameter\\|get_parameter\\|param' {SRC}/ --include='*.hpp' --include='*.cpp' | head -40"),

    # ---- Algorithm base class (subscribe logic) ----
    ("L. Algorithm base class full content",
     f"cat {SRC}/algorithms/Common/Algorithm.hpp"),

    # ---- Algorithm.cpp (init / constructor) ----
    ("M. Algorithm.cpp full content",
     f"cat {SRC}/algorithms/Common/Algorithm.cpp 2>/dev/null"),

    # ---- GSL_server node (main node setup) ----
    ("N. find main node / server class",
     f"grep -rln 'class.*Node\\|rclcpp::Node\\|GSL_server\\|GslServer' {SRC}/ "
     f"--include='*.hpp' --include='*.cpp' | head -10"),

    # ---- cat those node files ----
    ("O. cat main node hpp files",
     f"for f in $(grep -rln 'rclcpp::Node\\|GSL_server\\|GslServer' {SRC}/ "
     f"--include='*.hpp' | head -5); do echo '=== '$f' ==='; cat \"$f\"; done"),

    # ---- PMFS header ----
    ("P. PMFS.hpp content",
     f"cat {SRC}/algorithms/PMFS/PMFS.hpp 2>/dev/null"),

    # ---- GrGSL header ----
    ("Q. GrGSL.hpp content",
     f"cat {SRC}/algorithms/GrGSL/GrGSL.hpp 2>/dev/null"),

    # ---- Spiral header ----
    ("R. Spiral.hpp content",
     f"cat {SRC}/algorithms/Spiral/Spiral.hpp 2>/dev/null"),

    # ---- Algorithm enum or method selection ----
    ("S. method selection / enum",
     f"grep -rn 'enum\\|Method\\|AlgorithmType\\|gsl_method\\|chooseAlgorithm\\|createAlgorithm' "
     f"{SRC}/ --include='*.hpp' --include='*.cpp' | head -20"),

    # ---- any action interface / .action files ----
    ("T. .action files",
     "find ~/ros2_ws/src/GSL -name '*.action' 2>/dev/null"),

    # ---- CMakeLists / package.xml for deps ----
    ("U. package.xml",
     "cat ~/ros2_ws/src/GSL/gsl_server/package.xml 2>/dev/null | head -40"),

    # ---- resources dir ----
    ("V. resources dir listing",
     "ls ~/ros2_ws/src/GSL/gsl_server/resources/ 2>/dev/null"),

    # ---- all yaml files content ----
    ("W. all yaml content",
     "for f in $(find ~/ros2_ws/src/GSL -name '*.yaml' 2>/dev/null); do "
     "echo \"=== $f ===\"; cat \"$f\"; done"),

    # ---- follow_gas / utility subscriber ----
    ("X. gas measurement callback",
     f"grep -rn 'gasCallback\\|gas_callback\\|onGas\\|gasMessage\\|gasMsg\\|concentration' "
     f"{SRC}/ --include='*.hpp' --include='*.cpp' | head -30"),

    # ---- wind callback ----
    ("Y. wind callback",
     f"grep -rn 'windCallback\\|wind_callback\\|onWind\\|windMessage\\|windMsg\\|anemometer\\|windSpeed' "
     f"{SRC}/ --include='*.hpp' --include='*.cpp' | head -30"),

    # ---- odometry / pose callback ----
    ("Z. pose callback",
     f"grep -rn 'poseCallback\\|pose_callback\\|onPose\\|odomCallback\\|odom_callback\\|robotPose\\|robot_pose' "
     f"{SRC}/ --include='*.hpp' --include='*.cpp' | head -30"),
]


def run_ssh_commands():
    print(f"Connecting to {VM_HOST} as {VM_USER} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(VM_HOST, username=VM_USER, password=VM_PASS, timeout=10)
    except Exception as e:
        print(f"ERROR: Cannot connect to {VM_HOST}: {e}")
        sys.exit(1)

    print(f"Connected. Running {len(COMMANDS)} commands.\n")

    for idx, (label, cmd) in enumerate(COMMANDS, 1):
        print(f"\n{'#' * 80}")
        print(f"# [{idx}/{len(COMMANDS)}] {label}")
        print(f"# CMD: {cmd}")
        print(f"{'#' * 80}")

        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")

        if out.strip():
            print(out)
        else:
            print("(no stdout)")
        if err.strip():
            print(f"[STDERR] {err}")

    print("\n" + "=" * 80)
    print("Phase 2 complete.")
    client.close()


if __name__ == "__main__":
    run_ssh_commands()
