# ISJ Benchmark 实验运行文档

## 概述
- 目标期刊：IEEE Sensors Journal (ISJ, IF ~3.4)
- 实验日期：2026-07-08
- 总运行数：160次（4场景 × 4方法 × 10种子）
- VM地址：zyc@192.168.111.128 (密码: 123456)

## 场景配置

| 场景 | House | Config | 源位置(x,y,z) | 起点(x,y) | 类型 |
|------|-------|--------|---------------|-----------|------|
| H01_gnd | House01 | 2,4-1_fast | (-0.40, -2.90, -0.30) | (0.30, -1.20) | 地面源 |
| H01_air | House01 | 1,3-2,4_fast | (-0.60, 1.95, 0.40) | (-0.90, 0.15) | 空中源 |
| H02_air | House02 | 3,5-1_fast | (0.00, -1.00, 0.20) | (-0.50, -2.50) | 空中源 |
| H03_gnd | House03 | 1-2,5_fast | (-0.45, 1.90, -0.10) | (2.00, 0.00) | 地面源 |

## 方法配置

### OPGSL（本文方法）
```bash
ros2 launch vgr_ablation.launch.py \
  vgr_data_path:=<data_path> config_id:=<config> \
  algorithm:=OPGSL method:=M7_full_saisc_pf \
  source_x:=<sx> source_y:=<sy> source_z:=<sz> \
  start_x:=<stx> start_y:=<sty> seed:=<seed> timeout_sec:=300 \
  use_sbd:=false opgsl_ddm:=false opgsl_wraig:=false \
  opgsl_cp:=true opgsl.event_driven.enabled:=true
```

### SurgeCast
```bash
ros2 launch vgr_gsl_pmfs.launch.py \
  vgr_data_path:=<data_path> config_id:=<config> \
  algorithm:=SensorAwareSurgeCastPF method:=B0_surge_cast_official \
  source_x:=<sx> source_y:=<sy> source_z:=<sz> \
  start_x:=<stx> start_y:=<sty> seed:=<seed> timeout_sec:=300
```

### GrGSL
```bash
ros2 launch vgr_gsl_pmfs.launch.py \
  vgr_data_path:=<data_path> config_id:=<config> \
  algorithm:=GrGSL method:=B5_GrGSL_official \
  source_x:=<sx> source_y:=<sy> source_z:=<sz> \
  start_x:=<stx> start_y:=<sty> seed:=<seed> timeout_sec:=300
```

### PMFS（确定性，每场景只跑一次）
```bash
ros2 launch vgr_gsl_pmfs.launch.py \
  vgr_data_path:=<data_path> config_id:=<config> \
  algorithm:=PMFS method:=B4_PMFS_official \
  source_x:=<sx> source_y:=<sy> source_z:=<sz> \
  start_x:=<stx> start_y:=<sty> seed:=0 timeout_sec:=300
```

## 数据路径
- House01: `/home/zyc/vgr_data_scenarios/House01`（无子目录）
- House02: `/home/zyc/vgr_data_scenarios/House02/House02`
- House03: `/home/zyc/vgr_data_scenarios/House03/House03`

## 运行脚本
- 主脚本：VM `/tmp/run_isj_v3.py`（跳过PMFS，3方法×4场景×10种子=120次）
- PMFS脚本：VM `/tmp/run_pmfs.py`（PMFS确定性，4场景各1次）
- 结果文件：VM `/tmp/v8_exp/isj_full/results.csv`

## 结果解析
- 从ros2 launch输出中grep `final_error=` 行
- 格式：`final_error=X.XXX localized2=Y timeout=Z`
- 成功判定：`final_error < 2.0m`

## 已知问题
1. PMFS需要GMRF wind estimation服务，已添加GMRF节点到launch文件
2. GMRF风速阈值从0.01改为0.001（GADEN室内风速很低）
3. PMFS是确定性算法，seed不影响结果
4. benchmark_runner有时崩溃，从GSL server日志提取结果

## 代码版本
- VM代码commit：9d819d3（GBI框架+双向cross-wind）
- Launch文件已修改：PMFS launch添加了GMRF节点和useWindGroundTruth:=false
- vgr_sim_node已修改：wind frame_id保持为'map'
