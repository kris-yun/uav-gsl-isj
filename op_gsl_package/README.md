# OPGSL - UAV Gas Source Localization

基于化学趋向导航的 UAV 气体源定位算法，在 VGR 公开数据集上验证。

## 重要文档

| 文档 | 内容 |
|------|------|
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | **项目现状、目标、问题、踩坑记录、VM 信息** |
| [docs/CROSS_DOMAIN_IDEAS.md](docs/CROSS_DOMAIN_IDEAS.md) | **7 个远领域可迁移思想（附公式和迁移逻辑）** |
| [docs/algorithm_analysis.md](docs/algorithm_analysis.md) | 算法架构 + 创新点 + 消融设计 |
| [docs/experiment_summary.md](docs/experiment_summary.md) | 结果对比表 |

## 文件结构

```
op_gsl_package/
├── README.md                      # 本文件
├── code/                          # C++ 源代码（部署到 VM 的 gsl_server 包）
│   ├── OPGSL.cpp                 # 主算法
│   ├── OPGSL.hpp                 # 头文件
│   ├── WATS_GSL.hpp              # WR-SFE + WA-IG 模块（KDE 场估计 + 信息增益探索）
│   └── CMakeLists.txt            # 编译配置
├── scripts/                       # 运行脚本
│   ├── run_on_vm.py              # 本地 Python 工具：通过 SSH 在 VM 上执行命令
│   ├── launch_single.sh          # VM 端：启动单次 ROS2 launch
│   ├── gsl_run_client.py         # VM 端：ROS2 action client 触发实验
│   ├── run_gsl.sh                # VM 端：launch + client 一体化脚本
│   └── batch_all_v2.sh           # VM 端：批量实验（所有 House × 所有 seed × 所有方法）
├── data/
│   └── experiment_results.csv    # 完整实验结果
└── docs/
    ├── algorithm_analysis.md     # 算法架构 + 创新点 + 消融设计
    └── experiment_summary.md     # 结果对比表
```

## 环境要求

| 项目 | 值 |
|------|-----|
| VM IP | 192.168.111.128 |
| VM 用户 | zyc |
| VM 密码 | 123456 |
| OS | Ubuntu 22.04 |
| ROS | ROS2 Humble |
| 工作空间 | /home/zyc/gsl_ws/ |
| VGR 数据集 | /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/ |

VGR 数据集目录结构：
```
scenarios/
├── House01/    # config_id=2,4-1_fast, source=(-0.40, -2.90, -0.30)
├── House02/    # config_id=3,5-1_fast, source=(0.00, -1.00, 0.20)
└── House03/    # config_id=1-2,5_fast, source=(-0.45, 1.90, -0.10)
```

## 完整复现步骤

### 第一步：部署代码到 VM

从本地 PowerShell 执行（不是 cmd，不是 bash）：

```powershell
# SSH/SCP 工具路径
$SSH = "C:\Windows\System32\OpenSSH\ssh.exe"
$SCP = "C:\Windows\System32\OpenSSH\scp.exe"
$VM = "zyc@192.168.111.128"
$OPT = "-o StrictHostKeyChecking=no"

# 1. 复制 C++ 代码到 VM
& $SCP $OPT "code/OPGSL.cpp" "zyc@192.168.111.128:/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/"
& $SCP $OPT "code/OPGSL.hpp" "zyc@192.168.111.128:/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/"
& $SCP $OPT "code/WATS_GSL.hpp" "zyc@192.168.111.128:/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/"

# 2. 复制运行脚本到 VM /tmp/
& $SCP $OPT "scripts/launch_single.sh" "zyc@192.168.111.128:/tmp/"
& $SCP $OPT "scripts/gsl_run_client.py" "zyc@192.168.111.128:/tmp/"
& $SCP $OPT "scripts/batch_all_v2.sh" "zyc@192.168.111.128:/tmp/"

# 3. 编译
& $SSH $OPT $VM "cd /home/zyc/gsl_ws && source install/setup.bash && colcon build --packages-select gsl_server 2>&1 | tail -5"
```

编译成功应显示：
```
Finished <<< gsl_server [XX.Xs]
Summary: 1 package finished
```

### 第二步：运行单次实验

```powershell
# 清理旧进程
& $SSH $OPT $VM "pkill -9 -f ros2; pkill -9 -f vgr; pkill -9 -f gsl; sleep 1"

# 启动 launch（后台运行，必须用 nohup + &）
& $SSH $OPT $VM "nohup bash /tmp/launch_single.sh OPGSL 0 H01 2,4-1_fast /mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01 -0.9 0.15 > /tmp/gsl_launch.log 2>&1 &"

# 等待 action server 就绪（约 12 秒）
Start-Sleep -Seconds 15

# 验证就绪
& $SSH $OPT $VM "grep 'GSL action server is ready' /tmp/gsl_launch.log"

# 运行 client（阻塞，等待算法完成，超时 120 秒）
& $SSH $OPT $VM "cd /home/zyc/gsl_ws && source install/setup.bash && python3 /tmp/gsl_run_client.py OPGSL 120"

# 读取结果
& $SSH $OPT $VM "cat /tmp/gsl_result.csv"
```

