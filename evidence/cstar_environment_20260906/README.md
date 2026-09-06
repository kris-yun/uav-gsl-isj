# CSTAR 三屋环境执行审计 — 2026-09-06

## 结论

`CSTAR_ENVIRONMENT_ALIGNMENT=PASS`，限于真实共享输入 loader 和预注册静止 endpoint+dwell。

本轮已完成交接方案的第一优先级：三屋环境 gate。**没有完成 M1/M2 科学验证，
没有启动模型训练、生产 smoke 或 A0/F00/F10/F11 的 12-run。** 这里交回环境审计
检查点，不把环境 PASS、可用原始文件、或代码回归当作模块收益。

## 实际执行

- 起点：GitHub 分支 `g3-cstar-revise-before-exec-20260906` 的 `82f3491`。
- 三屋 runtime 代码提交：`88701c7a2e7e62e93c5bf6475702ffd9ef9603ba`。
- VM：`/home/zyc/CSTAR_ENV_ALIGN_20260906`；Python 3.10.12，Torch 2.12.1+cpu。
- 起点和加强后整套回归都通过，完整 stdout/stderr 保存在 `selftest_*.log`。
- 旧 VM checkout 和它的 bundle origin 未修改；只在新目录恢复易失的 H01 查询程序。
  其编译结果和原始源码 SHA 见 `raw_query_build.log`。
- H02/H03 使用持久化 player，二进制 SHA 和真实命令见各屋 `run_status.json`。
  这是明确记录的依赖恢复，不声称其数值输出与所有旧二进制完全等价。

## 三屋统一规则

从各 House 的 `OccupancyGrid3D.csv` 导出 z=0.3 m 切片；0.1 m 分辨率，
同一数组轴和图像 Y 翻转规则。实际 VGR `/map` 的每个栅格与 PGM 比较通过。

| House | 地图尺寸 | 地图 origin (m) | 全自由格候选数 | 实际正时间观测 |
| --- | --- | --- | ---: | ---: |
| H01 | 87 × 114 | (-7.55, -7.88) | 6866 | 8 |
| H02 | 83 × 119 | (-5.39273, -7.45088) | 6811 | 8 |
| H03 | 138 × 83 | (-0.85, -1.863) | 7258 | 8 |

所有候选中心、真实风观测位置、冻结 endpoint 均落在自由格内。候选由几何生成，
未按源真值或气体观测筛选。未来 producer 必须绑定这些候选文件，不能以旧路线
外包矩形代替后仍沿用本次 gate。

每屋先验证 t=0 bootstrap 和 map parity，再释放自己的 paused simulator；
记录 t=0,0.2,...,1.6 s 共 9 帧。t=0 的零风不计作观测，wind CSV 只含 8 帧。
风由真实 Anemometer 直接 downwind 解码，不加 π、不经过 GMRF、不用稍后的 TF。
与 bridge 的原始 downwind 日志交叉核验，最大差异 4.99954e-7 m/s，
位于日志六位小数舍入误差内；坐标和导航高度也核对通过。

## 重要边界

1. route 是运行前冻结的旧 R4 seed12 起点 + 1.6s hover，只证明静止点和输入链。
   不证明一般路径安全、复杂 planner 路由或闭环收益。
2. A0/F00/F10/F11 shared identity 是今后四臂必须遵守的输入绑定合同。
   本轮未运行这四个科学臂，不能称“四臂生产接线全部验证”。
3. probe 证明实际 VGR map 与冻结地图一致，不证明未来所有生产 loader 已改完。
4. 没有重跑 GMRF，也没有提升其预测 RMSE 的新结论。
5. H02 bridge 日志尾部有本脚本主动清理进程后产生的 ROS context shutdown 异常。
   保留原文；它发生于 probe 成功退出后的收尾，不是缺帧或仿真观测错误。
6. 本轮未读写保护 bank，也未改变旧算法、风场求解器或 House 原始几何。

## 方案哪些地方需要纠正

环境优先顺序正确，但起点代码仍只接受 inline YAML origin，runtime audit 可以在
没有有效帧的情况下被 validator 接受，probe 只给 CLI 文件算哈希而未比较 ROS map。
已修复并增加反例回归。新增超时/失败输出、真实地图逐格匹配、8 个正时间样本和
raw JSONL/CSV 绑定；失败 audit、错误 git/帧数、替换的 wind CSV 现在会被拒绝。

## 受控科学验证的真实状态

目录审计发现每屋两处源位置，各有 fast/slow，共 12 个原始 realization 目录，
每个有 2000 个 iteration 文件和 11 个 wind 文件。**这是文件名/数量盘点，
不是同源干预身份的物理验证，更不是 controlled asset PASS。**

本轮还没有生成满足新合同的受控历史、decision-locked route outcomes 和冻结 split。
因此没有执行正式 controlled validator，也没有训练网络。详见
`CONTROLLED_ASSET_STATUS.json`，其科学状态为 NOT EVALUATED 而不是 NO-GO。

下一阶段应先审核原始 realization 的源/释放/输运身份、锁定整 realization split
和 truth-blind controlled route，再采集受控输入；不得把本次 1.6s hover 或历史
自适应轨迹直接改名为 M1/M2 正式证据。

## 证据与复核

- `CSTAR_ENVIRONMENT_ALIGNMENT_V1.json`：所有真实输入的路径、SHA、几何和共享合同。
- `CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json`：三屋统一 validator 输出。
- `maps_v1/`：真实导出地图、候选/endpoint CSV、3D geometry SHA。
- `probes_v1/H0*/`：实际 runtime audits、原始观测、bridge/player 日志与执行命令。
- `BRIDGE_TO_INGRESS_CROSSCHECK.json`：独立的风向量/坐标/时间核验。
- `source_snapshot/`：实际执行输入链、导出器和验证器的原始字节快照。
- `CONTROLLED_PREREQUISITE_INVENTORY.json`：只读原始数据盘点。

完整本地离线复核（不需要 ROS，不改原证据）：

```bash
python tools/cstar_reverify_environment_bundle.py --output /tmp/cstar_environment_reverify.json
```

该工具显式重定位 VM 路径，按归档源码和 raw SHA 重验；不是重新跑 ROS。
本目录禁用 Git 换行转换，防止 Windows 改写 CSV 后使科学证据 SHA 失效。
