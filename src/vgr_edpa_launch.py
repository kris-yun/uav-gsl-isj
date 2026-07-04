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
        DeclareLaunchArgument("vgr_data_path", default_value="/home/zyc/enva_vgr"),
        DeclareLaunchArgument("config_id", default_value="A1_fast"),
        DeclareLaunchArgument("algorithm", default_value="OPGSL"),
        DeclareLaunchArgument("method", default_value="M7_full_saisc_pf"),
        DeclareLaunchArgument("source_x", default_value="5.00"),
        DeclareLaunchArgument("source_y", default_value="6.20"),
        DeclareLaunchArgument("source_z", default_value="0.50"),
        DeclareLaunchArgument("start_x", default_value="4.0"),
        DeclareLaunchArgument("start_y", default_value="4.0"),
        DeclareLaunchArgument("seed", default_value="0"),
        DeclareLaunchArgument("timeout_sec", default_value="300.0"),
        DeclareLaunchArgument("resultsFile", default_value="/tmp/edpa_results.csv"),
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
                "opgsl.seed": _int("seed"),
                "opgsl.modules.edpa": True,
                "opgsl.edpa.detection_threshold": 0.01,
                "opgsl.edpa.lambda0": 1.0,
                "opgsl.edpa.ell": 2.0,
                "opgsl.edpa.alphaw": 0.5,
                "opgsl.edpa.stop_epsilon": 1.5,
                "opgsl.edpa.stop_delta": 0.10,
                "opgsl.edpa.stop_eta": 5.0,
                "opgsl.modules.sbd": False,
                "opgsl.modules.ddm": False,
                "opgsl.modules.cp": False,
                "opgsl.modules.wraig": False,
                "opgsl.modules.upwind_tracking": False,
                "opgsl.modules.levy": True,
                "opgsl.modules.bout": True,
                "opgsl.modules.adaptive_step": True,
                "opgsl.sdnbv.enabled": True,
                "opgsl.convergence.min_time": 30.0,
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
                    "output_csv": LaunchConfiguration("resultsFile"),
                }]),
        ]),
    ])