结果格式：`<耗时秒> <定位误差米>`，例如：
```
---------------------------------------------------
18.0629 1.22021
```
表示 18 秒完成，定位误差 1.22 米。

### 第三步：批量实验

```powershell
# 清理旧进程
& $SSH $OPT $VM "pkill -9 -f ros2; pkill -9 -f vgr; pkill -9 -f gsl; sleep 1"

# 启动批量（后台运行，约 2-3 小时）
& $SSH $OPT $VM "nohup bash /tmp/batch_all_v2.sh > /tmp/batch_log_v2.txt 2>&1 &"

# 查看进度（每 5 分钟检查一次）
& $SSH $OPT $VM "cat /tmp/all_results.csv"

# 查看是否还在运行
& $SSH $OPT $VM "ps aux | grep batch | grep -v grep"

# 查看日志尾部
& $SSH $OPT $VM "tail -10 /tmp/batch_log_v2.txt"
```

### 第四步：查看结果

```powershell
# 最终结果
& $SSH $OPT $VM "cat /tmp/all_results.csv"
```

结果 CSV 格式：
```
method,house,seed,distance,time_s,status
OPGSL,H01,0,1.22021,18.0629,OK
PMFS,H01,0,6.32,23.82,SUCCESS
GrGSL,H01,0,1.70,300,TIMEOUT
```

## launch_single.sh 参数说明

```bash
bash /tmp/launch_single.sh <METHOD> <SEED> <HOUSE> <CONFIG> <DATA_PATH> <START_X> <START_Y>
```

| 参数 | 说明 | 示例 |
|------|------|------|
| METHOD | 算法名 | OPGSL / PMFS / GrGSL / surge_cast |
| SEED | 随机种子 | 0 / 1 / 2 / 3 / 4 |
| HOUSE | 数据集 | H01 / H02 / H03 |
| CONFIG | GADEN 配置 | 2,4-1_fast / 3,5-1_fast / 1-2,5_fast |
| DATA_PATH | 数据集路径 | /mnt/hgfs/.../House01 |
| START_X | 起点 X | -0.9 |
| START_Y | 起点 Y | 0.15 |

## 常见问题

### Q: SSH 命令超时
**原因**：`nohup ... &` 在 SSH 中不会正确后台化。
**解决**：launch 必须先用 `nohup ... &` 启动，然后单独执行 client。

### Q: 编译报错 "undefined reference to main"
**原因**：CMakeLists.txt 中 OPGSL 库链接问题。
**解决**：重新 `colcon build --packages-select gsl_server`，不要用 `colcon build`。

### Q: 所有 seed 结果完全相同
**原因**：算法的 `chooseGoalAndMove()` 从未被调用，只是随机游走。
**解决**：确认 OPGSL.cpp 中有 `OnCompleteNavigation` override。

### Q: gas_hits 始终为 0
**原因**：算法绕过了 `StopAndMeasureState`，没有收集气体数据。
**解决**：确认 `OnCompleteNavigation` 中有 `stateMachine.forceSetState(stopAndMeasureState.get())`。

### Q: "Node has already been added to an executor"
**原因**：在 action 回调中直接调用 `chooseGoalAndMove()` → `sendGoal()` → 嵌套 spin。
**解决**：使用 `need_next_goal_` 标志，在 `OnUpdate()` 中延迟调用。

## 实验结果

### VGR House01-03 Fair Comparison (No Ground-Truth Leakage, 2026-06-30)

| 方法 | Overall Error | SR@1m | 备注 |
|------|--------------|-------|------|
| PMFS | 5.65±3.92m | 27% | 内部仿真，不依赖传感器 |
| GrGSL | 3.94±3.12m | 13% | 梯度追击 |
| SurgeCast | 3.71±2.90m | 20% | 十字扫描 |
| Ours | 6.93±3.12m | 7% | 前向模型 + 两阶段 |

> 注意：之前报告的 GrGSL 0.21m 存在 ground-truth 泄漏（导航用了真值源位置），已修正。

### GADEN Env A (Pre-computed Grid, 10 seeds)

| 方法 | Error | SR@1m | 备注 |
|------|-------|-------|------|
| GrGSL | 0.52±0.35m | 90% | 梯度追击 |
| Ours | 1.07±0.46m | 30% | 前向模型 + 两阶段 |
| PMFS | 1.77±0.74m | 20% | 内部仿真 (model-mismatch) |
| SurgeCast | 6.18±0.36m | 0% | 固定风向假设 |

## 算法模块

| 模块 | 功能 | 来源领域 |
|------|------|---------|
| WR-SFE | 非参数 KDE 场估计 | 统计学 |
| WA-IG | 风场信息增益探索 | 信息论 |
| Chemotaxis | 加权质心梯度跟随 | 生物学（细菌趋化性） |
