# UAV-GSL ISJ 项目

## 目标期刊
IEEE Sensors Journal (ISJ)

## 科学问题
低风速环境下PMFS概率地图收敛失败导致UAV气体源定位误差增大

## 方法概述
在MAPIRlab官方PMFS算法基础上，增加3个跨领域创新模块：
1. PWC - 羽流风向校正（大气污染源反演）
2. PSDE - 羽流空间色散估计（P-G大气扩散模型）
3. SDR - 源概率图反卷积精化（医学CT重建）

## 目录结构
```
uav-gsl-isj/
├── README.md              # 本文件
├── code/
│   ├── src/               # 修改后的C++源文件
│   │   ├── PMFS.cpp
│   │   ├── PMFS_utils.cpp
│   │   └── PwcCorrector.cpp
│   ├── include/           # 头文件
│   │   ├── PwcCorrector.hpp
│   │   └── Settings.hpp
│   └── launch/            # ROS2 launch文件
│       └── vgr_gsl_unified_ablation.launch.py
├── data/                  # 实验结果数据
│   ├── House01/
│   ├── House02/
│   └── House03/
├── results/
│   ├── raw/               # 原始server/traj CSV
│   └── analysis/          # 统计分析结果
└── docs/
    ├── SCIENTIFIC_PROBLEM.md
    ├── MODULES.md
    ├── EXPERIMENT_DESIGN.md
    └── DELIVERY.md
```

## 实验配置
- 数据集: VGR (House01/02/03)
- 基线: PMFS (MAPIRlab官方)
- 消融: baseline / +PWC / +PSDE / +PWC+PSDE / +SDR / full
- 每条件: ≥10 seeds, matched seeds
- 统计: Wilcoxon配对检验, bootstrap 95% CI, Cohen's d

## VM环境
- IP: 192.168.111.128
- ROS2 Humble
- 代码路径: ~/ros2_ws/src/GSL/gsl_server/
- Launch: ~/ros2_ws/src/vgr_bridge/launch/vgr_gsl_unified_ablation.launch.py
