import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,SetLaunchConfiguration,IncludeLaunchDescription,SetEnvironmentVariable,OpaqueFunction,GroupAction,Shutdown
from launch.launch_description_sources import FrontendLaunchDescriptionSource, PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from ament_index_python.packages import get_package_share_directory
from launch.frontend.parse_substitution import parse_substitution

#===========================
def launch_arguments():
    return [
        DeclareLaunchArgument("scenario", default_value="A"),
        DeclareLaunchArgument("simulation", default_value="A1"),
        DeclareLaunchArgument("method",	default_value=["PMFS"]),
        DeclareLaunchArgument("use_infotaxis", default_value=["True"]),
    ]
#==========================

def launch_setup(context, *args, **kwargs):
    import sys
    sys.path.append(get_package_share_directory("gaden_common"))
    from gaden_internal_py.utils import read_sim_yaml
    context.launch_configurations["pkg_dir"] = get_package_share_directory("pmfs_env")
    read_sim_yaml(context)
    method = LaunchConfiguration("method").perform(context)
    gsl_call = [
        GroupAction(actions=[
            PushRosNamespace(LaunchConfiguration("robot_name")),
            Node(
                package="gsl_server",
                executable="gsl_actionserver_call",
                name="gsl_call",
                parameters=[
                    {"method": parse_substitution("$(var method)")},
                ],
            ),
        ])
    ]
    gsl_node = [
        GroupAction(actions=[
            PushRosNamespace(LaunchConfiguration("robot_name")),
            Node(
                package="gsl_server",
                executable='/home/zyc/ros2_ws/pmfs_early_declaration_20261018/gsl_actionserver_node',
                name="GSL",
                parameters=[
                    # Common
                    {'use_sim_time': False},	
                    {"maxSearchTime": 300.0},
                    {"robot_location_topic": "ground_truth"}, {"anemometer_topic": "/native20/wind_to"},
                    {"stop_and_measure_time": 0.4},
                    {"th_gas_present": parse_substitution("$(var th_gas_present)")},
                    {"th_wind_present": parse_substitution("$(var th_wind_present)")},
                    {"ground_truth_x": parse_substitution("$(var source_x)")},
                    {"ground_truth_y": parse_substitution("$(var source_y)")},
                    {'resultsFile': '/mnt/hgfs/workspace/PMFS_EARLY_DECLARATION_AUDIT_20261018/cases/EA18_B2_R01/runtime/native_results.csv'}, {'navigationPathFile': '/mnt/hgfs/workspace/PMFS_EARLY_DECLARATION_AUDIT_20261018/cases/EA18_B2_R01/runtime/navigation_path.csv'},
                    
                    {"scale": 25},
                    {"markers_height": 0.2},

                    {"anemometer_frame": parse_substitution("$(var robot_name)_anemometer_frame")},
                    {"openMoveSetExpasion": 5},
                    {"explorationProbability": 0.05},
                    {"convergence_thr": 1.0},
                    
                    #GrGSL
                    {"useDiffusionTerm": True},
                    {"stdevHit": 1.0},
                    {"stdevMiss": 1.2},
                    {"infoTaxis": parse_substitution("$(var use_infotaxis)")},
                    {"allowMovementRepetition": parse_substitution("$(var use_infotaxis)")},

                    #PMFS
                        # Hit probabilities
                    {"headless": True},
                    {"maxUpdatesPerStop": 5},
                    {"kernelSigma": 1.5},
                    {"kernelStretchConstant": 1.5},
                    {"hitPriorProbability": 0.3},
                    {"confidenceSigmaSpatial": 1.0},
                    {"confidenceMeasurementWeight": 1.0},
                    {"initialExplorationMoves" : parse_substitution("$(var initialExplorationMoves)")},
                        #Filament simulation
                    {"useWindGroundTruth": False},
                    {"stepsSourceUpdate": 3},
                    {"maxRegionSize": 5},
                    {"sourceDiscriminationPower": 1.0},
                    {"refineFraction": 0.1},
                    {"deltaTime": parse_substitution("$(var filamentDeltaTime)")},
                    {"noiseSTDev": parse_substitution("$(var filament_movement_stdev)")},
                    {"iterationsToRecord": parse_substitution("$(var iterationsToRecord)")},
                    {"maxWarmupIterations": parse_substitution("$(var maxWarmupIterations)")},

                    #Surge-Cast
                    {"step": 0.5},

                    
                ],
                
            ),
        ])
    ]

    gmrf_wind = Node(
        package="gmrf_wind_mapping",
        executable="gmrf_wind_mapping_node",
        name="gmrf",
        parameters=[
            {"sensor_topic": parse_substitution("$(var robot_name)/Anemometer/WindSensor_reading")},
            {"map_topic": parse_substitution("$(var robot_name)/map")},
            {"cell_size": 0.25},
        ]
    )

    basic_sim = Node(
        package="basic_sim",
        executable="basic_sim",
        parameters=[
            {"deltaTime": 0.1},
            {"speed": 5.0},
            {"worldFile": parse_substitution("$(find-pkg-share pmfs_env)/scenarios/$(var scenario)/basicSim/$(var simulation).yaml")}
            ],
    )

    gaden_player = Node(package='gaden_player', executable='/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016/public_clock_player', name='gaden_player', remappings=[('/odor_value','/native20/raw_odor_value'),('/wind_value','/native20/raw_wind_value')], parameters=[{'use_sim_time': False, 'player_freq': 2.0, 'initial_iteration': 500, 'num_simulators': 1, 'allow_looping': False, 'loop_from_iteration': 800, 'loop_to_iteration': 900, 'simulation_data_0': '/mnt/hgfs/workspace/NATIVE_PMFS_FULL20_20261014/cases/B2/one_realization', 'occupancyFile': '/mnt/hgfs/workspace/NATIVE_PMFS_FULL20_20261014/derived/5d9684e340a6/OccupancyGrid3D.csv', 'r7_frame_time_csv': '/home/zyc/ros2_ws/pmfs_early_declaration_20261018/cases/EA18_B2_R01/AUTHOR_WALL_FILE_CADENCE.csv', 'r7_clock_trace_path': '/mnt/hgfs/workspace/PMFS_EARLY_DECLARATION_AUDIT_20261018/cases/EA18_B2_R01/runtime/physical_clock_trace.csv'}])

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory("pmfs_env"),
                    "navigation_config/nav2_launch.py",
                )
            ),
            launch_arguments={
                "scenario": LaunchConfiguration("scenario"), "log_level":"INFO",
                "namespace" : LaunchConfiguration("robot_name")
            }.items(),
    )

    anemometer = [
        GroupAction(actions=[
            PushRosNamespace(LaunchConfiguration("robot_name")),
            Node(
                package="simulated_anemometer",
                executable="simulated_anemometer",
                name="Anemometer",
                parameters=[
                    {"sensor_frame" : parse_substitution("$(var robot_name)_anemometer_frame") },
                    {"fixed_frame" : "map"},
                    {"noise_std" : 0.3},
                    {"use_map_ref_system" : False},
                    {'use_sim_time': True},
                ]
            ),
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name='anemometer_tf_pub',
                arguments = ['0', '0', '0.5', '1.0', '0.0', '0', '0', parse_substitution('$(var robot_name)_base_link'), parse_substitution('$(var robot_name)_anemometer_frame')],
                parameters=[{'use_sim_time': True}]
            ),
        ])
    ]

    PID = [
        GroupAction(actions=[
            PushRosNamespace(LaunchConfiguration("robot_name")),
            Node(
                package="simulated_gas_sensor",
                executable="simulated_gas_sensor",
                name="PID",
                parameters=[
                    {"sensor_model" : 30 },
                    {"sensor_frame" : parse_substitution("$(var robot_name)_pid_frame") },
                    {"fixed_frame" : "map"},
                    {"noise_std" : 20.1},
                    {'use_sim_time': True},
                ]
            ),
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name='pid_tf_pub',
                arguments = ['0', '0', '0.5', '1.0', '0.0', '0', '0', parse_substitution('$(var robot_name)_base_link'), parse_substitution('$(var robot_name)_pid_frame')],
                parameters=[{'use_sim_time': True}]
            ),
        ])
    ]

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz",
        #prefix="xterm -e",
        arguments=[
            "-d" + os.path.join(get_package_share_directory("pmfs_env"), "launch", "gaden.rviz")
        ],
    )

    actions = []
    actions.append(gaden_player)
    actions.extend(anemometer)
    actions.extend(PID)
    actions.append(nav2)
    # actions.append(gmrf_wind)
    actions.append(basic_sim)
    actions.extend(gsl_node)
    # actions.extend(gsl_call)
    # Headless display-only omission: actions.append(rviz)

    return actions


