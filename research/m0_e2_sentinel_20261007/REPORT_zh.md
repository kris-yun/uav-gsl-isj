# M0 E2：四条跨风场 CRN sentinel 资格证据

**判决：`M0_E2_CRN_SENTINEL_QUALIFIED`。本轮实际科学运行恰好 4 条 wrong-wind，新增 U0=0，剩余 28 条=0。已停止。** M0 累计完成 12/40 行；科学机制和 posterior material-effect 均为 `NOT_TESTED`，无 M0_PASS、PRIMARY_GO 或算法优越性主张。

执行依据是用户本轮直接授权，以及 `research/pro-handoff-20261007` 的 `5f71e39717fb7f0c97c039de0152a5da38145610` 中 `M0_E0_E1_REVIEW_AND_E2_SENTINEL_AUTHORIZATION_PLAN_20261007.md`。该 review/plan 自身不授予运行权限。新授权清单只允许 `S0/r01`、seed `2026100701` 的四个冻结 ID；原 40 行 runlist 的 `launch_authorized=False` 未改动。R0 39 份冻结内容及 E1 封存内容均未改动。

## 运行前与实际运行

复核原 E1 全部 2,551 个 native 文件；原 E0 wind、occupancy、源和 gas、release、sigma/noise、时钟、route、runtime/source/helper 哈希均吻合。复用同一 native project/YAML 入口，所有科学 YAML 与 `m0r0_U0_S0_r01` 的原文件逐字节相同；只用各 arm 已在 E0 生成和 decoder 复读的 wind 文件。未重编或改动 generator/libgaden/helper。

Generator SHA256：`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`；libgaden：`d7fe2a08b3df6ddd3c39518f9e5ef75bd394c32509e0402b410db445cb008ee3`；playback helper：`4642c703d1f5d7d279e0b6bcd00e7155bfcae141bbe033070cacc6d8ef9d9350`。

实际 result leaves 均为此前不存在的 `/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e2_sentinel/projects/<arm>/simulations/<frozen_run_id>/result`，位于原合同允许根目录之内。每条新进程、OMP=1；argv/env/原生 effective parameters、ldd、依赖/source/input/output 哈希随包保存。E0 式 readback/噪声检查没有构造或步进 gas simulation。四条完成后 runner 直接停止，无 E3 代码路径或自动重试。

| 指定 run | 记录数 | 最小 3σ outlet margin / m | sigma/出生顺序与 U0 | native parity |
|---|---:|---:|---|---|
| m0r0_A_on_S0_r01 | 246 | 6.622977 | 逐字节一致 | 2,550 次，差值 0 |
| m0r0_A_off_S0_r01 | 246 | 6.622977 | 逐字节一致 | 2,550 次，差值 0 |
| m0r0_B_shear_S0_r01 | 246 | 6.622977 | 逐字节一致 | 2,550 次，差值 0 |
| m0r0_B_speed_S0_r01 | 246 | 6.622977 | 逐字节一致 | 2,550 次，差值 0 |

每个 wind 的实际 native decoder 复读 SHA256 与 E0/冻结合同完全相同。Pair A 的 Free-domain/ROI vector RMSE 分别为 `0.0009048415321811261` / `0.00420284627753083` m/s，两 arms 完全相同。Pair B 分别约 `0.00748490274` / `0.01282847697` m/s，两尺度差值均同时满足绝对≤1e−7、相对≤1e−4；finite、u、speed、vector error、max/RMS divergence 门全部原样通过。完整数值见 `E2_PREQUALIFICATION.json`。

## 跨风场随机配对与六面支撑

四条与已完成 U0 参照的原始 246-record clock、record index、wind index、filament count、offset、出生顺序和全 sigma-age 数组相同。源按 point Emit 固定返回坐标，无随机 retry；固定每 tick 一个 filament。每个 saved record 的 count 等于累计 release count，完整 sigma-age 数组也符合 native float32 Euler 递推。

所有 arms 的 sigma 序列 SHA256：`4bd11b65ed2eafea6639faf8e71656832d3f1df87320da5560ca7f26b98cda39`。实际 seed 对应 1000-entry Gaussian 周期序列 SHA256：`5d4022ce0bb79ec31a27333c8e60b26a59a4988d6e0209a6835c578d1317e3bd`，与 U0 相同；max_abs=3.361870527267456。

每条实际执行 1,401 native ticks，首次越过 140 s 的内部时间为 140.09934997558594 s；最后 saved 时间的文本值为 139.799332 s。20,22,…,120 s 对齐到同一最近先前 record，最大 lag=0.501221 s≤0.61。并未延长、截断或替换 native 时钟。

在 pinned-source、无 obstacle、OMP=1、零异常的原生控制流下，每个 live filament 每 tick 恰好三次 Gaussian draw，累计 2,946,303 次，call assignment 在此 S0/r01 区组四个错误风场和 U0 之间保持一致。这是控制流/不变式证书，不是新插入的逐 tick RNG trace；剩余 28 条自身的运行资格尚未测试。

