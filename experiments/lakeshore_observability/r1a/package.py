"""Portable R1A evidence, original-data immutability and independent gate checks."""
import csv,zipfile,subprocess,shutil,datetime,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *
decision=json.loads((OUT/'R1A_FINAL_DECISION.json').read_text())
summary=pd.read_csv(OUT/'height_summary_factor_1.csv');mid=summary.query('release==10 and height==30').set_index('environment').loc[ENVS].reset_index()
paired=pd.read_csv(OUT/'paired_F_control_comparisons.csv');alloc=pd.read_csv(OUT/'R30_allocation_by_source_seed.csv');rho=pd.read_csv(OUT/'source_x_R30_spearman.csv');peakrho=pd.read_csv(OUT/'source_x_peak_spearman_exploratory.csv')
fig,axs=plt.subplots(1,3,figsize=(16,4),layout='constrained');labels=mid.environment.tolist()
for ax,column,label in zip(axs,['hit_rate','top1','median_margin'],['30m hit rate','30m Top1 (fractional ties)','30m median Brier margin']):
 ax.bar(labels,mid[column]);ax.set_ylabel(label);ax.tick_params(axis='x',labelrotation=45);ax.grid(axis='y',alpha=.2)
fig.suptitle('R1A mid release10: controls without vertical wind retain source information')
fig.savefig(OUT/'R1A_mid_release_decomposition.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
for ax,rate in zip(axs,[5,10,20]):
 for env in ['C06','C08','H1','H2','F1','F2']:
  q=alloc[(alloc.release==rate)&(alloc.environment==env)].groupby('source_x').agg(hit10=('hit10','mean'),hit30=('hit30','mean'));ratio=q.hit30/(q.hit10+q.hit30);ax.plot(q.index,ratio,'o-',label=env)
 ax.set_title(f'{rate} filaments/s');ax.set_xlabel('Source x (m)');ax.set_ylabel('R30');ax.grid(alpha=.2);ax.legend(fontsize=7)
fig.savefig(OUT/'R1A_distance_allocation.png',dpi=150);plt.close(fig)
stability=summary.query('height==30').pivot_table(index='environment',columns='release',values=['hit_rate','top1','median_margin'])
rho_summary=rho.groupby(['environment','release']).spearman.agg(['count','min','median','max']);peak_summary=peakrho.groupby(['environment','release']).rho.agg(['count','median'])
report='''# R1A 因果拆解报告

## 结论

DECISION

原始判定仍为 `R1_HOLD_WEAK_OR_UNSTABLE`。没有回改原 R1 门槛或将其升为 PASS；R1.1、R2 均未执行。

在本次固定 GADEN 模型和轨迹内，均匀慢风以及不含垂直风的控制场可以产生30m源身份信息。不能再把“30m存在可辨识层”或source-x→R30单调性当作湖风锋垂直风的独有证据。完整 F 场仍可能改变观测分布，但源身份已经可由零垂直风控制辨识，不能据此宣称垂直抬升是必要机制。

## 原数据复核

原864-realization包的969条MANIFEST逐一复核，原始文件和冻结判定均未改变。原始F1/F2在r10、30m的margin中位数为0.077490/0.044918，最低0.030947/0.007531；N0/L1完全同分、fractional Top1=1/9、平均rank5。公开Wisco支持低空热力状态变化，不提供真实0.5–1m/s锋面抬升的实测确认。

时间前缀、10°锥和通道合并的复核均标为事后探索。45°捕获率100%只适用于有hit的样本，并非整个轨迹的所有source→query组合都在锥内；全轨迹几何比例另存CSV。r10完整300s的10+30m合并Top1仍为100%，但较弱通道会改变/稀释Brier margin；不能将margin下降写成该条件下的Top1下降。

## 控制场和冻结

C20=N0原文件；C06/C08为均匀u=.6/.8m/s，v=w=0。S06/S08为对应F场在原300s XY轨迹上、每个原生z网格的u均值，沿x/y不变且w=0，从而保持path-level水平风剖面。这不是根据新气体结果调参。H1/H2保持对应F场每个点完全相同的u/v，只把w置零；明确作为不满足不可压缩连续性的数值诊断场，不能作为真实气象场。F1/F2的原CSV字节保持一致。

保留9个source、原四高度、120s warmup、300s轨迹、原native methane filament参数、原Brier估计器和Beta(1,1)先验。新plume seeds31001–31008在所有条件间配对。先运行r10的648个realization；确认拆解可解释后按新协议运行r5/20的1296个，共1944个、2,332,800行。4个独立native进程并行，每个OMP_NUM_THREADS=1，不改变任何单个plume过程。

所有场均经现有原生GADEN CSV preprocessing/query验证，100点误差小于1e-5，最大误差约6e-8。H场非零散度按诊断性质报告，不冒充物理QC通过。原adapter和libgaden.so SHA保持不变，没有升级或修改House环境/模拟器。

## 中释放率，30m结果

MID_TABLE

Top1为fractional tie credit。C20的11.11%是完全无源信息的全候选同分；其他控制的正margin并非tie产物。

## 释放率稳健性

STABILITY_TABLE

0.5×/1×/2×阈值结果均保留在height_summary_factor_*.csv和M4_trials_factor_*.csv中。未按环境调阈值。

## F减去对应控制的配对增量

PAIRED_TABLE

增量为同source/seed的best-false-minus-true margin差。区间按8个配对seed簇bootstrap20,000次，source点保留在各簇内；它们是模型Monte Carlo不确定性，不是气象事件置信区间。表中bootstrap使用均值，而主结果表使用margin中位数，二者不能混写。未宣称多重比较校正后的真实湖岸因果显著性。

## source-x与R30

RHO_TABLE

无气体的常量序列相关系数未定义，保留为空值而非写0。慢风控制同样出现距离→垂直分配规律时，只能保留为一般传播时长/源距离现象，不具湖岸锋面专属性。

## 浓度峰值排序：探索性

PEAK_TABLE

count表示Spearman可定义的seed数，峰值完全塌缩为同一个x的seed不计为有序相关。H2若复现反转或塌缩，说明w不是该排序失真的必要条件；H2仍是非物理诊断，不能由此宣称已完成真实湖岸风场验证。

## 判定与解释边界

本次“30m有源信息”的运行前定义：相对C20 Top1增量至少25pp、median margin为正且至少6/8seed margin中位数为正。较大垂直增量要求F对对应C/S/H均有至少25pp Top1增量、配对margin差95%区间下界为正且至少6/8seed同向。它们是新增R1A操作定义，未修改原R1 Gate。源身份成功率已饱和时，正的hit增量不是新的辨识增益，也不等于w必要。

因变量由native methane gas模型产生，包含原生sigma扩展、随机位移和浮力；所以零垂直风控制的成功支持“慢平流加已有气体物理足够”，不能再拆成“只由随机扩散造成”。固定120s warmup下，慢风的到达延迟/启动瞬态也包含在观测中，未进一步证明其与稳态驻留时间分离。C/S匹配轨迹均值而非全部source→path旅行时间；F−H才是精确保持水平场的w干预。所有判断限定在本合成场家族，不是跨真实湖岸事件的一般规律，不证明主动垂直采样收益。

本包保留原Brier脚本、其依赖、native adapter源码、轨迹/气体配置和原N0/F1/F2风场，支持复现R1A评分和控制构造。重跑原864-realization事后复核仍需原Git证据目录或上轮完整ZIP（SHA256:13f79e22b86a764cb91b0c6166ae684949a449bad5ed74eeb477ffc7d299d40b），没有把原观测复制进本包。GADEN运行依赖同一VM上的已冻结二进制，不通过重新安装取代它。

下一步不自动恢复旧R1.1/R2。先按本结果重新判断候选机制的湖岸专属性和科学价值；若研究水平非均匀流造成峰值排序失真，还需物理自洽场及固定的歧义任务另行验证。
'''
report=report.replace('DECISION',decision['decision']).replace('MID_TABLE',mid.to_markdown(index=False)).replace('STABILITY_TABLE',stability.to_markdown()).replace('PAIRED_TABLE',paired.to_markdown(index=False)).replace('RHO_TABLE',rho_summary.to_markdown()).replace('PEAK_TABLE',peak_summary.to_markdown())
(OUT/'R1A_DECONFOUND_REPORT_zh.md').write_text(report,encoding='utf-8')
for name in ['README.md','GENERATION_PLAN.md','R1_FORENSIC_DECONFOUND_20261003.md']:
 shutil.copyfile(EXP/name,OUT/('PROTOCOL_'+name))
shutil.copyfile(OLD/'MANIFEST.csv',OUT/'ORIGINAL_R1_MANIFEST.csv')
freeze=[]
for line in (OUT/'PRE_GAS_SHA256SUMS.txt').read_text().splitlines():
 h,name=line.split('  ',1);freeze.append({'path':name,'unchanged':sha(ROOT/name)==h})
assert all(q['unchanged'] for q in freeze)
oldrows=list(csv.DictReader((OLD/'MANIFEST.csv').open(encoding='utf-8')));oldchanged=[q['path'] for q in oldrows if sha(ROOT/q['path'])!=q['sha256']];assert not oldchanged
binary=subprocess.check_output(['ssh',HOST,'sha256sum '+ADAPTER+' '+LIB],text=True);assert binary==(OUT/'runtime_binary_hashes_before.txt').read_text();(OUT/'runtime_binary_hashes_after.txt').write_text(binary)
obs=pd.read_csv(OUT/'observation_manifest.csv');assert len(obs)==1944 and not obs.duplicated(['environment','release','source_x','source_y','plume_seed']).any()
for q in obs.itertuples():assert sha(ROOT/q.path)==q.sha256
primary=json.loads((OUT/'R1A_PRIMARY_DECISION.json').read_text());assert primary['decomposition_interpretable']
validation={'realizations':len(obs),'rows':1200*len(obs),'original_manifest_files_unchanged':len(oldrows),'frozen_analysis_checks':freeze,'runtime_binaries_unchanged':True,'secondary_gate_was_interpretable_primary':True,'original_R1_decision_unchanged':json.loads((OLD/'FINAL_DECISION.json').read_text())['decision']=='R1_HOLD_WEAK_OR_UNSTABLE','R1_1_and_R2_not_executed':True}
write_json('DELIVERY_VALIDATION.json',validation)
write_json('DELIVERY_PROVENANCE.json',{'branch':'research/lakeshore-observability-r0-r2-20261003','protocol_commit':'c351b287faa74171fded9af122cf4992b9facbb2','native_adapter_sha256':binary.splitlines()[0].split()[0],'native_library_sha256':binary.splitlines()[1].split()[0],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'R1A deconfounding only; original R1 hold preserved'})
dependencies=[EXP/'scripts/score_identifiability.py',EXP/'scripts/extract_fixed_paths.py',EXP/'scripts/gaden_adapter.cpp',EXP/'configs/gas_and_scoring.yaml',OLD/'fixed_path_contract.csv']+[EXP/f'generated_project/wind_simulations/{name}/wind_0.csv' for name in ['N0','F1','F2']]
members=sorted(set(p for base in [OUT,HERE] for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not (p.parent==OUT and p.name in ['MANIFEST.csv','SHA256SUMS.txt']))|set(dependencies))
rows=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in members]
with (OUT/'MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
(OUT/'SHA256SUMS.txt').write_text(''.join(q['sha256']+'  '+q['path']+'\n' for q in rows))
target=pathlib.Path(r'C:\work\LAKESHORE_R1A_DECONFOUND_EVIDENCE_20261003.zip')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in members+[OUT/'MANIFEST.csv',OUT/'SHA256SUMS.txt']:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for q in rows:assert __import__('hashlib').sha256(z.read(q['path'])).hexdigest()==q['sha256']
digest=sha(target);target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n')
print(json.dumps({'zip':str(target),'sha256':digest,'files':len(members)+2,'bytes':target.stat().st_size,'decision':decision['decision']},indent=2))
