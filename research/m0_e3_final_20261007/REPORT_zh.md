# M0 E3 完整 40 条冻结科学判决

**判决：`M0_STOP`。** E3 新增 28 条全部合格，累计科学运行恰好 40/40；无重试、补 seed、新源或额外仿真。所有资格通过后才调用原 R0 `gate_logic.py`。已停止。

本受控二候选源机制箱出现前向羽流/传感器变化，但未达到冻结的源后验损伤差异门。不能将此 null 外推为复杂湖岸的 transport uncertainty 不重要；也不能用前向差异、BMA、NLL 或其他 secondary 改判。FSR 数据集建设独立继续。

## 主判决证据

固定 U0 观测，对同一测试 master seed 同时排除两个候选源、所有五个 wind 的该 seed，只用其余三个建立模板。两类 likelihood 参数、0.1 ppm hit threshold、20–120 s 的 51 点、uniform prior、variance floor、同方向/同 seed 交集、每源 3/4、material 0.10 与 absolute harm 0.05 门均未修改。BMA 四个 wrong models 等 prior，排除 U0，未进入主 gate。

| Pair | 最大绝对 ΔD_F | 最大绝对 ΔD_Y | 最大绝对 ΔBrier HIT | 最大绝对 ΔBrier LOG | 同方向完整交集 |
|---|---:|---:|---:|---:|---|
| A | 0.462346508 | 0.351838181 | 8.84506939e-08 | 0 | 1: S0 0/4, S1 0/4；-1: S0 0/4, S1 0/4 |
| B | 0.271911749 | 0.151390561 | 3.82605025e-13 | 0 | 1: S0 0/4, S1 0/4；-1: S0 0/4, S1 0/4 |

两个 pair 在两种预允许方向、两源和两 family 中，达到 ≥0.10 的 material posterior difference 的 seed 集合全部为空；不存在 ≥3/4 的单-source/family 重复效应，因此也不符合 M0_PARTIAL_HOLD。`FINAL_GATE_INPUTS.json` 和 `FINAL_DECISION.json` 保留全部门输入/逐方向交集。

## 完整后验、排序和定位结果

| Family | Model | 正确 / 8 | 最小 p_true | 最大正 Brier damage vs U0 |
|---|---|---:|---:|---:|
| HIT_FORWARD | U0 | 8/8 | 0.999999951429 | 0 |
| HIT_FORWARD | A_on | 8/8 | 0.999702593386 | 8.84506939299e-08 |
| HIT_FORWARD | A_off | 8/8 | 0.999999951429 | 0 |
| HIT_FORWARD | B_shear | 8/8 | 0.999999919049 | 4.19396491589e-15 |
| HIT_FORWARD | B_speed | 8/8 | 0.999999380477 | 3.82605025243e-13 |
| HIT_FORWARD | WRONG_MODEL_BMA | 8/8 | 0.99999956471 | 1.89164369329e-13 |
| LOG_GAUSSIAN | U0 | 8/8 | 1 | 0 |
| LOG_GAUSSIAN | A_on | 8/8 | 1 | 0 |
| LOG_GAUSSIAN | A_off | 8/8 | 1 | 0 |
| LOG_GAUSSIAN | B_shear | 8/8 | 1 | 0 |
| LOG_GAUSSIAN | B_speed | 8/8 | 1 | 0 |
| LOG_GAUSSIAN | WRONG_MODEL_BMA | 8/8 | 1 | 1.77493703675e-30 |

所有单 wind 后验和 BMA 的 true-source rank=1、MAP error=0。完整 96 行后验表保留 p、原始 candidate log evidence、NLL、scaled Brier、D_B、TV、rank/tie、MAP error 和 posterior-mean error。LOG_GAUSSIAN 的 p_true=1 是浮点饱和的 posterior score，不能解读成真实世界确定性或概率校准；原始 log evidence 和另一 candidate 概率仍保留。四个 master seeds 才是独立随机区组，两源不形成八个独立环境。

## 资格、原始证据和随机配对

