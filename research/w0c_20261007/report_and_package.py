from pathlib import Path
import csv, json, hashlib, zipfile, datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OLD=Path('C:/Users/50176/Documents/Codex/2026-10-05/codex-pmfs-pmfs-task-sufficient-world/outputs')
DEST=ROOT/'_deliveries/W0C_STAGE0_20261007'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
decision=json.loads((HERE/'STAGE0_V2_DECISION.json').read_text());verify=json.loads((HERE/'INDEPENDENT_VERIFICATION.json').read_text())
assert decision['eligible_cells']==0 and verify['status']=='PASS'
with (HERE/'STAGE0_V2_CELL_ELIGIBILITY.csv').open(newline='',encoding='utf-8') as f:cells=list(csv.DictReader(f))
table='\n'.join(f"| {r['house']} | {r['wind']} | G{r['gas']} | {r['source']} | {100*float(r['worst_run_mean_edge_mass_fraction']):.2f}% | {100*float(r['worst_run_q95_edge_mass_fraction']):.2f}% | {r['eligible_realizations']}/4 |" for r in cells)
text=f'''# W0C Stage 0：边界支撑资格审查

日期：2026-10-07。判定：**`W0C_STAGE0_NO_CLEAN_BASE_HOLD`**。

已核验并执行 W0C 的基准案例资格阶段。64 条 baseline、16 个 House×wind×gas×source cell 中，只有 2 条单独 realization 合格，**0 个 cell 的四次 realization 全部合格**。没有可冻结为正式配对干预的干净基准。新增 GADEN run 为 **0**，构造的干预风场为 **0**，matched-error 因果问题尚未得到结果。

这是前提未满足，不能写成 `W0C_GLOBAL_ERROR_SUFFICIENT_STOP`，也不能升级为 `W0C_TASK_ANISOTROPY_PASS` 或 PRIMARY_GO。W0-PRE2 保持 exploratory 地位，R0C1/R0D/P0 的既有停止边界保持有效。

## 仓库与环境

用户要求将 `D:/ZYC/A-gas` 的 origin 改为 `https://github.com/kris-yun/uav-gsl-isj.git`，已执行。此前为 `https://github.com/kris-yun/cp-sbd-gsl.git`。本次只更新 remote URL，没有重置原 checkout 或改动它的既有工作文件。

独立工作树：`D:/ZYC/A-gas/_worktrees/w0c-matched-error-20261007`，分支 `codex/w0c-matched-error-20261007`，从用户 handoff head `b3d16c8ed39e439dc14ce3aadc451af786276afc` 开始。W0C 合同来自 `12d530768e66619c24c1b7ae458819890b3ab5b2`，PRE2 来自 `d539ad9297e99905fbc530a8c1073b9876c7526a`。

VM `zyc@192.168.111.128` 当前可访问；本次读取时 `/home/zyc/ros2_ws` 所在文件系统约 28 GiB 可用、内存约 5.4 GiB available，没有正在运行的 GADEN 科学作业。已核对原 seeded generator 的 SHA-256 为 `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`，与 R0C/R0D 冻结记录相同。VM 仅做只读检查，没有启动、修改或清理 ROS/GADEN 作业。

## 门限与先后顺序

先保存 `STAGE0_BOUNDARY_PROTOCOL_FROZEN.json`，再读取并计算边界分数。时间窗固定为 100–700 s、31 个时点，使用原有 32×32 column footprint。每次 realization 要求外侧三列/行的 footprint mass 平均比例 ≤5%、95 分位 ≤10%，源和质心保留至少三格边界余量。

最初 V1 仅检查按平均 plume-weighted wind 选出的一个下风侧，并先检查 G13。这种实现错误地将 H02-WD 两源选为干净案例。随后全侧诊断发现：WD 的平均水平净风极小，所选 ymax 侧几乎没有质量，而其他侧有大量质量。source0 的 ymin mean 可达到 42.38%，source1 可达到 28.31%。**平均风抵消使单侧筛查出现假通过**。

因此，V1 和全部诊断被保留，没有覆盖。另行冻结 V2，改用四个水平外边界的三格带并集，角部只计一次；同时检查全部 64 条已有 baseline，包括 G10 和 G13。5%/10% 门限没有放宽。V2 的源及质心余量也在全部水平侧检查。此修正发生于任何干预构造和仿真之前，修正的是已显示的筛查漏洞，没有使用干预结果选参数。

外边界 footprint 比例是**截断风险的保守筛查代理**，并不是已经流出 domain 的物理质量比例。这里的结论是不能在所冻结的标准下排除混杂，不是证明每条 plume 都被同等程度截断。三格带在这些小 domain 中具有实际空间宽度，这一筛查比只看质心严格。

## 全部 cell 结果

下表的 mean/q95 是各 cell 四次 realization 中的最大值。一个 cell 必须 4/4 全部合格。16 个 cell 的最差 realization 平均边缘比例均高于 5%，范围 17.65%–83.52%。不能只挑两条单独通过的 realization 而丢弃同 cell 的其他重复。

| House | wind | gas | source | 最差 mean edge mass | 最差 q95 edge mass | 合格重复 |
|---|---|---|---:|---:|---:|---:|
{table}

逐 run 及逐 time 的完整数值分别在 `STAGE0_V2_RUN_BOUNDARY_SCORES.csv` 和 `STAGE0_V2_TIME_BOUNDARY_TRACES.csv`。

## 已做但不能用于救回资格的观察预检

V1 暂时选中 H02-WD 后，曾先冻结一条 geometry-only 的 31 点 serpentine 理想采样日程，在原有 native 3D 场缓存上检查两种二候选源推断。hit-likelihood 和 log-concentration Gaussian likelihood 都是 7/8 oracle 分类正确，每个源至少 3/4 正确且四次都可检测。这个结果只说明该理想 sparse observation 在这些 baseline 中有源信息，**不能替代边界资格**。

这条路线仅是原有 native free-voxel 上的稀疏观察日程，没有通过连续飞行的碰撞/可达性验证。第一种推断是二候选 forward-simulation hit-probability surrogate，未主张 native PMFS 公式/代码/闭环 parity；第二种是简化 source-term likelihood。没有实施 transport ensemble 或复现 Piro 算法，因为后续干预资格已经失败。预检文件完整保留，并明确不作为 W0C Stage 3/4 因果结果。

## 独立复核与冻结完整性

独立验证没有导入主筛查实现：边界质量用 total 减 interior 重新计算，分位数用手工线性插值，质心用另行导出的 `PLUME_STATES_AND_CAUSAL_WIND_64.csv`，而不是原缓存的 raw 数组。复核 64 个原始状态 SHA-256、1984 个时点的原生质心，以及 protocol/code 的封存 hash。最大数值差异 {verify['max_numeric_difference']:.3g}；重新得到 0 个合格 cell，验证 PASS。

旧 runner、source、gas、RNG seeds、House geometry、风场、raw archive 和 frozen analysis 均仅被读取。没有额外 seed、source 迁移、公开数据集、神经模型、world model、626 候选网格或旧路线重跑。

## 下一步的具体阻塞与可评审修复边界

当前 W0C 原场景缺少通过此门的基准，不能直接启动“32 次干预”并将差异解释为内部 transport structure 的因果作用。需要先补充可排除边界风险的真实 unperturbed 基准，然后重新冻结 W0C，才能形成一个可执行的 runlist。

可讨论的 benchmark 修订是给同一 House/源增加真实下风 transport support（同时重新取得与扩展计算域一致的 oracle wind），或者在后续 FSR 自建案例上取得合法的干净基准。不能把现有 wind 零填充扩域后视为真实 oracle，也不能事后缩短 100–700 s 窗口、放宽 5%/10% 门限、替换两条有利重复或悄悄搬源。当前执行没有进行这些修订。

Piro 等工作的公开摘要确认了多错误模型排序/融合的先例：[CNR 作者机构记录](https://iris.cnr.it/handle/20.500.14243/544045)。本次仅核验了公开摘要，没有宣称完成其公式级复现。因此泛化的“多模型融合”仍不能作为本项目创新。

## 复现与证据包

运行 `verify_stage0_v2.py` 可在原文件位置复核。`audit_stage0_v2.py` 和两个预检脚本会拒绝覆盖已有判定；重新复算请在副本中移除副本的输出并重新封存，保持本目录不变。

交付 ZIP 包含本目录全部 protocol、脚本、分数、判定与独立复核，还包含原 64 个 P0 state NPZ、源合同、geometry、原生质心 CSV 与相关 parent seals。保留原文件的 hash，不生成新羽流数据。native 3D route 的大缓存以原路径和 SHA 清单提供，只作为已废止 V1 的前检 provenance。完整 GADEN raw archive 仍位于原 R0C/R0D 库，未复制或改写。
'''
(HERE/'REPORT_zh.md').write_text(text,encoding='utf-8')
(HERE/'README.md').write_text('Active decision: STAGE0_V2_DECISION.json. V1 is superseded because its net-wind side selector missed other boundary support. Read REPORT_zh.md. New simulations = 0. Do not use ROUTE_PREFLIGHT_DECISION.json to override the boundary HOLD.\n',encoding='utf-8')
DEST.mkdir(parents=True,exist_ok=True)
archive=DEST/'W0C_STAGE0_NO_CLEAN_BASE_HOLD_20261007.zip'
if archive.exists():raise RuntimeError('Preserve existing package')
items=[(p,'w0c_stage0/'+p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in ['PACKAGE_CONTENTS_SHA256.csv','PACKAGE_VERIFICATION.json']]
deps=[OLD/'P0'/name for name in ['RUNS_64_FROZEN.json','EXTRACTION_SEAL_BEFORE_SCORING.json','PLUME_STATES_AND_CAUSAL_WIND_64.csv','House01_OccupancyGrid3D.csv','House02_OccupancyGrid3D.csv']]
deps += [OLD/'R0C/SOURCE_CONTRACT_R0C.json',OLD/'R0C/FROZEN_CONFIGS_32.json',OLD/'R0C/RUNTIME.json']
for p in deps:items.append((p,'dependencies/'+p.parent.name+'/'+p.name))
for p in sorted((OLD/'P0/states').glob('*.npz')):items.append((p,'dependencies/P0/states/'+p.name))
inventory=[]
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    for p,name in items:
        z.write(p,name);inventory.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
    with (HERE/'PACKAGE_CONTENTS_SHA256.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(inventory)
    z.write(HERE/'PACKAGE_CONTENTS_SHA256.csv','PACKAGE_CONTENTS_SHA256.csv')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for row in inventory:
        data=z.read(row['path']);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
verification={'status':'PASS','archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'verified_members':len(inventory),'baseline_state_count':sum('/states/' in r['path'] for r in inventory),'zip_crc_and_all_member_hashes_verified':True,'new_simulations':0,'status_of_causal_hypothesis':'UNTESTED_STAGE0_HOLD'}
(HERE/'PACKAGE_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
(DEST/'PACKAGE_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
(DEST/'SHA256SUMS.txt').write_text(verification['sha256']+'  '+archive.name+'\n',encoding='utf-8')
print(json.dumps(verification,indent=2))
