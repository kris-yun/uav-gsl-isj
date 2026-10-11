"""Immutable flat RK0 parent + RK1 evidence in one offline review package."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path, PurePosixPath
import os, shutil, hashlib, json, zipfile
BASE=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
PARENT=BASE/'outputs/PMFS_RK0_PRO_REVIEW_BUNDLE_20261010_V2'
RK1=BASE/'outputs/PMFS_RK1_MATCHED_SUPPORT_CROSSFIT_20261010'
BUNDLE=BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010'
def long(p):
    s=os.path.abspath(str(p))
    return Path('\\\\?\\'+s) if os.name=='nt' and not s.startswith('\\\\?\\') else Path(s)
def sha(p):return hashlib.sha256(long(p).read_bytes()).hexdigest()
def cp(src,dst):
    long(dst.parent).mkdir(parents=True,exist_ok=True)
    shutil.copyfile(long(src),long(dst))
def tree(src,dst):
    for p in sorted(long(src).rglob('*')):
        if p.is_file():
            assert '__pycache__' not in p.parts
            cp(p,long(dst)/p.relative_to(long(src)))
def write(p,s):
    assert not long(p).exists()
    long(p).write_text(s.strip()+'\n',encoding='utf-8')
old_manifest=PARENT/'SHA256SUMS.json'
assert sha(old_manifest)=='c808546bc326cd0e2a35ed28e212b4bb98922bae66b7ba1a8017f8982d501b0b'
old=json.loads(long(old_manifest).read_text(encoding='utf-8'))
assert len(old)==1848
for n,h in old.items():assert sha(PARENT/n)==h,n
assert not BUNDLE.exists(),'Refuse overwrite review bundle'
BUNDLE.mkdir()
for p in sorted(long(PARENT).rglob('*')):
    if p.is_file():
        rel=p.relative_to(long(PARENT))
        if rel.as_posix()=='SHA256SUMS.json':rel=Path('RK0_ROOT_MANIFEST_FROZEN.json')
        cp(p,BUNDLE/rel)
tree(RK1,BUNDLE/'RK1_NEW')
cp(WORK/'verify_rk1.py',BUNDLE/'RK1_NEW/verify_rk1.py')
cp(WORK/'INDEPENDENT_NUMERIC_REVIEW_zh.md',BUNDLE/'RK1_NEW/independent_validation/INDEPENDENT_NUMERIC_REVIEW_zh.md')
tree(WORK/'independent_validation',BUNDLE/'RK1_NEW/independent_validation')
for n in ['SCIENCE_REVIEW_zh.md','science_recalculate_rk1.py','SCIENCE_INDEPENDENT_ARITHMETIC.json','SCIENCE_FINE_CLASS_GAP_RECOMPUTATION.json']:
    cp(WORK/n,BUNDLE/'RK1_NEW/independent_scientific_review'/n)
for n in ['freeze_rk1.py','build_rk1_reports.py','repair_figure_layout.py','package_rk1.py']:
    cp(WORK/n,BUNDLE/'RK1_NEW/workflow_archive'/n)
tree(BASE/'work/PMFS_TARGETED_EXPERIMENT_PLAN_20261010',BUNDLE/'RK1_NEW/pre_execution_static_feasibility')
write(BUNDLE/'RK1_NEW/workflow_archive/README_zh.md','''
# 工作流存档：不用重新运行生产器

实际实验入口已执行一次，权威文件为RK1_NEW/contract.json、PRE_RUN_CONTRACT_SHA256.txt、source/冻结源码及EXECUTION_LEDGER.json。此目录保留冻结、报告/图生成和打包代码，使用原Windows工作目录，不是包内新的实验入口。

报告/图脚本只读取结果。repair_figure_layout.py修复图C标签重叠，没有改核或预测。独立复算入口为包根verify_rk1_review_bundle.py；不要重新执行source/run_rk1.py、supervise_rk1.py或打包脚本。pre_execution_static_feasibility/与PRE_EXECUTION_SCIENTIFIC_REVIEW_zh.md是执行前原样文件，状态尚未执行的文字属于历史记录，不覆盖实际完成结果。
''')
cp(WORK/'verify_rk1_review_bundle.py',BUNDLE/'verify_rk1_review_bundle.py')
for n in ['test_rk1_review_bundle.py','RK1_MASTER_VERIFIER_QA.json','RK1_MASTER_VERIFIER_REVIEW_zh.md']:
    cp(WORK/n,BUNDLE/'RK1_NEW/delivery_verifier_qa'/n)
write(BUNDLE/'RK1_NEW/delivery_verifier_qa/REPORT_REVIEW_AND_RENDER_QA_zh.md','''
# 交付内容审查与图形验收

独立科学审查核对新报告与decision JSON，主MSE、均值、bias、检出、覆盖均一致。审查提出C7的“U→S”箭头笔误，已仅修报告文字，未动数值。C参数少于S、非嵌套、oracle、整库留出、旧材料及事后finegap均明确。

实际PNG经两次视觉查看：首次图C图例与tail文字重叠；仅重排图C图例空间，将tail块数放到横轴附注，再次查看通过。原科学数据、合同与实验输出不变。PNG/SVG均为实际数据派生审计图，不是新的实验。
''')
write(BUNDLE/'START_HERE_RK1_zh.md','''
# 给PRO：只需这一个包，先读RK1新结论

**这次已执行一次新的整库交叉拟合鉴别，不是再次整理旧实验。**目标是排除参考自拟合与缺kernel两个混杂，检验“共享响应把不同源条件的物理组成混合”。旧RK0、PRO及M2/M3完整证据一并逐字保留。

## 新结果与反例

| 整库留出材料 | U浓度MSE | S浓度MSE | C_ORACLE浓度MSE | S相对U变化 |
|---|---:|---:|---:|---|
| C7_1 | 1.105202 | 0.854989 | 0.760596 | 下降22.64% |
| K2_1 | 0.655702 | 0.672869 | 0.283668 | **上升2.62%** |
| C7_0 | 1.385552 | 1.230607 | 0.735548 | 下降11.18% |
| K2_0 | 0.418049 | 0.382582 | 0.214615 | 下降8.48% |

单位ppm²。U为共享XY响应；S为共享高度×扩散尺度四类；C是两套候选源各自的XY响应。四库等权均值U=0.891126、S=0.785262、C_ORACLE=0.498607。S改善3/4；C比S改善4/4，均值再降36.50%。共享U在两折均低估C7、高估K2。

**判断：共同支持内的条件响应压缩损失跨实现重现，不能完全归于覆盖缺项或参考自拟合。**普通四类有价值，但不能说已经充分。C7_0的C MAE、C7_1的C绝对bias仍有退化，全部结果保留。

最小科学边界：所有臂使用同Q和同一精确原生尾项，连续误差只来自Q内；C按真生成条件在输出冻结后选核，属于source-aware oracle，未实现未知源定位。C/S非嵌套，C总系数其实少于S，仍存在条件信息与容量差异。四库以前已被查看，200相关块不是200独立实验。本轮没有更新PMFS后验，没有新增分类成绩、时变风证据或CSCG训练。

## 这次究竟定位到哪一环

M3已给出导航支撑限制气体传播的干预证据；PRO同bank同scorer证明“中心占用→PID读出”足以改变当前候选排序；RK0/RK1进一步检查正确读出压缩，指向“保总体平均却损失源条件响应组成”。并未唯一分离高度、连续sigma、格内位置与遮挡，也未把B4完整错误收敛全部解释完。

请不要又回到泛泛的“所有机制HOLD”，也不要把这次oracle浓度预测收益直接写成定位方法收益。现在有可计算、可反驳的组成机制，主创新有效仍需新任务与可部署表示验证。

## 最省审核额度的阅读顺序

1. RK1_NEW/RK1_MATCHED_SUPPORT_MECHANISM_REPORT_zh.md：新实验完整定义、结果、反例、源码联系及边界。
2. RK1_NEW/TEST_BANK_PAIRED_COMPARISONS.csv、TEST_POSE_DIAGNOSTICS.csv、RK1_PAIRED_RESPONSE_DIAGNOSTIC.png：主端点及局部覆盖。
3. RK1_NEW/independent_scientific_review/SCIENCE_REVIEW_zh.md 与 independent_validation/INDEPENDENT_NUMERIC_REVIEW_zh.md：独立科学/数值复核。
4. 若需旧证据，FIRST_READ_FOR_PRO_zh.md、RK0_NEW/报告、PRO_REVIEW/、PARENT_M2M3_FROZEN/均原样保留。它们的状态与旧判断属于原轮，最新结论以本页及RK1_NEW为准。

八张核、全部408行×4候选响应、42490条细类差、原生逐粒子缓存、冻结合同与源码都在包内。无需VM、ROS或网络即可复算，不必再次索取原始数字。

## 请集中回答一个决策

**这次跨整份实现的条件残差，是否足以将下一有限原型聚焦“响应保真的有限状态构造”？若认可，怎样在相同oracle信息、实际容量与预算下，和正确普通共享响应及固定分箱公平对照，使它能被新任务否证？**

暂不要求重新搜几十篇理论，不启动24份气体、新的seed、CSCG或闭环。若认为普通模型即可解释，请指出本包哪项配对支持它，以及用哪个最小控制区分。不要把C真源选核当未知源部署方法。

## 一次只读核验

Python3 + NumPy；包含旧PRO深核时另需OpenCV。包根命令，输出必须为包外尚不存在JSON文件：

```text
python -B verify_rk1_review_bundle.py --package . --deep --parent-deep --out ../rk1_full_review_new.json
```

--deep重算RK1的核、预测、分母、指标与冻结身份；--parent-deep重算原RK0及PRO标量端点。均不调用producer/原生查询/新仿真，派生输出只写包外。主清单覆盖全新包；原RK0_ROOT_MANIFEST_FROZEN.json另以固定SHA硬锁1848个旧成员。验证器16项软件QA通过，包括412字符Windows路径及重哈旧篡改拒绝。

本轮只执行一次8核批计算，7.13秒、峰值91.59MiB；独立复核另计。完成后停止，等待PRO审核。
''')
write(BUNDLE/'SEND_TO_PRO_zh.md','''
请审核此合并包中的RK1新实验，不需要我再补旧文件。我们已按整份气体实现做两折留出，并让U/S/C使用完全相同的共同支持Q和精确原生尾项，从而隔离缺kernel和参考自拟合。共享XY响应U的等权浓度MSE为0.891126ppm²，普通高度×尺度四类S为0.785262，S在3/4库改善但K2_1退化2.62%；按真实生成条件事后选取的C_ORACLE为0.498607，较S四库均改善，平均再降36.50%。这支持共同组件内跨实现的源条件响应压缩损失，但不是部署定位收益：C为oracle，所有臂带原生尾项，C/S非嵌套，四份是旧材料，200块不独立。我们保留了MAE/bias及二值检出的反例，并提供冻结源码、196缓存、204原生锚点、全部核与预测及独立复核。请集中判断：这种证据是否足以研究响应保真的有限状态构造？若认可，怎样在相同信息/实际容量/预算下与正确普通模型及固定分箱公平对照，并用一个新任务否证它？不需要现在再扩展理论名单或启动批量气体。
''')
provenance=dict(stage='RK1_TARGETED_MATCHED_SUPPORT_CROSSFIT',parent_commit='16d69ac263ec2f8a17fa0d4895b9e5fe9837f885',
    frozen_parent_manifest_SHA256=sha(old_manifest),frozen_parent_members=len(old),
    original_RK0_ZIP_SHA256='5a797f485a98b8b96d2f98b728a72ab669b84e76a4ea5cbd2d4ede5534f79369',
    contract_SHA256=sha(RK1/'contract.json'),source_SHA256=sha(RK1/'source/run_rk1.py'),
    independent_checker_SHA256=sha(WORK/'verify_rk1.py'),new_producer_entries=1,new_phi_calls=0,new_physics=0,
    old_member_bytes_unchanged=True,old_root_manifest_renamed_only=True,
    source_condition_used_only_after_prediction_freeze=True,no_new_experiment_in_packaging=True)
write(BUNDLE/'RK1_DELIVERY_PROVENANCE.json',json.dumps(provenance,ensure_ascii=False,indent=2))
# This invariant is checked before writing the new manifest and by the shipped master.
assert sha(BUNDLE/'RK0_ROOT_MANIFEST_FROZEN.json')==sha(old_manifest)
for n,h in old.items():assert sha(BUNDLE/n)==h,n
mm={p.relative_to(long(BUNDLE)).as_posix():sha(p) for p in sorted(long(BUNDLE).rglob('*')) if p.is_file()}
assert 'SHA256SUMS.json' not in mm
write(BUNDLE/'SHA256SUMS.json',json.dumps(mm,ensure_ascii=False,indent=2))
archive=BUNDLE.with_name(BUNDLE.name+'_REVIEW.zip')
assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as z:
    for p in sorted(long(BUNDLE).rglob('*')):
        if p.is_file():
            n=p.relative_to(long(BUNDLE)).as_posix()
            assert not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
            z.write(p,n)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    count=len(z.infolist())
meta=dict(package=str(BUNDLE),ZIP=str(archive),ZIP_bytes=archive.stat().st_size,ZIP_SHA256=sha(archive),
    files=count,root_hashed_members=len(mm),root_manifest_SHA256=sha(BUNDLE/'SHA256SUMS.json'),CRC_PASS=True,
    old_hashed_members_checked=len(old),new_RK1_producer_calls_in_packaging=0)
write(archive.with_suffix('.zip.sha256'),meta['ZIP_SHA256']+'  '+archive.name)
write(BASE/'outputs/PMFS_RK1_DELIVERY_ARCHIVE_CHECK.json',json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps(meta,ensure_ascii=False,indent=2))
