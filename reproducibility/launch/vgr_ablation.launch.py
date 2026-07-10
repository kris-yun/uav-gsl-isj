from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def _int(name):
    return ParameterValue(LaunchConfiguration(name), value_type=int)
def _bool(name):
    return ParameterValue(LaunchConfiguration(name), value_type=bool)
def _float(name):
    return ParameterValue(LaunchConfiguration(name), value_type=float)

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("vgr_data_path", default_value="/home/zyc/vgr_data_scenarios/House01"),
        DeclareLaunchArgument("config_id", default_value="2,4-1_fast"),
        DeclareLaunchArgument("algorithm", default_value="OPGSL"),
        DeclareLaunchArgument("method", default_value="M7_full_saisc_pf"),
        DeclareLaunchArgument("source_x", default_value="-0.40"),
        DeclareLaunchArgument("source_y", default_value="-2.90"),
        DeclareLaunchArgument("source_z", default_value="-0.30"),
        DeclareLaunchArgument("start_x", default_value="-0.9"),
        DeclareLaunchArgument("start_y", default_value="0.15"),
        DeclareLaunchArgument("seed", default_value="0"),
        DeclareLaunchArgument("timeout_sec", default_value="300.0"),
        DeclareLaunchArgument("resultsFile", default_value="/tmp/sbd_test_results.csv"),
        DeclareLaunchArgument("use_sbd", default_value="true"),
        # Ablation toggles
        DeclareLaunchArgument("opgsl_ddm", default_value="true"),
        DeclareLaunchArgument("opgsl_wraig", default_value="true"),
        DeclareLaunchArgument("opgsl_cp", default_value="true"),
        DeclareLaunchArgument("opgsl_wraig_beta", default_value="0.5"),
        Node(package="vgr_bridge", executable="vgr_sim_node", name="vgr_uav_sim", output="screen",
            parameters=[{
                "vgr_data_path": LaunchConfiguration("vgr_data_path"),
                "config_id": LaunchConfiguration("config_id"),
                "flight_height": 0.3,
                "start_x": _float("start_x"),
                "start_y": _float("start_y"),
                "seed": _int("seed"),
            }]),
        Node(package="gsl_server", executable="gsl_actionserver_node", name="gsl_server", output="screen",
            parameters=[{
                "use_sim_time": False,
                "maxSearchTime": _float("timeout_sec"),
                "distanceThreshold": -1.0,
                "resultsFile": LaunchConfiguration("resultsFile"),
                "ground_truth_x": _float("source_x"),
                "ground_truth_y": _float("source_y"),
                "opgsl.modules.sbd": _bool("use_sbd"),
                "opgsl.seed": _int("seed"),
                "opgsl.sbd.eig_threshold": 0.0005,
                "opgsl.sbd.cusum_threshold": 5.0,
                "opgsl.sbd.cusum_drift": 0.1,
                                "opgsl.data_path": LaunchConfiguration("vgr_data_path"),
"opgsl.convergence.min_time": 30.0,
                "opgsl.modules.levy": True,
                "opgsl.modules.bout": True,
                "opgsl.modules.adaptive_step": True,
                "opgsl.modules.upwind_tracking": True,
                "opgsl.sdnbv.enabled": True,
                "opgsl.altitude.gp": True,
                "opgsl.altitude.z_min": -0.5,
                "opgsl.altitude.z_max": 2.0,
                # New ablation modules
                "opgsl.modules.ddm": _bool("opgsl_ddm"),
                "opgsl.modules.wraig": _bool("opgsl_wraig"),
                "opgsl.modules.cp": _bool("opgsl_cp"),
                "opgsl.wraig.beta": _float("opgsl_wraig_beta"),
                "opgsl.event_driven.enabled": True,
                "opgsl.event_driven.detection_threshold": 0.01,
                "opgsl.event_driven.lambda0": 2.0,
                "opgsl.event_driven.ell": 1.0,
                "opgsl.event_driven.alpha_w": 0.5,
                "useWindGroundTruth": True,
            }]),
        TimerAction(period=5.0, actions=[
            Node(package="vgr_bridge", executable="gsl_benchmark_runner", name="benchmark", output="screen",
                parameters=[{
                    "algorithm": LaunchConfiguration("algorithm"),
                    "method": LaunchConfiguration("method"),
                    "source_x": _float("source_x"),
                    "source_y": _float("source_y"),
                    "seed": _int("seed"),
                    "time_budget_s": _float("timeout_sec"),
                    "repo_root": "/home/zyc/gsl_ws/src/GasSourceLocalization",
                }],
            ),
        ]),
    ])