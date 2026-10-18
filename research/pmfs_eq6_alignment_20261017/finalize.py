from pathlib import Path
import csv,hashlib,json,shutil,statistics,zipfile
R=Path(__file__).resolve().parent;PROJECT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def write(p,rs):
    with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
assert not (R/'DELIVERY.json').exists(),'Final evidence already exists'
lock=json.loads((R/'AUTHOR_SOURCE_LOCK.json').read_text(encoding='utf-8'))
for a in lock['files']:
    p=R/'author_release'/a['path'];assert sha(p)==a['sha256']
    oid=hashlib.sha1(b'blob '+str(p.stat().st_size).encode()+b'\0'+p.read_bytes()).hexdigest()
    assert oid==a['git_blob_oid'],a['path']
P=json.loads((R/'FROZEN_PLAN.json').read_text(encoding='utf-8'))
for c in P['contexts']:
    for m in c['maps']:assert sha(R/'fixtures'/c['key']/m['map_file'])==m['sha256']
previous=PROJECT/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016'
audit=PROJECT/'_staging/FSR_S2_PMFS_PAPER_BASELINE_AUDIT_V1_20261018'
peer=PROJECT/'_staging/FSR_S2_PMFS_EQ6_INPUT_INVENTORY_20261017'
copies=[(audit/'PAPER_CODE_PARAMETER_MATRIX.csv','provenance/PAPER_CODE_PARAMETER_MATRIX_PRIOR.csv'),(audit/'VERSION_SEMANTIC_MATRIX.json','provenance/VERSION_SEMANTIC_MATRIX_PRIOR.json'),(audit/'COST_AND_RUNTIME_REVIEW.json','provenance/COST_AND_RUNTIME_REVIEW_PRIOR.json'),(previous/'paper_baseline_2024/FINAL_NATIVE_REPRO_RESULTS.csv','provenance/HISTORICAL_ALL_RESULTS_PRIOR.csv'),(previous/'paper_baseline_2024/RANDOMNESS_AND_REPETITION_AUDIT_zh.md','provenance/RANDOMNESS_AND_REPETITION_AUDIT_PRIOR_zh.md')]
for src,rel in copies:
    dst=R/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
if peer.exists():
    for src in sorted(peer.iterdir()):
        if src.is_file():dst=R/'peer_handoff'/src.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(src,dst)
peer_review=PROJECT/'_staging/FSR_S2_PMFS_EQ6_RESULT_REVIEW_20261017'
if peer_review.exists():
    for src in sorted(peer_review.iterdir()):
        if src.is_file():dst=R/'peer_result_review'/src.name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(src,dst)
eligible=json.loads((R/'HISTORICAL_2024_ELIGIBILITY.json').read_text(encoding='utf-8'))
ids={r['id']for r in eligible['records']}
old=[r for r in rows(previous/'paper_baseline_2024/FINAL_NATIVE_REPRO_RESULTS.csv')if r['id']in ids]
write(R/'HISTORICAL_SIX_REPEATS.csv',old)
aggregate=[]
for case,paper_error,paper_time in [('A2',.6,87.),('B2',2.3,110.5)]:
    a=[r for r in old if r['case']==case]
    aggregate.append(dict(case=case,repeats=len(a),native_mean_declared_error_m=statistics.mean(float(r['native_declared_error_m'])for r in a),native_mean_search_s=statistics.mean(float(r['native_search_s'])for r in a),paper_mean_error_approx_m=paper_error,paper_mean_time_approx_s=paper_time,paper_repeats=30,strict_comparison_qualified=False,reason='Paper figure values inherited from prior approximate reading. July-based adapted historical execution, shared generated gas realization, unresolved exact experimental snapshot/confidence/coverage/clock semantics; not new Sep18 runs.'))
