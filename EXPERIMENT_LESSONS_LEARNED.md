# UAV GSL 实验经验教训总结 (2026-06-23)

## 一、Seed参数传递

### 问题
launch文件的seed参数名是 `seed`，不是 `random_seed`。
之前脚本用 `random_seed:=1` 导致seed始终为默认值0。

### 正确用法
```
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py seed:=2 ...
```

### 验证方法
检查 `run_status.json` 中的 `"seed"` 字段是否与传入值一致。
检查 `sim_pose_trace.csv` 的 `seed` 列是否不同。

### 代码位置
- launch参数声明: vgr_gsl_pmfs.launch.py 第52行
- 传给gsl_server: 第125行 `'random_seed': _int('seed')`
- 传给runner: 第184行 `'seed': _int('seed')`
- 传给sim_node: 第102行 `'seed': _int('seed')`

---

## 二、气体检测与起始位置

### 问题
起始位置 (-5,-5) 距源 (-0.4,-2.9) 约5.1m，UAV在300s内无法到达gas plume区域。
导致 raw_hit_count=0，SEPF后验无法更新，所有实验数据无效。

### 关键发现
- 风向 ~1.63 rad (93°, 东)，气体向东扩散
- (-1.5,-2.5) 在源的上风向（西边），但仍有气体: true_gas=0.64ppm
- B0从(-1.5,-2.5)能移动到(-0.27,-1.37)，说明surge_cast在此位置工作
- SEPF从(-1.5,-2.5)能移动到(-0.67,0.15)，说明SEPF工作正常

### 结论
从(-5,-5)出发，explore策略（golden-angle）无法将UAV导向源方向。
需要coverage-first策略：先用lawnmower/beacon覆盖搜索，找到gas后再启用SEPF/PMFS。

### 实验建议
1. 先用近源位置验证算法正确性
2. 再用(-5,-5)测试explore策略改进
3. 测试时检查 `true_gas_ppm` 是否 > 0（读sensor_trace.csv第7列，不是第5列）

---

## 三、Sensor Trace CSV 列顺序

### 列定义 (0-indexed)
```
0: t_ros_s
1: step
2: iteration
3: x
4: y          <-- 注意：不是gas!
5: z
6: true_gas_ppm    <-- 真实气体浓度
7: measured_gas_ppm <-- 传感器读数
8: sensor_mode
9: seed
```

### 常见错误
读 fields[4] 以为是gas，实际是y坐标。
正确应读 fields[6] (true_gas_ppm) 或 fields[7] (measured_gas_ppm)。

---

## 四、B0 Estimate计算修复

### 问题
B0 baseline (use_sepf=0) 时，estimate默认为(0,0)而非终端位置。
导致 final_error_m = distance((0,0), source) = 2.927m，不是真实误差。

### 修复
在 saveResultsToFile() 中，当 pf_ 为空时，将 latest_estimate_ 设置为终端位置：
```cpp
if (pf_) {
    latest_estimate_ = pf_->estimate();
} else {
    latest_estimate_.mean = {
        currentRobotPose.pose.pose.position.x,
        currentRobotPose.pose.pose.position.y
    };
}
```

### 代码位置
SensorAwareSurgeCastPF.cpp 第957行 saveResultsToFile()

---

## 五、Wind Speed Bug (已修复)

### 问题
SensorAwareSurgeCastPF.cpp 第273行：
```cpp
obs.wind_speed = 0.0;  // 硬编码!
```
导致SEPF的各向异性羽流模型完全失效。

### 修复
```cpp
obs.wind_speed = std::abs(latest_wind_speed_m_s_);
```

### 影响
所有先前SEPF实验结果不可信。修复后SEPF能正确使用风速信息。

---

## 六、PMFS GMRF问题

### 问题
PMFS官方基线报 "CANNOT READ ESTIMATED WIND VECTORS"。
GMRF风场估计管道没有正确连接。

### 影响
PMFS精度差（6.32m vs 论文声称2.41m）。
需要检查 gmrf_wind_mapping_node、topic、QoS、map frame。

### 状态
未修复。需要单独排查GMRF管道。

---

## 七、Benchmark Runner问题

### 问题1: git仓库检查
runner需要git仓库来获取commit hash。
修复：在gsl_ws目录初始化git仓库。

### 问题2: repo_root参数
runner的repo_root默认为os.getcwd()（install目录）。
修复：在launch文件中添加 'repo_root': '/home/zyc/gsl_ws'

### 问题3: trace文件路径
runner期望trace文件在 /tmp/gsl_runs_v4/runs/<run_id>/trace.csv
但vgr_sim_node写在 run_dir/sensor_trace.csv
可能导致 "missing synchronized trace file" 错误。

---

## 八、实验流程检查清单

### 每次实验前
1. [ ] 清理旧ROS2进程: `pkill -9 -f ros2; sleep 2`
2. [ ] 确认代码已构建: `colcon build --packages-select gsl_server vgr_bridge`
3. [ ] 确认git仓库存在: `cd /home/zyc/gsl_ws && git status`
4. [ ] 使用正确的seed参数: `seed:=X` (不是random_seed)

### 每次实验后
1. [ ] 检查 run_status.json 的 seed 字段
2. [ ] 检查 sim_pose_trace.csv 的起始和终止位置
3. [ ] 检查 sensor_trace.csv 的 true_gas_ppm (fields[6]) 是否 > 0
4. [ ] 检查 saisc_pf_audit.csv 的 raw_hit_count
5. [ ] 检查 wind_trace.csv 的 wind_speed 是否合理 (~0.1-0.8 m/s)

### 数据解读
- raw_hit_count=0: UAV未进入gas plume，后验算法无法工作
- cov_trace不变: 后验未收敛，estimate=先验均值
- 种子结果相同: 检查seed是否正确传递
- UAV不动: 检查explore策略或goal有效性

---

## 九、VGR数据集注意事项

### House01配置
- 源位置: (-0.40, -2.90)
- 默认起始: (-5.0, -5.0)
- 风向配置: 2,4-1_fast (风从西向东)
- 风速: ~0.17 m/s (低风速)
- 飞行高度: 1.0m (benchmark) 或默认

### 气体场
- true_gas_ppm在源附近可达0.6-0.8 ppm
- measured_gas_ppm受MOX传感器动态影响，通常低于true值
- 5m远处气体浓度接近0

### 风场数据
- wind_simulations/ 目录下有U/V/W分量CSV
- 风向约1.63 rad (93°, 东)
- 不同seed的风场数据相同（风场是确定性的）

---

## 十、关键代码文件路径 (VM)

### 算法代码
- /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/SensorAwareSurgeCastPF/SensorAwareSurgeCastPF.cpp
- /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/SensorAwareSurgeCastPF/SensorAwareSurgeCastPF.hpp
- /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/SensorAwareSurgeCastPF/uav_gsl/SoftEvidenceParticleFilter.hpp

### Launch文件
- /home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_gsl_pmfs.launch.py (我们的launch)
- /home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_gsl_benchmark.launch.py (官方benchmark)

### 结果基础设施
- /home/zyc/gsl_ws/src/vgr_bridge/vgr_bridge/result_contract.py
- /home/zyc/gsl_ws/src/vgr_bridge/vgr_bridge/gsl_benchmark_runner.py

### 数据
- /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/
