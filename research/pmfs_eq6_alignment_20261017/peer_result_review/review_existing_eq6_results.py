from pathlib import Path
import json,csv,math,hashlib,collections
E=Path(__file__).resolve().parent;P=E.parent.parent/'workspace/PMFS_EQ6_ALIGNMENT_20261017';OLD=E.parent/'FSR_S2_PMFS_PAPER_BASELINE_AUDIT_V1_20261018'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
raw=OLD/'source/AUTHOR_FIX_20240918/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp';originals=list((P/'author_release').rglob('PMFSLib.cpp'));variants=list((P/'paper_eq6').rglob('PMFSLib.cpp'));assert len(originals)==1 and len(variants)==1
original=originals[0];variant=variants[0];assert sha(raw)==sha(original)==read(P/'PATCH_CHECK.json')['original_sha256']
a=original.read_text();b=variant.read_text();old='double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);';new='double exponent = -(cell.omega * cell.omega) / std::pow(settings.confidenceMeasurementWeight, 2);';assert a.count(old)==1 and a.replace(old,new)==b
assert sha(variant)==read(P/'PATCH_CHECK.json')['patched_sha256']
cells=list(csv.DictReader((P/'analysis_v2/CELL_CONFIDENCE_AND_SOURCE.csv').open()));comp=list(csv.DictReader((P/'analysis_v2/SOURCE_COMPARISON.csv').open()));group=collections.defaultdict(list)
for row in cells:group[row['context']].append(row)
rows=[]
for context,items in group.items():
 base=[float(x['native_source_probability']) for x in items];paper=[float(x['paper_eq6_source_probability']) for x in items];tv=.5*sum(abs(x-y) for x,y in zip(base,paper));pair=[x for x in comp if x['context']==context];assert len(pair)==2
 assert all(abs(tv-float(x['tv_from_native']))<1e-12 for x in pair)
 assert abs(sum(base)-1)<1e-12 and abs(sum(paper)-1)<1e-12
 truth=int(pair[0]['truth_cell']);truthrows=[x for x in items if int(x['cell_index'])==truth];supported=bool(truthrows)
 assert supported==(pair[0]['truth_supported']=='True')
 ranks={}
 if supported:
  for arm,col in [('author_confidence','native_source_probability'),('paper_eq6_only','paper_eq6_source_probability')]:
   p=float(truthrows[0][col]);rank=1+sum(float(x[col])>p for x in items);saved=next(x for x in pair if x['arm']==arm);assert rank==int(saved['truth_strict_rank']);ranks[arm]=rank
 rows.append(dict(context=context,free_cells=len(items),tv=tv,truth_cell=truth,truth_supported=supported,recomputed_strict_truth_ranks=ranks,total_source_mass_native=sum(base),total_source_mass_eq6=sum(paper)))
commands=read(P/'execution/COMMANDS.json');assert len(commands)==6 and all(x['exit_code']==0 for x in commands)
parity=read(P/'analysis_v2/PARITY_CHECKS.json');assert sum(x['archived_candidates'] for x in parity['checks'])==614
decision=read(P/'analysis_v2/DECISION.json');assert not decision['full_paper_reproduction'] and not decision['closed_loop_gain_tested'] and not decision['formal_figures_8_10_11_statistical_comparison_eligible']
files=[raw,original,variant,P/'PATCH_CHECK.json',P/'paper_eq6_only.patch',P/'analysis_v2/CELL_CONFIDENCE_AND_SOURCE.csv',P/'analysis_v2/SOURCE_COMPARISON.csv',P/'analysis_v2/PARITY_CHECKS.json',P/'analysis_v2/DECISION.json',P/'execution/COMMANDS.json',P/'execution/RESULT.json',P/'HISTORICAL_2024_ELIGIBILITY.json']
put(E/'READONLY_RESULT_REVIEW.json',dict(status='PASS_RECOMPUTED_FIXED_SUPPORT_TV_RANKS_SOURCE_IDENTITY_NOT_FULL_PMFS',source_commit='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533',only_one_formula_line_modified=True,scope='Independent read-only recheck of existing results. No rerun of C++ binary, candidate propagation, physics or ROS.',diagnostic_inputs='2026 corrected-wind A2/B2 recorded Omega and candidate maps; not September trial histories',rows=rows,native_score_max_difference_reported=max(x['max_native_logscore_error'] for x in parity['checks']),native_posterior_max_difference_reported=max(x['max_native_posterior_error'] for x in parity['checks']),native_parity_scope='Reported by peer command results; this checker independently recalculates cell-mass TV, ranks, source identity and patch isolation, not all614 forward-map scores.',eligibility=decision,files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files],new_scientific_jobs=0))
report='''# Eq6结果只读复核

已核对研究2的既有产物，本聊天没有重跑二进制、传播或ROS。

作者原始PMFSLib.cpp与已核验官方a8d5a764字节一致，变体恰好只替换累计量平方这一行。六条既有C++构建/评分命令退出码均0；它们是数学/冻结预测评分控制，不是完整September PMFS运行资格。

我从逐格CSV独立重算了四个固定支持集的总变差、归一化质量和真源严格排名：

| 记录 | 后验总变差 | 真源排名原生→Eq6 |
|---|---:|---|
| A2_update_0 | 0.06833977 | 141→142 |
| A2_update_1 | 0.02426207 | 112→110 |
| B2_update_0 | 0.06584551 | 真源674不在记录支持域 |
| B2_update_1 | 0.08366402 | 真源674不在记录支持域 |

这些输入属于2026修风后的受限诊断，不能称作者2024原实验或September候选库。A2排名一退一进，没有一致改进证据；B2两条记录必须先作为候选域资格问题处理，不能归因于Eq6。固定候选树/轨迹还排除了改变Eq6后可能发生的递归细化和动作变化，不能据此声称闭环定位受益。

完整论文HOLD保留：团龄覆盖规律未明确、原实验snapshot/全参数仍未对应，2024六回合也缺直接Omega和历史候选库。先前真实数据和版本证据不变。原始结果目录为workspace/PMFS_EQ6_ALIGNMENT_20261017，详细复算及源文件SHA见READONLY_RESULT_REVIEW.json。
'''
(E/'Eq6受限对照复核_zh.md').write_text(report,encoding='utf-8',newline='\n')
put(E/'FILES_MANIFEST.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in E.iterdir() if p.is_file()]))
print(json.dumps(dict(status='verified',contexts=rows,full_S2_enabled=False,new_jobs=0),ensure_ascii=False))
