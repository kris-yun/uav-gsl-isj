import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,shutil,hashlib,numpy as np
W=Path(__file__).resolve().parent;root=W.parents[2]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/boundary_point_experiment'
rows=list(csv.DictReader((root/'PAIRWISE_FACTORIAL_EFFECTS.csv').open(encoding='utf-8')));s=list(csv.DictReader((root/'FORWARD_SCORE_AND_SUPPORT.csv').open(encoding='utf-8')));mv=list(csv.DictReader((root/'MOVEMENT_PHASE_SUMMARY.csv').open(encoding='utf-8')))
def table():
 lines=['| 源表示 | 障碍物响应 | T 错/真评分比 | W 错/真评分比 | 选择 |','|---|---|---:|---:|---|']
 for form,bound in [('uniform','native'),('uniform','slide'),('point','native'),('point','slide')]:
  z=[x for x in rows if x['source_form']==form and x['boundary']==bound];lines.append(f'| {form} | {bound} | {float(z[0]["wrong_over_true_score"]):.3f} | {float(z[1]["wrong_over_true_score"]):.3f} | 两状态均为错误 K2 |')
 return '\n'.join(lines)
ledger=json.loads((root/'EXECUTION_LEDGER.json').read_text());build=json.loads((root/'BUILD_RESULT.json').read_text())
report=f'''# M3 源表示 × 障碍物边界规则：新物理对照

## 本轮问题与结论

只判断两个具体原因是否足以解释 B4 真/错候选的错误评分偏好：源叶内均匀释放是否偏离实际点释放，以及遇墙停滞是否使真源羽流不能到达关键观测区域。本轮新增 12 次二维前向，另做 2 个必要原生锚点。旧 4 份 uniform/native 预测直接复用，不重复生成。没有新的 GADEN、CFD、ROS 初始化、导航、后验更新或种子。

明确结果：**两个因素均有数值影响，但都不足以翻转错误源偏好；组合干预后，两固定随机状态仍分别偏向错误源约 1,598 和 2,292 倍。** 这是一项完成的否证结果，不以“继续 HOLD”替代现有结论。它否证的是“这两项最小修正即可解释掉错误偏好”的充分性，不能证明壁面效应在所有任务均无作用。

{table()}

比值是本轮原生 447 格乘积评分的单格候选比；两个候选均 1×1 等面积。它不是经过标定的物理似然比，也不是新后验或闭环定位成绩。

## 代码中的实际动力学差异

PMFS `Simulations::moveAlongPath()` 锁定的 `USE_DDA=0` 分支，用半格最大步长推进，步数为 `int(distance / stepSize)`；遇占据格就退回最后一个步长，立即结束本次移动。上游源码另有明确注释希望以后实现壁面偏转。GADEN `RunningSimulation::StepTowards()` 则以 `previousCell-currentCell` 构造法向，将剩余位移去掉法向分量并递归推进；其原生遍历步数为 ceil，且包括 3D 出口语义。

本轮仅将 GADEN 的**切向投影思想**加入 PMFS 已有障碍回退分支，保留 PMFS 的 floor 步数、free/visibility 快路径及越界删除。**不是把完整 GADEN 的 StepTowards 移植为二维，也没有顺带改变步长、出口或风场。** 深度32保护所有运行触发次数均为0，非法起始格次数均为0。点源使用上游原生 `SimulationSource::Point`，另外补齐点写出钩子，不触发 uniform 抽样；固定点采用原源码 float32 世界坐标。

## 机制量化

T 状态真源 uniform/native 记录段有 299,603 次粒子移动，其中 136,553 次位移严格为零，比例45.58%；相同起始随机状态的 uniform/slide 为 275,526 次移动、零位移0。切向干预确实消除了大部分原生壁面停滞，不是没有作用的假补丁。与此同时，真源预测原始非零自由格从110增至127，平均自由格命中率从0.13853增至0.17962，真源评分约增加3.05倍；错误源评分只增加约1.02倍。**干预改变了输运支撑，却仍留下约5,868倍错误偏好。** W 状态得到相同方向：约20,181倍降至约6,207倍。

Point/native 对真源评分几乎没有改变：T 约4.182e-10→4.348e-10，W 约3.824e-10→3.844e-10；错误源评分下降更明显，T约7.339e-6→2.872e-6，W约7.717e-6→3.847e-6。**1×1 区域内部源混合影响较大，但真源自身的低预测评分不能靠精确点释放恢复。** Point+slide 联合后真源评分仍低于错误源，故不能把叶内采样或遇墙停滞选作本次错误定位的单一主根因。

## 随机性及比较边界

T/W 是此前原生已保存的两个 engine 状态与2500元素高斯表相位（5、2425），不是新增独立物理种子。各对照起始状态相同；粒子存活路径变化后，后续高斯抽样与粒子身份不再逐事件配对。点模式不调用 uniformRandomF，原生 uniform 模式仍按原来次序调用。此处不能把“两状态结果一致”写成跨独立气体实验的统计复现。两源及精确点均由已知 B4 结果选取，属于 oracle 根因诊断，不能部署或用于新算法性能宣称。

## 验证与资源

2个新锚点逐字节复现了旧 M1 的 blurred/unblurred 命中图、2000个释放点，以及初末 RNG 与高斯相位；评分也一致。其后12次前向均正常返回。所有新图用冻结 B4 测量图和原生评分公式独立复算，相对容差3e-13内与 C++ 结果一致。

前向合计{ledger['forward_wall_seconds']:.6f}秒，峰RSS {ledger['peak_RSS_bytes']:,}字节，低于120秒/512MiB；隔离编译{build['wall_seconds']:.3f}秒、峰RSS {build['max_RSS_bytes']:,}字节，低于180秒/1.5GiB。前向后目录大小{ledger['new_remote_disk_bytes']:,}字节，低于200MB。可执行SHA256：`{build['executable_sha256']}`。

## 可交给 PRO 的决策

1. 壁面停滞是已证实的 2D 原生动力学现象，切向干预能缓解并扩大真源预测覆盖；但本轮错源偏好没有消失，故不能把它单独定为主要物理失败机制。
2. 粗叶5×1影响已经在M1控制；本轮进一步控制1×1内部源混合和精确点释放，仍不能解释掉真源低评分。
3. 下一解释应使用同一3D粒子路径上的有限宽度浓度核/中心格事件读出对照，并结合评分语义与空间传播证据分析；这两项应与本轮完成的否证放在一起，而不是继续重复源区域实验。
4. 本轮没有运行完整PMFS更新或导航；所有历史官方成功、错误位置收敛和STOP判决保持冻结。

## 文件索引

- `FACTORIAL_RESULT.json`：完成判决与8个配对比值。
- `FORWARD_SCORE_AND_SUPPORT.csv`：16候选条件的评分、预测覆盖和置信加权误差。
- `PAIRWISE_PER_CELL_DIFFERENCES.csv`：每种条件每个自由格对错误源偏好的贡献。
- `MOVEMENT_PHASE_SUMMARY.csv`、原始 `MOVEMENT_CELL_AGGREGATES.csv`：warmup/record拆分的移动、遇墙、零位移统计。
- `forward_calls/`：2锚点+12新调用完整图、释放点、相位与评分。
- `reused_M1/`：4原生预测只读副本。
- `Simulations_boundary_diagnostic.cpp`、`candidate_forward.cpp`、`M3Audit.hpp`：隔离源码。
- `GADEN_RunningSimulation_original.cpp`：实际 GADEN 壁面响应源码。
- `EXECUTION_CONTRACT.json`：与父合同和可执行hash绑定、执行前冻结的子合同。

采集归档曾因在gzip关闭前读BytesIO导致本地解压报EOF；已修正归档关闭顺序后只重新读取输出，**没有重进任何 forward**。两个派生分析脚本的本地格式问题也在全部前向结束后修正，未改变任何模拟资产。
'''
dest=root/'BOUNDARY_POINT_CAUSAL_REVIEW_zh.md';assert not dest.exists();dest.write_text(report,encoding='utf-8')
for n in ['analyse.py','write_report.py']:
 assert not (root/n).exists();shutil.copy2(W/n,root/n)
print(dest)