- 原 R0 39 文件、E1/E2 证据及原 native manifests 在运行前后保持相同 SHA256；原 runlist 的 launch_authorized=False 未改动，另建授权清单，严格扣除已完成 12 行得到 28 行。review commit=635903e6ab99aa84612aee390a280a21b1884efd。
- 实际 generator/libgaden/source/MathUtils/PointSource、native decoder/旧 helper 哈希保持冻结。所有 28 sim.yaml 与相应 U0 原 YAML 字节相同，只替换已冻结的 wind input location。继续使用原生 project/YAML 入口，未使用有温压绑定缺陷的旧 ROS 参数入口。
- 全 40 条六面支撑、零删除、无位置异常、同 source/seed 的 clock/record/count/sigma/出生顺序、Gaussian table/call assignment 和 native sampling 均通过。每条 246 saved records，共 9,840；原生 1,401 ticks、terminal 140.09934997558594 s，20–120 s 对齐窗口及 max lag≤0.61 不变。
- 全 bank 最小 3σ outlet margin=6.62297697067 m；centroid/source clearance 原门均通过。每个 seed 四个错误风场与其 U0 对齐，零删除为 pinned-source、release/sigma 与保存间隔/terminal 位移界的控制流证书，不是 instrumented per-tick deletion/RNG counter。
- Native wind 实际 readback 与 5 个冻结字段 SHA256 相同；finite/speed/divergence 与 Free+ROI matched-RMSE 全部通过。独立 checker 从实际 f32 arrays 再计算两个 volume 的 RMSE。
- 主 ROI 浓度 parity=102,000 queries，difference=0。另补齐 R0 已规定的 120×80 whole-domain secondary native columns：40×51=2,040 张，47 个 Free z samples 积分，ROI crop 与原 primary columns 逐字节一致；其另 102,000 direct native checks 差值也为 0。没有保存 full-3D time-volume bank，没有添加气体运行。全域提取只读旧 snapshot，原有 route/state readback 字节一致；重复诊断 dumps 在 VM 单独保留，归档用原始 bank 去重表示。
- 前向 D_F/D_Y、arrival/detection、centroid/spread、total/ROI/outside mass、每面 band、逐record 3σ margin 全部保留；secondary 和 BMA 不救主门。

## 独立复核与资源

独立 checker 使用 scalar Bernoulli/手工 sample variance、显式 exponent normalization 和独立 gate arithmetic，不导入主 likelihood 或 gate；稳定 erfc 检查 Gaussian 支撑尾部。原始 14,779 项 file hashes、39 R0 hashes、候选/seed 排除、matched RMSE、全部 raw clock/sigma/native parity、full common-direction seed intersections 全部通过，独立判决同为 `M0_STOP`。
posterior max diff=1.33226762955e-15；likelihood max diff=3.97903932026e-13；forward max diff=2.77555756156e-17；BMA weight max diff=2.33146835171e-15；support margin diff=0。

E3 scientific+extraction+逐条资格 campaign wall=65.2826862 s，40 条 simulation+extraction 合计=47.5382833 s；40 条 simulation/ROI extraction 最大 native RSS=127860736 bytes；VM raw root=1074670575 bytes，3 h/5 GiB/2 GiB 及 12/3 GiB preflight/post 门通过。这是当前解析风场原生机制箱的开销，不是 FSR CFD 成本或 PMFS 加速结果。

## 数据定位与停止边界

`ALL40_INDEX.json` 和 `ORIGINAL_TO_ARCHIVE_HASHES.csv` 映射旧 E1/E2、新 E3 每个原始文件至不改字节的 bank。六个 `M0_NATIVE_*.zip` 是完整、不重叠的原始归档；包含全部 iterations、filament states、route/ROI/global columns、parity、实际 inputs/readback、runtime/source/hash/argv/env/time/RSS、原始 logs、预运行代码 seal 与冻结副本。native ZIP CRC 和每 member hash 在 VM 与回传端均复核。
原 E2 时间文本误报及勘误原样保留于父提交；E3 在运行前已按 native float32 比较并通过原 12 条历史记录，没有根据新结果修补资格或打破冻结。

**执行科学 STOP。** 不降低门、不补 seeds/候选源/路线、不加 NN、不重跑或继续挖本箱来救路线。本结果没有证实足以进入 FSR 的 transport-error-to-source-posterior damage 机制；FSR 湖岸 CFD/气体扩散数据集按独立主线继续建设。

Linux 从新 ZIP 副本复算：原 freeze、主评价、独立 checker、global/ROI crop checker 四项均 exit=0，判决同为 M0_STOP，没有调用 native executable 或新 simulation。环境 Python 3.10.12、NumPy 1.26.4、SciPy 1.8.0；既有版本范围 warning 保留在日志，未更换依赖。见 LINUX_FINAL_REPLAY_VERIFICATION.json 与 linux_replay_logs/。

补充 whole-domain native extraction 的实测最大 RSS=117641216 bytes，也通过 2 GiB 门；SECONDARY_RESOURCE_AUDIT.json 与全部 time.txt 保留。