所有 984 个 sentinel records 的 3σ outlet margin≥6.623 m，centroid clearance≥10.189 m，source clearance=10.75 m。六面的 1 m Gaussian band 各面及并集 mean/q95 原样报告于 CSV；独立稳定 erfc 并集上界给出 window mean≤5.285e−69、q95≤1.880e−71，全 saved records 上界≤6.982e−57，远低于 0.05/0.10 门。主实现并集数值 0 不代表 Gaussian 物理尾部精确为 0。

零删除由每 record 的累计 release deficit=0，以及覆盖全部保存间隔和最后 0.300018 s 尾段的保守位移界确认。使用各实际 wind 的 max speed、实际 Gaussian 表最大值及 CO buoyancy 上界；最大轴向间隔位移界为 0.292781 m，远小于支撑净距。日志无位置/更新异常或隐藏 retry。**删除数证书确认 0；没有直接 instrumented per-tick deletion counter。**

source-blind route 的坐标、请求时间和选取的 record 与 U0 参照完全一致。真实观测继续绑定原 U0 route，SHA256 `fabd22992ebdbf867aac088ffb506c35bcb31a0c6043270aa62db93c3e8a7fe4`。错误 wind 的 route/column 输出仅作为前向模型与描述性 QC；没有替换真实 query。

## 审计实现误报及可追溯勘误

预运行封存的主 analyzer 把两件事写成了 `clock==ref_clock==expected`：实际跨 arm 时钟一致，以及文本时间与未格式化 float32 重构值精确一致。原生 TSV 以 9 位有效数字写出时钟，例如 `0.600000024`，而该 native float32 转成 float64 是 `0.6000000238418579`。实际五个 arms 的记录逐项相同，后一个过严格比较却使初始报告错误地标记 RNG HOLD。

原 analyzer、预运行 seal 和全部初始 HOLD 输出保留在 `initial_audit/`，没有删除或重新封存其旧代码。外置 `analyze_e2_clock_serialization_erratum.py` 只修正这一个表达式：跨 arm 原始记录仍要求精确相同；重构时间比较先还原到原生 float32 表示，并要求精确一致，未新增容差、放宽门或修改任何科学设置。`E2_AUDIT_CLOCK_SERIALIZATION_ERRATUM.json` 给出 before/after 表达式和两版 SHA256；无新增模拟。

**预运行封存的独立 verifier 未修改。** 它直接复核五个 arms 原始记录、完整 sigma 数组、输入/native 哈希及稳定 Gaussian tail，没有使用主 analyzer 的错误重构比较。独立复核 PASS，margin max difference=0、前向 QC max difference=0；检查 1,620 个 raw 文件、39 份 R0 冻结文件和 10,200 次 native parity。此勘误纠正审计实现错误，未救援实际失败的科学门。

随后在 Linux 新目录从 ZIP 重新解包，执行原 `freeze_design.py --verify`、外置勘误 analyzer 和未改动的独立 verifier，三项 exit=0、同样资格判决；新增科学运行=0。`LINUX_REPLAY_VERIFICATION.json`、Linux 独立结果和三个 stdout/stderr 日志均随包保存。环境为 Python 3.10.12、NumPy 1.26.4、SciPy 1.8.0；该 SciPy 声明的 NumPy 版本范围 warning 原样保留，计算仍通过，未更换依赖或 native runtime。Linux review 输入 ZIP 自身也有独立哈希并随包保留。

## 资源、证据及停止

四条 scientific simulation＋native extraction campaign 实测 wall=7.457593 s，单条 simulation=0.809–0.960 s；最大 RSS=127,848,448 bytes，约 121.9 MiB。E2 原始输入/输出/审计材料约 412.4 MB；按冻结资源公式，包括已完成 E1 与剩余 28 条的安全系数及 30 min 余量，wall 投影约 1,930 s、总 bytes 投影约 1.104 GB，低于 3 h/5 GiB。post-run disk free=26,779,406,336 bytes，RAM available=5,679,644,672 bytes，仍满足 12/3 GiB。

Native archive SHA256：`f2833ae96a9650a3734206867036cb2ac82da424b3a95a5634b162a9c4dff670`，25,899,770 bytes；含四条全部原生结果、readback/输入、filament state/route/columns/parity、runtime/source/argv/env/time/RSS、完整 U0 S0/r01 参照及 1,620 项 hash manifest。VM 和回传后 CRC/member hashes 均 PASS。原 E1 native files 在运行前后均再次复核未变。

`E2_DESCRIPTIVE_FORWARD_QC.json` 仅归档此单个区组 D_F/D_Y。wrong-wind 的其他 seeds 和 S1 库尚未完成，因此没有构建不合格的 LORO posterior 或评分 D_B，不选择有利方向、阈值、mask 或 horizon。两个候选、四 seed 的最终科学门只能在全部 40 行合法且资格通过后按原合同计算。

**已停止，等待下一轮 E2 审查与剩余 28 条的新授权。** 不启动 E3、新算法训练或新数据集实验。本结果只关闭这个 sentinel 的 CRN/运行资格门。
