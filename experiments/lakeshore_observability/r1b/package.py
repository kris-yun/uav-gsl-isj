"""Delivery only: immutable input audit, plots, replayable ZIP and CRC/SHA verification."""
import subprocess,shutil,zipfile,datetime,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *
decision=json.loads((OUT/'R1B_FINAL_DECISION.json').read_text())
g=pd.DataFrame(decision['scene_gates'])
summary=pd.read_csv(OUT/'endpoint_summary.csv')
main=summary[(summary.threshold_factor==1)&(summary.height==10)&(summary.prefix_s==300)]
src=pd.read_csv(OUT/'source_region_errors.csv')
fig,axs=plt.subplots(1,2,figsize=(13,4),layout='constrained')
for arm in ['oracle','uniform','profile','negative_uniform']:
 q=main[main.arm==arm].set_index('scene').loc[SCENES]
 axs[0].plot(range(6),100*q.top1,'o-',label=arm);axs[1].plot(range(6),q.candidate_error,'o-',label=arm)
for ax,label in zip(axs,['Top1 (%)','Mean candidate error (m)']):
 ax.set_xticks(range(6),SCENES,rotation=40,ha='right');ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=8)
axs[0].set_ylim(0,105);fig.suptitle('R1B independent seeds: 10 m,300 s,release unknown')
fig.savefig(OUT/'R1B_primary_endpoints.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained')
for row,strength in enumerate([1,2]):
 for col,arm in enumerate(['uniform','profile']):
  ax=axs[row,col]
  for front in [90,120,150]:
   q=src[(src.scene==f'XF{front}_F{strength}')&(src.arm==arm)];ax.plot(q.source_x,100*q.error_fraction,'o-',label=f'front{front}m')
  ax.set_title(f'F{strength} / {arm}');ax.set_xlabel('True source x (m)');ax.set_ylabel('Wrong candidate (%)');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Does the error region follow the front? Fixed source grid20/50/80m')
fig.savefig(OUT/'R1B_source_region_tracking.png',dpi=150);plt.close(fig)
checks={};oldcount=0
for folder in [OLD,ROOT/'evidence/lakeshore_r1a_deconfound_20261003']:
 m=pd.read_csv(folder/'MANIFEST.csv')
 for q in m.itertuples():assert sha(ROOT/q.path)==q.sha256,q.path
 checks[folder.name+'_unchanged_files']=len(m);oldcount+=len(m)
for line in (OUT/'PRE_GAS_SHA256SUMS.txt').read_text().splitlines():
 h,name=line.split('  ',1);assert sha(ROOT/name)==h,name
checks['final_pre_gas_freeze_unchanged']=True
binary=subprocess.check_output(['ssh',HOST,'sha256sum '+ADAPTER+' '+LIB],text=True)
(OUT/'runtime_binary_hashes_after.txt').write_text(binary);assert binary==(OUT/'runtime_binary_hashes_before.txt').read_text();checks['native_runtime_unchanged']=True
# Re-run one new-seed case and compare exported bytes, without touching original output.
tag='F_XF90_F1_x20_y-20_r5_seed32001'
cmd=PREFIX+'export GADEN_RNG_SEED=32001; '+ADAPTER+' '+REMOTE+'/F_XF90_F1.csv '+REMOTE+'/repeatability.csv 20 -20 5 > '+REMOTE+'/repeatability.log 2>&1; sha256sum '+REMOTE+'/'+tag+'.csv '+REMOTE+'/repeatability.csv'
r=subprocess.check_output(['ssh',HOST,cmd],text=True);assert len(r.splitlines())==2 and r.splitlines()[0].split()[0]==r.splitlines()[1].split()[0]
(OUT/'native_repeatability_hashes.txt').write_text(r);checks['new_seed_native_byte_repeatability']=True
obs=pd.read_csv(OUT/'observation_manifest.csv');assert len(obs)==3888 and obs.rows.sum()==4665600
assert len(list((OUT/'native_logs').glob('*.log')))==3888
checks['new_realizations']=3888;checks['native_rows']=4665600
# Validate wind at actual trajectory query locations, in addition to random native parity.
winderrors=[]
for env in ENVS:
 d=pd.read_csv(OUT/'observations'/f'{env}_x20_y-20_r5_seed32001.csv');wind=pd.read_csv(HERE/'wind'/f'{env}.csv')
 idx=np.floor((d[['x','y','z']].to_numpy()-np.array([-100,-100,-5]))/5).astype(int)
 flat=idx[:,2]*3200+idx[:,1]*80+idx[:,0];expected=wind[['U:0','U:1','U:2']].to_numpy()[flat];error=float(abs(expected-d[['u','v','w']].to_numpy()).max());assert error<1e-5,(env,error)
 winderrors.append(dict(environment=env,path_query_wind_max_error=error,query_rows=len(d)))
