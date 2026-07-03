# 13 VM Setup and Known Issues

## VM Information
- IP: 192.168.111.128
- User: zyc, Password: 123456
- OS: Ubuntu (ROS2 Humble)
- Python: 3.10.12
- SSH key: configured (passwordless login works)

## Installed Packages
- ROS2 Humble
- GSL server (MAPIRlab/GasSourceLocalization, C++)
- GMRF-wind (MAPIRlab/GMRF-wind)
- VGR bridge (custom Python package)
- GADEN (via gadentools Python package)
- nav2_msgs (installed during session)
- numpy 1.26.4 (downgraded from 2.2.6)

## Key Directories on VM
- GSL source: `~/ros2_ws/src/GSL/gsl_server/`
- VGR bridge: `~/ros2_ws/src/vgr_bridge/`
- GMRF wind: `~/ros2_ws/src/GMRF-wind/`
- VGR data: `/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/`
- Shared workspace: `/mnt/hgfs/workspace/` (maps to D:\ZYC\A-gas\workspace\)
- Baseline results: `/tmp/gsl_final_results/`

## Known Issues

### 1. numpy 2.x breaks gadentools
**Symptom**: vgr_sim_node crashes with "downgrade to numpy<2"
**Fix**: `pip3 install 'numpy<2' --user --force-reinstall`

### 2. GMRF wind service not running
**Symptom**: PMFS quadtree has 0 cells, PMFS declares immediately
**Fix**: Start GMRF before PMFS:
```
ros2 run gmrf_wind_mapping gmrf_wind_mapping_node --ros-args \
    -p frame_id:=map \
    -p sensor_topic:=/Anemometer/WindSensor_reading \
    -p map_topic:=/map \
    -p exec_freq:=10.0 \
    -p cell_size:=0.3
```

### 3. nav2_msgs not installed
**Symptom**: PMFS cannot navigate (ComputePathToPose not available)
**Fix**: `sudo apt-get install ros-humble-nav2-msgs`

### 4. scale parameter not passed to GSL server
**Symptom**: PMFS uses scale=65 (1×1 grid) instead of scale=3 (29×38 grid)
**Fix**: Use `vgr_gsl_pmfs.launch.py` (has scale=3 hardcoded) instead of
`vgr_gsl_benchmark.launch.py` (has scale=65 default)

### 5. convergence_thr not received by GSL server
**Symptom**: PMFS always uses default threshold 0.5 regardless of launch param
**Status**: UNRESOLVED — ROS2 parameter declaration issue in GSL server
**Workaround**: Use the official PMFS launch file (threshold=0.5 is acceptable)

### 6. Process cleanup between experiments
**Symptom**: Sequential experiments fail due to resource contention
**Fix**: Kill all GSL/ROS2 processes between experiments:
```
ps aux | grep 'gsl_action\|vgr_sim' | grep -v grep | awk '{print $2}' | xargs kill -9
sleep 3
```

### 7. GrGSL consistently times out
**Symptom**: GrGSL experiments timeout at 180s
**Status**: UNRESOLVED — may need different convergence parameters

## Running Experiments on VM

### Start GMRF Wind Service (Required for PMFS)
```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
nohup ros2 run gmrf_wind_mapping gmrf_wind_mapping_node --ros-args \
    -p frame_id:=map \
    -p sensor_topic:=/Anemometer/WindSensor_reading \
    -p map_topic:=/map \
    -p exec_freq:=10.0 \
    -p cell_size:=0.3 \
    > /tmp/gmrf.log 2>&1 &
```

### Run PMFS (Official Launch)
```bash
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
    vgr_data_path:='/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01' \
    config_id:='2,4-1_fast' \
    source_x:='-0.4' source_y:='-2.9' source_z:='-0.3' \
    start_x:='-0.55' start_y:='2.12' \
    seed:=0 \
    output_csv:='/tmp/pmfs_result.csv' \
    server_results_file:='/tmp/pmfs_server.txt' \
    server_path_file:='/tmp/pmfs_path.txt'
```

### Run via Benchmark Launch (for systematic comparison)
```bash
python3 ~/run_baselines_final.py
```
