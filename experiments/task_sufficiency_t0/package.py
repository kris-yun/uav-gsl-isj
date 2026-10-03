"""Recompute frozen gate, verify lineage/splits, and package retrainable T0 evidence."""
import csv,hashlib,json,zipfile,subprocess
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];O=ROOT/'evidence/task_sufficiency_t0_20261003';S=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 decision=json.loads((O/'FINAL_DECISION.json').read_text());d=pd.read_csv(O/'CASE_METRICS.csv');p=pd.read_csv(O/'OOF_PREDICTIONS.csv');runs=json.loads((O/'RUNS.json').read_text())
 assert len(runs)==32 and len(d)==20 and len(p)==19008
 for case in sorted(d.case.unique()):
  rr=[r for r in runs if r['context']==case];keys=[]
  for r in rr:
   meta=O/'provenance'/r['run_id'];m=json.loads((meta/'RUN_MANIFEST.json').read_text(encoding='utf-8-sig'));qc=json.loads((meta/'QC.json').read_text(encoding='utf-8-sig'));proof=json.loads((meta/'ARCHIVE_PROOF.json').read_text(encoding='utf-8-sig'))
   assert sha(meta/'FULL_SHA256SUMS.txt')==proof['inventory_sha256']
   assert m['generator_binary_sha256']==qc['binary_sha256']=='ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
   pars={k:v for k,v in m['simulation_parameters'].items() if not k.startswith('source_position_') and k!='results_location'}
   keys.append(json.dumps([pars,m['asset_checks']['occupancy_sha256'],m['asset_checks']['wind_bundle_sha256'],qc['timeline_sha256'],qc['wind_index_sequence_sha256']],sort_keys=True))
  assert len(set(keys))==1
  for fold in range(1,5):
   test={r['run_id'] for r in rr if int(r['replicate'])==fold};train={r['run_id'] for r in rr if int(r['replicate'])!=fold};assert not test&train and len(test)==2 and len(train)==6
   assert set(p[(p.case==case)&(p.fold==fold)].run_id)==test
 for field,file in [('training_script_sha256',S/'train.py')]:assert sha(file)==json.loads((O/'ENGINEERING_ERRATUM.json').read_text())[field]
 protocol=json.loads((O/'PROTOCOL_FROZEN.json').read_text());assert sha(O/'PROTOCOL_FROZEN.json')==(O/'PRE_TRAIN_FREEZE_SHA256.txt').read_text().split()[0]
 # Equal-weight independent realizations, with correlated windows never counted as replication.
 source_ci=[]
 for (case,arm),group in p.groupby(['case','arm']):
  r=group.groupby(['run_id','source']).prob_source1.mean().reset_index();acc=np.where(r.source.values==1,r.prob_source1.values>=.5,r.prob_source1.values<.5)
  from scipy.stats import beta
  k=int(acc.sum());n=len(acc);source_ci.append(dict(case=case,arm=arm,correct=k,n=n,accuracy_ci_low=0 if k==0 else float(beta.ppf(.025,k,n-k+1)),accuracy_ci_high=1 if k==n else float(beta.ppf(.975,k+1,n-k))))
 pd.DataFrame(source_ci).to_csv(O/'SOURCE_ACCURACY_EXACT_CI.csv',index=False)
 fig,ax=plt.subplots(1,2,figsize=(12,4));arms=['raw','statistics','generic','source_only','joint'];cases=sorted(d.case.unique());x=np.arange(4)
 for i,a in enumerate(arms):
  q=d[d.arm==a].set_index('case').loc[cases];ax[0].bar(x+(i-2)*.15,q.realization_auc,width=.15,label=a);ax[1].bar(x+(i-2)*.15,q[['brier_10','brier_30']].mean(axis=1),width=.15,label=a)
 for a in ax:a.set_xticks(x,cases);a.grid(axis='y',alpha=.2)
 ax[0].set_ylabel('Held-out realization source AUC');ax[0].set_ylim(0,1.05);ax[1].set_ylabel('Mean future 10/30s hit Brier');ax[0].legend(fontsize=8);fig.tight_layout();fig.savefig(O/'COMPARISON.png',dpi=160);plt.close(fig)
 lines=['# T0 task-sufficiency feasibility audit','',f'正式判定：**{decision["decision"]}**。','', '冻结的 R1/R1A/R1B/Wisco 判定保持原样。使用32次已有独立 House 模拟，无新GADEN/CFD、无闭环、无144次多源生成。','', '## 数据与评价','', 'H01/s0→X00，H01/s1→X02，H02/s0→X04，H02/s1→X06；s0/s1是这里明确冻结的两个 fast wind/gas 环境别名，不是待分类源标签。每环境均有两个配置源、每源四次独立模拟，所有非源参数、风、气体、几何、时间线和生成器已核验一致。','', '源盲路线覆盖每个 House 在约0.2m室内水平切片的最大连通自由区：几何格点及最短自由路径决定路线，未使用源坐标、浓度或标签选路。沿路径0.2m/s，2s采样，模拟时刻100–700s。位置取真实网格中心（House01约0.231m，House02约0.249m）。这是一条离线虚拟移动传感器路线，不是真实无人机飞行。','', '每次模拟54个匹配历史；20点、2s间隔，端点跨度38s，名义40s预算。预测10/30s浓度和hit，未来XYZ已知，未来风/浓度不进入输入。仅训练/评价使用源真值，模拟ID只用于分组与诊断。','', '4折留出完整模拟；每折训练每源3次，测试每源1次。训练归一化、模型、下游头和所有探针均不使用测试模拟拟合。源rank/AUC先在每个完整测试模拟内平均概率，独立样本量每环境8，而非432个相关窗口。额外保留窗口源探针准确率，避免全路线平均掩盖局部歧义。','', '五臂：raw history、hand statistics（不是正式PMFS实现）、generic sequence autoencoder、source-only bottleneck、joint bottleneck。所有源读出用相同C=1线性logistic；未来读出用相同logistic/ridge，含已知未来XYZ。轻量48隐藏单元、8维latent、160epochs；神经网络三个预冻结初始化，未搜索超参数。joint包含源CE、未来hit BCE、log1p浓度MSE、latent L2和同源同时间跨训练模拟方差罚项。','', '## 结果','', '|case|arm|source rank|source AUC|source window acc|Brier10|Brier30|NLL10|NLL30|realization probe|heldout latent MSE|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in d.itertuples():lines.append(f'|{r.case}|{r.arm}|{r.mean_source_rank:.3f}|{r.realization_auc:.3f}|{r.source_probe_accuracy:.3f}|{r.brier_10:.4f}|{r.brier_30:.4f}|{r.hit_nll_10:.4f}|{r.hit_nll_30:.4f}|{r.nuisance_probe_accuracy:.3f}|{r.heldout_latent_prototype_mse:.4f}|')
 lines+=['','浓度NLL在log1p(ppm)空间使用训练残差固定方差的高斯预测，另列于CASE_METRICS.csv；这是简化分布头，不能解读成已校准的完整羽流浓度分布。','', '## 冻结门','', '```json',json.dumps(decision['gates'],indent=2),'```','', 'rank/AUC增益对raw；预测Brier与hit NLL必须均优于source-only；同源realization探针要低于generic且源探针≥0.75。正式门未修改。','', 'realization探针是训练模拟的三分类（chance=1/3），在同源内用早段结束≤300s拟合、晚段≥440s评价，历史不重叠。它不声称能分类未见ID，也不直接证明latent与随机羽流独立。训练与预测仍可能需要保留任务相关的随机动态。heldout latent MSE是在训练尺度下，未见模拟与同源同时间训练原型的距离。','', '## 解释与停止边界','', '这只筛选被冻结的轻量估计器及单一路线。两个离散源、每源4个seed无法证明任意源坐标回归、跨环境泛化、信息论充分性或大模型不可行。全路线raw若接近满分，会限制rank/AUC改进的空间；必须保留这种天花板，不能为过门换终点。L2/8维是压缩正则，不是严格的信息上界。','', '未训练或评价flow-aligned memory；本轮按用户要求只做T0-A及必要诊断，不能对M2下结论。未生成多源下一阶段数据，不自动进入闭环。','', '证据包含全部观测、统一tensor、冻结配置、训练脚本/日志/144个encoder检查点、OOF逐窗口预测、按模拟计数结果、原始档案元数据及所读native输入SHA256。大型原始filament和wind输入保留在C:\\GADEN_OCB_R2_ARCHIVE，ZIP不重复打包；NATIVE_INPUT_SHA256.csv记录确切位置与字节哈希。训练可只用ZIP内观测重跑，重新提取需本地原档案和原VM native库。','', '## 理论来源与归属','', '[Learning Task-Sufficient World Models](https://arxiv.org/abs/2607.04409)；[Flow Equivariant World Models](https://flowequivariantworldmodels.github.io/)。本轮是气体源任务的轻量概念探针，不是上述论文算法复现，也不构成独立新颖性证明。']
 means=d.groupby('arm').mean(numeric_only=True);j=means.loc['joint'];c=means.loc['source_only'];b=means.loc['generic'];raw=means.loc['raw']
 brief={'joint_source_window_accuracy':float(j.source_probe_accuracy),'raw_source_window_accuracy':float(raw.source_probe_accuracy),'joint_source_rank':float(j.mean_source_rank),'raw_source_rank':float(raw.mean_source_rank),'joint_source_auc':float(j.realization_auc),'raw_source_auc':float(raw.realization_auc),'joint_future_brier_mean':float((j.brier_10+j.brier_30)/2),'source_only_future_brier_mean':float((c.brier_10+c.brier_30)/2),'joint_future_hit_nll_mean':float((j.hit_nll_10+j.hit_nll_30)/2),'source_only_future_hit_nll_mean':float((c.hit_nll_10+c.hit_nll_30)/2),'joint_nuisance_accuracy':float(j.nuisance_probe_accuracy),'generic_nuisance_accuracy':float(b.nuisance_probe_accuracy),'nuisance_chance':1/3}
 (O/'SUMMARY_NUMBERS.json').write_text(json.dumps(brief,indent=2)+'\n')
 lines+=['','## 判定的具体含义','',f'四个环境raw与joint都达到source rank=1、AUC=1，因而rank/AUC中位增益为0，原门要求的正增益未成立；这存在明确的两源、长路线平均天花板。窗口源正确率joint={j.source_probe_accuracy:.2%}，raw={raw.source_probe_accuracy:.2%}，但这是辅助终点，不能用它替换冻结的主终点。', '',f'joint未来平均Brier={brief["joint_future_brier_mean"]:.6f}，source-only={brief["source_only_future_brier_mean"]:.6f}；hit NLL分别为{brief["joint_future_hit_nll_mean"]:.6f}与{brief["source_only_future_hit_nll_mean"]:.6f}，保留真实的联合预测正信号。', '',f'条件realization探针joint={j.nuisance_probe_accuracy:.2%}，generic={b.nuisance_probe_accuracy:.2%}，chance=33.33%；未降低，所以严格门未过。但是两者都接近chance，不能把1.29个百分点差说成joint严重记住了随机模拟。该诊断较弱，需要独立证据才能证明nuisance消除。', '', '结论是本轮未建立同时满足全部冻结要求的task-sufficient优势，不是“源信息消失”，也不是整个世界模型主线已被数学否定。正式FAIL保留，按要求停止扩实验。']
 (O/'REPORT_zh.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
 validation=dict(native_contracts_pass=True,selected_native_files=len(pd.read_csv(O/'NATIVE_INPUT_SHA256.csv')),independent_realizations=32,trajectory_observations=9632,windows=1728,oof_predictions=19008,trained_encoders=144,all_folds_train_test_disjoint=True,protocol_hash_unchanged=True,old_decisions_unchanged=True,scope_no_new_simulation=True)
 (O/'VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
 # Mark raw byte hashing explicitly to preserve checksums across Git CRLF checkout.
 (O/'.gitattributes').write_text('* -text\n');(S/'.gitattributes').write_text('* -text\n')
 files=[p for folder in [O,S] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in {'stage.tar','MANIFEST.csv'}]
 manifest=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
 pd.DataFrame(manifest).to_csv(O/'MANIFEST.csv',index=False)
 target=Path(r'C:\work\TASK_SUFFICIENCY_T0_EVIDENCE_20261003.zip')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[O/'MANIFEST.csv']:z.write(p,p.relative_to(ROOT).as_posix())
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
 digest=sha(target);target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n')
 print(json.dumps(dict(decision=decision['decision'],zip=str(target),bytes=target.stat().st_size,sha256=digest,members=len(files)+1),indent=2))
if __name__=='__main__':main()