def generate_launch_description():

    launch_description = [
        # Set env var to print messages to stdout immediately
        SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1"),
        SetEnvironmentVariable("RCUTILS_COLORIZED_OUTPUT", "1"),
        SetLaunchConfiguration(
            name="pkg_dir",
            value=[get_package_share_directory("pmfs_env")],
        ),
        SetLaunchConfiguration(
            name="nav_params_yaml",
            value=[PathJoinSubstitution(
                [LaunchConfiguration("pkg_dir"), "navigation_config", "nav2_params.yaml"]
            )],
        ),

        SetLaunchConfiguration(
            name="robot_name", 
            value="PioneerP3DX"
        ),


        # GSL params (overwritable in each YAML)
        ##############################################
        SetLaunchConfiguration(
            name="th_gas_present", 
            value="0.1"
        ),
        SetLaunchConfiguration(
            name="th_wind_present", 
            value="0.02"
        ),

        SetLaunchConfiguration(
            name="filament_movement_stdev", 
            value="0.5"
        ),
        SetLaunchConfiguration(
            name="sourceDiscriminationPower", 
            value="0.2"
        ),
        SetLaunchConfiguration(
            name="iterationsToRecord", 
            value="200"
        ),
        SetLaunchConfiguration(
            name="maxWarmupIterations", 
            value="500"
        ),
        SetLaunchConfiguration(
            name="initialExplorationMoves", 
            value="2"
        ),
        SetLaunchConfiguration(
            name="filamentDeltaTime", 
            value="0.1"
        ),
    ]
    
    launch_description.extend(launch_arguments())
    launch_description.append(OpaqueFunction(function=launch_setup))
    
    return  LaunchDescription(launch_description)