# OPGSL 实验运行手册

## 概述
- 方法名称：OPGSL (Optimal-Path Gas Source Localization)
- 理论框架：GBI (Generalized Bayesian Inference)
- 目标期刊：IEEE Sensors Journal (ISJ, IF ~3.4)
- 最后更新：2026-07-08

## 环境要求
- **VM**: zyc@192.168.111.128 (密码: 123456)
- **ROS2**: Humble
- **工作空间**: /home/zyc/gsl_ws/
- **代码仓库**: https://github.com/kris-yun/uav-gsl-isj.git

## 代码结构

### 核心文件
`
/home/zyc/gsl_ws/src/GasSourceLocalization/
├── gsl_server/src/gsl_server/algorithms/OPGSL/
│   ├── OPGSL.cpp          # 主算法实现 (1602行)
│   ├── OPGSL.hpp          # 类定义
│   ├── CP_Stopping.hpp    # E-Process停止规则
│   ├── DDM_Stopping.hpp   # DDM停止规则
│   ├── WATS_GSL.hpp       # 场估计+信息增益
│   └── ...
├── vgr_bridge/launch/
│   ├── vgr_ablation.launch.py    # OPGSL launch
│   └── vgr_gsl_pmfs.launch.py    # 基线方法 launch
└── ...
`

### Launch文件
- **OPGSL**: gr_ablation.launch.py
- **SurgeCast/GrGSL/PMFS**: gr_gsl_pmfs.launch.py

## 数据集

### GADEN数据集
- 来源: https://zenodo.org/records/10842409
- 本地路径: /home/zyc/vgr_data_scenarios/

### 场景配置
| 场景 | House | Config | 源位置(x,y,z) | 起点(x,y) | 类型 |
|------|-------|--------|---------------|-----------|------|
| H01_gnd | House01 | 2,4-1_fast | (-0.40, -2.90, -0.30) | (0.30, -1.20) | 地面源 |
| H01_air | House01 | 1,3-2,4_fast | (-0.60, 1.95, 0.40) | (-0.90, 0.15) | 空中源 |
| H02_air | House02 | 3,5-1_fast | (0.00, -1.00, 0.20) | (-0.50, -2.50) | 空中源 |
| H03_gnd | House03 | 1-2,5_fast | (-0.45, 1.90, -0.10) | (2.00, 0.00) | 地面源 |

**注意**: House01数据直接在根目录；House02和House03有嵌套子目录 (e.g., House02/House02/)

## 运行方法

### 1. OPGSL（本文方法）
`ash
source /opt/ros/humble/setup.bash
source /home/zyc/gsl_ws/install/setup.bash

ros2 launch vgr_bridge vgr_ablation.launch.py \
  vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
  config_id:=2,4-1_fast \
  algorithm:=OPGSL \
  method:=M7_full_saisc_pf \
  source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
  start_x:=0.30 start_y:=-1.20 \
  seed:=0 timeout_sec:=300 \
  use_sbd:=false opgsl_ddm:=false opgsl_wraig:=false \
  opgsl_cp:=true opgsl.event_driven.enabled:=true
`

### 2. SurgeCast
`ash
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
  vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
  config_id:=2,4-1_fast \
  algorithm:=SensorAwareSurgeCastPF \
  method:=B0_surge_cast_official \
  source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
  start_x:=0.30 start_y:=-1.20 \
  seed:=0 timeout_sec:=300
`

### 3. GrGSL
`ash
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
  vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
  config_id:=2,4-1_fast \
  algorithm:=GrGSL \
  method:=B5_GrGSL_official \
  source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
  start_x:=0.30 start_y:=-1.20 \
  seed:=0 timeout_sec:=300
`

### 4. PMFS（确定性，每场景只跑一次）
`ash
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
  vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
  config_id:=2,4-1_fast \
  algorithm:=PMFS \
  method:=B4_PMFS_official \
  source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
  start_x:=0.30 start_y:=-1.20 \
  seed:=0 timeout_sec:=300
`

## 批量实验脚本

### ISJ完整基准测试 (160 runs)
`ash
# 在VM上运行
python3 /tmp/run_isj_v3.py
`

### 结果解析
`ash
# 从日志提取结果
grep "final_error=" /tmp/v8_exp/isj_full/*.log | sed 's/\x1b\[[0-9;]*m//g'
`

## 结果文件
- **VM**: /tmp/v8_exp/isj_full/results.csv
- **本地**: D:\ZYC\A-gas\experiment_results\results_raw.csv
- **汇总**: D:\ZYC\A-gas\experiment_results\summary_stats.csv

## 已知问题
1. PMFS需要GMRF wind estimation服务，已添加GMRF节点到launch文件
2. GMRF风速阈值从0.01改为0.001（GADEN室内风速很低）
3. PMFS是确定性算法，seed不影响结果
4. benchmark_runner有时崩溃，从GSL server日志提取结果

## 代码版本
- VM代码commit: 9d819d3 (GBI框架+双向cross-wind)
- Launch文件已修改: PMFS launch添加了GMRF节点和useWindGroundTruth:=false
- vgr_sim_node已修改: wind frame_id保持为'map'

## 算法参数说明

### OPGSL核心参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| opgsl.convergence.entropy_threshold | 4.0 | 后验收敛熵阈值 |
| opgsl.convergence.min_bouts | 5 | 最小bout数 |
| opgsl.convergence.stable_steps | 5 | 连续稳定步数 |
| opgsl.convergence.min_time | 30.0 | 最小运行时间(s) |
| opgsl.cp.enabled | true | E-Process停止规则 |
| opgsl.ddm.enabled | false | DDM停止规则 |
| opgsl.wraig.enabled | false | Wasserstein信息增益 |

### 检测模型参数
- 检测函数: Logistic P(d) = 1/(1+exp(γ(d-d0)))
- d0 = 1.5m (检测半径)
- γ = 2.0 (灵敏度)
- 自适应η: detected [0.6, 0.9], non-detected [0.15, 0.5]