pd.DataFrame(winderrors).to_csv(OUT/'actual_path_wind_parity.csv',index=False)
checks['all18_actual_path_wind_parities_pass']=True
write_json('DELIVERY_VALIDATION.json',checks)
runtime='''# R1B runtime audit

ROS2 Humble / native GADEN core3.0, unchanged existing PF_DEI_V3_GADEN_BUILD libgaden.so; native CLI adapter uses official ParseOpenFoamVectorCloud, RunningSimulation, SampleWind and SampleConcentration. Exact adapter/lib SHA in before/after files, equality asserted. Isolated build Git links are historically broken, so no unsupported exact source commit is asserted. No package/kernel/House change.

18 regular3D wind CSVs, 99,200 cells each,80x40x31 at5m. Six physically divergence-consistent full fronts; six uniform and six x-invariant profile controls. Front90/120/150m; amplitudes are unchanged original F1/F2 values, not re-normalized after front translation. Original XF120 full field bytes preserved. Native random100-point parity and all1200 actual trajectory wind queries per field checked. Ground and outlet geometry identical to prior experiments.

Methane,298K/1atm,120s warmup,300s trajectory query,1Hz,filament release5/10/20,noise/sigma/growth unchanged. Seeds32001..32008,OMP1 per native process,4 independent processes. New-seed byte repeatability checked. Native observation output still has10/30/60/100m for unchanged adapter; only10m primary and30m secondary analyzed. This is native filament physics including methane buoyancy, not thermally driven CFD/LES.
'''
(OUT/'runtime_audit.md').write_text(runtime,encoding='utf-8')
table=g[['scene','arm','oracle_top1','baseline_top1','penalty_pp','mean_error_m','error_fraction','mean_x_bias','direction_fraction','consistent_seed_count','all_six']].to_markdown(index=False,floatfmt='.4f')
locks='\n'.join(f"- F{q['strength']} / {q['arm']}: most-affected x={[x if c is not None else 'undefined (no errors)' for x,c in zip(q['most_affected_source_x'],q['error_centroid_x'])]}; error-weighted centroids={q['error_centroid_x']}; locked={q['front_locked']}" for q in decision['front_lock'])
post=pd.read_csv(OUT/'R1A_POSTHOC_EXPLORATORY_summary.csv');post=post[(post.threshold_factor==1)&(post.height==10)&(post.prefix_s==300)]
report=f'''# R1B 湖风锋空间失配确认报告

最终判定：`{decision['decision']}`。六项门槛全部通过的场景 {decision['passed_scene_count']}/6；不计front-lock时通过的场景 {decision['local_mismatch_scene_count']}/6；全部uniform负对照是否>=90%：{decision['negative_controls_pass']}。

保持原`R1_HOLD_WEAK_OR_UNSTABLE`及`R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION`。未运行R1.1、R2、PMFS、闭环、主动感知或高保真CFD。未恢复垂直抬升主线，未改源网格、阈值或锋面位置来过门。判定未通过时停止后续lake-front机制主线；HOLD也不能作为PASS继续。

## 旧1944数据的探索复核

{post.to_markdown(index=False,floatfmt='.5f')}

该复核仅为exploratory，不回改旧判定。单次Beta先验的合并模板复现用户给出的F1/C06及F2/C08数值。实现中先对三档释放率的21个训练样本合并，再计算(1+hits)/23；三档各贡献七个seed、等权。先按每档加先验再平均会引入三份先验并产生小差别，第一版输入草案与最终输入冻结均保留，澄清发生在没有任何新32001+气体输出前。

## 冻结与执行

完整阅读协议commit f4d322a82ea21c1097108d71cb2cdc37e4233c76。六个全锋面、六个uniform、六个profile场；固定9源x20/50/80、y-20/0/20、z1；release5/10/20、独立新seeds32001..32008，总3888个realization、4,665,600行。原二次评分和新矩阵均使用相同的release-unknown estimator。均匀场匹配原生z10查询所在网格的300s轨迹平均u；profile在每个原生高度匹配同一轨迹平均u，没有使用气体结果来匹配风。

主终点固定z10、300s、阈值.001ppm。30/60/120s前缀、30m、.5/2x阈值均作为次要/敏感性保存，没有选择它们来替代主gate。每次测试从所有9候选和三档release模板移除配对seed。Brier取300个时间点平均，保留候选分数、rank、margin、分数相同候选的等权预测。误差为候选欧氏误差的期望；错误率=1-fractional Top1，bias为预测x减真x的期望。固定路径源映射为template指纹分类，不是闭环定位或跨天气泛化。

## 主结果

{table}

方向比例的分母是全部错误，包括只在y错而x不变的错误。>=6/8seed要求同seed oracle-baseline Top1差>0且平均x-bias与总体错误主方向相同。每个场景必须由同一个baseline arm满足全部六项，不能从两个arm中拼凑门槛。negativecontrol为每场景uniform truth+同uniformmodel的release-unknown评分。

## 错误区域是否随front移动

{locks}

F1/XF150主终点没有任何错误，因此不存在受影响源区域。原始JSON的most_affected_source_x=50仅是所有错误率同为0时的并列中心计算值，不能解释为错误区域移动到了50m；上表明确标为undefined。F2三位置的最易误判源均为x20，错误率随front移向150m显著减少，并未发生要求的区域移动。

由于协议未给出移动的数值公式，在新气体生成前冻结保守的离散源网格实现：按y/release/seed平均错误率最高的source-x定义受影响区域；并列最高用x均值。对同一强度和同一arm，90->120->150三场景均有错误、区域非递减且首尾至少移动30m才通过。错误率加权centroid同时报告但不替换gate。三锋面均位于有限源网格的下游，这一实验几何限制明确保留；若区域总固定在同一源位置，就无法排除固定源位置/传播距离解释。不扩密、不移动源网格补救。

## 边界与下一步

误差方向一致或单场景模型失配本身不足以证明front-relative机制。只有>=4/6场景满足全部要求并通过负对照才允许PASS。若FAIL/HOLD，本任务在确认门处结束；不会继续CFD或主动感知。非methane气体robustness只在PASS后执行，本次状态见FINAL_DECISION及交付说明。当前全部结果是298K固定native methane参数下的机制测试，不是实测湖岸定位误差，也不外推VOC。真实热力湖岸机制最终需要独立热力CFD/LES复核。

## 复现与核验

新生成/评分脚本在experiments/lakeshore_observability/r1b；config与PRE_GAS_SHA256SUMS锁定分析输入。原R1及R1A共{oldcount}条MANIFEST均逐一复核无改动。运行前后runtime binary SHA一致，新seed原生再跑导出CSV字节一致，18风场nativequery随机点与实际pathquery通过。ZIP带完整新观察、log、候选分数、次要终点、JSON判定、两张PNG及旧exploratory评分所用1944观察和关键依赖。MANIFEST.csv和SHA256SUMS列出每个有效成员；ZIP自身SHA在旁边sha256文件。

已有文件离线重评分：python experiments/lakeshore_observability/r1b/score.py；旧探索重评分：同脚本加posthoc。需numpy/pandas（报告需要matplotlib/tabulate）。原生重新生成还需相同VM已有adapter/library及SSH访问；ZIP不包含虚拟机或GADEN动态库。不要在原冻结交付目录随意重跑prepare并覆盖输入，复现请解压到新目录。
'''
(OUT/'R1B_REPORT_zh.md').write_text(report,encoding='utf-8')
(OUT/'.gitattributes').write_text('* -text -whitespace\n',encoding='utf-8')
protocol=OUT/'protocol';protocol.mkdir(exist_ok=True)
for name in ['README.md','GENERATION_PLAN.md','R1A_POSTHOC_MODEL_MISMATCH_AND_R1B.md']:shutil.copyfile(EXP/name,protocol/name)
write_json('DELIVERY_PROVENANCE.json',{'protocol_commit':'f4d322a82ea21c1097108d71cb2cdc37e4233c76','branch':'research/lakeshore-observability-r0-r2-20261003','decision':decision['decision'],'old_observations_in_zip':1944,'new_observations_in_zip':3888,'gas_robustness':'conditional on PASS; see final decision, not run for FAIL/HOLD','prior_evidence_unchanged':True})
deps=[EXP/'scripts/gaden_adapter.cpp',OLD/'fixed_path_contract.csv',OLD/'wind_F1_QC.json',OLD/'wind_F2_QC.json',EXP/'generated_project/wind_simulations/F1/wind_0.csv',EXP/'generated_project/wind_simulations/F2/wind_0.csv']
deps+=sorted((ROOT/'evidence/lakeshore_r1a_deconfound_20261003/observations').glob('*.csv'))
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['MANIFEST.csv','SHA256SUMS'])+sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)+deps
files=sorted(set(files));manifest=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
pd.DataFrame(manifest).to_csv(OUT/'MANIFEST.csv',index=False)
(OUT/'SHA256SUMS').write_text(''.join(q['sha256']+'  '+q['path']+'\n' for q in manifest),encoding='utf-8')
zip_path=pathlib.Path('C:/work/LAKESHORE_R1B_FRONT_MISMATCH_EVIDENCE_20261003.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files+[OUT/'MANIFEST.csv',OUT/'SHA256SUMS']:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for q in manifest:assert hashlib.sha256(z.read(q['path'])).hexdigest()==q['sha256'],q['path']
digest=sha(zip_path);zip_path.with_suffix('.zip.sha256').write_text(digest+'  '+zip_path.name+'\n')
print(json.dumps({'zip':str(zip_path),'sha256':digest,'bytes':zip_path.stat().st_size,'members':len(files)+2,'decision':decision['decision']},indent=2))