write(R/'PAPER_COMPARISON_DIAGNOSTIC_ONLY.csv',aggregate)
cmds=json.loads((R/'execution/COMMANDS.json').read_text())+json.loads((R/'execution/GRID_COMMANDS.json').read_text())
put(R/'COST_AND_COMMANDS.json',dict(status='EIGHT_CPP_COMPONENT_COMMANDS_EXIT0',commands=cmds,guest_child_cpu_s=sum(x['child_cpu_s']for x in cmds),sum_guest_command_wall_s=sum(x['wall_s']for x in cmds),desktop_analysis_cpu_not_measured=True,not_an_algorithm_efficiency_benchmark=True,analysis_attempt1_exit_code=1,analysis_attempt2_exit_code=0,new_forward_simulations=0,new_rng_states=0,new_gas_worlds=0,new_ROS_episodes=0,AIMMD_or_S2_runs=0))
draft='''# 给作者的三个精确问题（本地草稿，未发送）

Subject: PMFS TRO 2024 reproducible baseline: confidence, coverage, and experimental configuration

Dear PMFS authors,

We are reconstructing the baseline described in the final IEEE Transactions on Robotics article, DOI 10.1109/TRO.2024.3426368. We keep the released source unchanged and label any paper-equation control separately. Could you clarify the following?

1. On page 3556, Equation (6) accumulates Gaussian distance weights as Omega, then uses alpha = 1 - exp(-Omega^2 / sigma_Omega^2). Commit a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533 accumulates omega in the same way but computes 1 - exp(-omega / confidenceMeasurementWeight^2). Which expression and parameter meaning were used in the published experiments? Is confidenceMeasurementWeight equal to sigma_Omega, or was a different definition intended? The cited Kernel DM+V article and the 2025 thesis retain the squared expression; we have not found an equivalent released definition.

2. On page 3557, the article describes discrete filament coverage increasing with time since emission. The inspected public implementation records the centre cell and does not retain a per-filament age/radius state. Could you provide the actual coverage/growth law, coefficients, obstacle handling and implementation used in the experiments, or clarify whether the article should refer to centre-cell occupancy? We will not invent r(age) or equate fixed map blur with per-filament age-dependent coverage.

3. Equation (8) gives a per-cell factor 1-alpha*abs(p_measured-p_simulated), whereas the release also multiplies the difference by sourceDiscriminationPower. A value of 1 matches the printed factor, while released example configurations contain other values. What coefficient and exact source/dependency snapshot were used for the published experiments? Could you also identify the scene parameter files, historical GMRF revision, clock/acceleration conventions, declaration/readout rules, and any original gas realization or repetition-seed records that can be shared? We recognize that later maintenance fixes may differ from the experiment snapshot.

Our Eq6-only component control confirms the algebra changes output; it does not establish which implementation generated the paper figures, or indicate that any published experiment was wrong.

Thank you for your help.

Evidence: https://doi.org/10.1109/TRO.2024.3426368 ; https://github.com/MAPIRlab/GasSourceLocalization/tree/a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533
'''
(R/'给作者的三个问题_未发送.md').write_text(draft,encoding='utf-8')
report='''# PMFS论文Eq6单因素重建：本轮交付

本轮完成独立命名的Eq6对齐组件和固定历史评分对照；完整论文复现仍为HOLD。AIMMD、S2、新ROS闭环和新气体世界均未启动。Pro文字中提到的新补丁包没有随消息附上，本轮未找到该附件；因此使用先前已核验的作者2024-09-18源码独立生成补丁，不声称运行了Pro原附件。

## 四种身份

|身份|本轮证据与边界|
|---|---|
|作者原样发布版|固定a8d5a764；53个既有审计登记源码/配置文件逐字SHA256及Git blob OID匹配。这里是明确范围的源码集，并非完整ROS及全部依赖发行包，也没有证明它是原论文实验提交。|
|工程适配版|本轮不新增任何源代码工程补丁。保留作者修复版的原生Grid2D；4种非方形尺寸的3144次整数索引/反索引与边界检查通过，仅为组件资格，不冒称完整导航或ROS验收。既有July运行的观测窗口、map-ready、时钟与GMRF适配继续分别记录。|
|论文Eq6对齐版|在独立副本中，仅把置信度指数的omega改成omega*omega；其余文件原样保留。git apply --check通过，21组C++公式检查通过；提取的原函数数学运算与真实响应图评分通过，不等于完整Sep18节点已编译运行。|
|完整论文描述版|HOLD。年龄相关覆盖律、相关参数/障碍处理、准确实验提交，以及评分额外系数与实验配置尚未澄清。没有猜测补全。|

## C++实际执行

从Sep18的PMFSLib.cpp提取置信度行，从Math.cpp提取高斯、logistic及lerp原函数，从Simulations.cpp提取原sourceProbFromMaps函数体；以最小数据容器编译C++17。原作者函数体及单行改动均可核查。没有把Python新公式误称为原生节点执行。

21组固定Omega/权重检查相对独立长双精度公式最大误差5.55e-17。五次中心观测中，第一步alpha从0.3289705682变为0.1471357967，第五步从0.8639470869变为0.9812933009。Omega<1时平方后置信度更低，Omega>1时更高，因此不能把这项变更描述为统一“调软”。这只是按固定参数对应关系实现的论文公式控制，尚不能确定作者当年的sigma参数解释。

四种矩形(3,7)、(7,3)、(33,47)、(47,33)的3144次索引往返全部通过；未修改Grid2D.hpp。该检查不涵盖所有障碍传播、地图裁剪或运行时接口。

## 同历史评分结果：614张已有预测，零新传播

2024历史六次A2/B2有实际消费记录与42次后验快照，但没有直接Omega列及历史完整候选响应/owner/RNG，因此不能精确重构这些真实回合的Eq6反事实。同行窗口另外整理的54套旧离线预测属于July源码加新的安全RNG控制，也不能冒充Sep18或历史actor预测。

为完成有严格数值回查的公式敏感性诊断，本轮使用2026修风后A2/B2四次已有源更新中的直接Omega、实际接触图及614张已保存候选响应。原预测图、全部测量、源支持、评分系数0.3和原最终粗细树均冻结。源评分函数在该控制下与Sep18提取表达式一致；这不让整个2026前向实现变成2024方法。原始分数重算最大差2.31e-14，原始归一化后验最大差1.53e-16，先通过重算一致性再比较平方项。

|已有记录|作者式真源格排名→Eq6排名|后验均值误差m：作者式→Eq6|两分布总变差|
|---|---|---|---|
|A2 update_0|141→142|3.1151→3.3144|0.06834|
|A2 update_1|112→110|1.0349→1.0023|0.02426|
|B2 update_0|不具备真源支持|仅保留描述性输出|0.06585|
|B2 update_1|不具备真源支持|仅保留描述性输出|0.08366|

A2两次的MAP均未变化。这说明平方项确实改变源概率，影响有正有负；没有证明统一定位增益。B2这份2026记录中的真源格674为非候选，不能把真源概率为零归因于Eq6，也不开放该格制造恢复。首次分析在支持域断言停止，原脚本及失败记录保留；只修正报告程序，将不合法真源指标标为不可用，未重跑C++或前向模拟。

该表只是固定已有粗细树后的条件性重评分。Eq6改变后可能会选择不同细化叶和动作，这些反事实状态没有保存，本轮没有生成。表中排名是格级严格排名，区域内同分格会并列，不是独立候选数；均值误差也不是论文最终声明误差。不能据此称新增闭环收益。

## A2/B2正式论文复现资格

现存2024历史六回合共660消费窗口、42次源更新、33756格快照，三次来自每配置同一已生成气体实现，并非三个独立气体世界。它们仍是July源码及单独记录的接口/时钟适配运行，不能自动升级为Sep18或论文一致版。

六次较完善的观测有效性/地图就绪版本中，A2声明误差均值约0.3172m、搜索约109.27s；B2约2.1522m、129.85s。先前从论文图近似读取的对应值约0.6m/87s、2.3m/110.5s，原文每配置30次。当前三次诊断、共同物理实现、版本及时间语义未完全对齐，不足以进行正式统计复现裁决，也不能把本机误差更小视为算法改进。

在实际统计对照图8/10/11前，还须确认年龄覆盖与评分系数、准确源码和GMRF依赖、局地测风而非真风、物理帧/机器人/算法计时耦合、源支持和传感器消费、声明方差小于1m²以及读出规则。论文未给出所有PMFS通用300秒上限，不能把Surge-Cast的300秒直接移植。现有矩阵PAPER_CODE_PARAMETER_MATRIX_PRIOR.csv和各run身份记录均随包保留。

## 结束裁决

已完成：只改单行的可复查Eq6源码、C++数学与矩形索引组件、同历史概率敏感性、既有A2/B2资格及反例归档、作者精确询问草稿。

尚未完成：完整论文基线、完整Sep18 ROS节点资格、正式30次统计结果对齐。当前不能用继续增加随机重复替代缺失的覆盖律及实验参数。作者三个问题草稿仅保存在本地，没有发邮件、issue或评论。

下一步仅在取得缺失定义/可核验实验代码之后，做相应事件与参数资格检查；本轮不自动恢复AIMMD或启动新批次。没有把公式重建、工程适配或原生复现的差异记作创新收益。
'''
(R/'本轮结论_zh.md').write_text(report,encoding='utf-8')
readme='''# Reproduce this bounded control

This package is an Eq6-only reconstruction and a fixed-tree stored-history sensitivity study, not a complete ROS distribution or full paper replication. Read 本轮结论_zh.md first.

On Linux with g++ and Python+NumPy, compile `g++ -std=c++17 -O2 cpp/check.cpp -o eq6_check`; then run `./eq6_check --unit` and, for each fixture directory, `./eq6_check fixtures/A2_update_0 /tmp/A2_update_0_scores.csv` (the output filename must be new). The C++ runner reads only stored maps. Grid check: `g++ -std=c++17 -O2 cpp/grid_probe.cpp -o grid_probe && ./grid_probe`.

`python verify.py` checks all delivered file hashes. The saved Windows/VM paths in original provenance are historical identities, not required network resources. `prepare.py` is the original frozen-data preparation procedure and requires original local evidence; it is not an offline portable entrypoint. The guest runner is the original execution logger, not a portable ROS launcher.

The C++ formula fragments and original score body are derived from the pinned Sep18 source; minimal containers do not reproduce ROS/grid orchestration. The stored prediction maps and history are explicitly the 2026 corrected-wind diagnostic, with coefficient0.3 and adaptive tree frozen. Changing Eq6 may change adaptive refinement/actions; those are not simulated here. No importance sampling or new closed-loop gain is tested.
'''
(R/'README.md').write_text(readme,encoding='utf-8')
verify='''from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
m=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for r in m['files']:
 p=R/r['path'];assert p.stat().st_size==r['bytes'],r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],r['path']
print(json.dumps(dict(status='PASS',files=len(m['files']))))
'''
(R/'verify.py').write_text(verify,encoding='utf-8')
put(R/'DELIVERY.json',dict(status='COMPONENT_AND_SENSITIVITY_COMPLETE_STRICT_PAPER_BASELINE_HOLD',author_unchanged_files_verified=len(lock['files']),source_maps_verified=sum(len(c['maps'])for c in P['contexts']),cpp_commands=len(cmds),zero_new_forward_and_ROS=True,author_draft_sent=False,Pro_patch_attachment_received=False,branch='codex/pmfs-paper-eq6-alignment-20261017',further_experiments_stopped=True))
files=[]
for p in sorted(R.rglob('*')):
    if p.is_file() and p.name!='MANIFEST_SHA256.json' and '__pycache__'not in p.parts:files.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
put(R/'MANIFEST_SHA256.json',dict(files=files))
dest=Path('C:/Users/50176/Downloads/PMFS_论文Eq6单因素重建_同历史核验与基线缺口_20261017.zip');assert not dest.exists()
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
    for p in sorted(R.rglob('*')):
        if p.is_file()and'__pycache__'not in p.parts:z.write(p,'PMFS_EQ6_ALIGNMENT_20261017/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(dest)as z:
    assert z.testzip()is None
    for r in files:assert hashlib.sha256(z.read('PMFS_EQ6_ALIGNMENT_20261017/'+r['path'])).hexdigest()==r['sha256']
receipt=dict(status='PASS_ZIP_CRC_AND_EVERY_MANIFEST_MEMBER_SHA256',archive=str(dest),bytes=dest.stat().st_size,sha256=sha(dest),manifest_files=len(files),manifest_sha256=sha(R/'MANIFEST_SHA256.json'))
put(dest.with_suffix('.verification.json'),receipt)
print(json.dumps(receipt,ensure_ascii=False))
