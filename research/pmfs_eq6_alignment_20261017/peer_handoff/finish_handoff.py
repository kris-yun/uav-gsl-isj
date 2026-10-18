from pathlib import Path
import json,hashlib,csv
E=Path(__file__).resolve().parent;ROOT=E.parent.parent/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016';N=ROOT/'NATIVE7_MIN_RESEARCH_20261016';OLD=E.parent/'FSR_S2_PMFS_PAPER_BASELINE_AUDIT_V1_20261018';LIT=E.parent/'FSR_S2_PMFS_PAPER_DISCREPANCY_LITERATURE_V1_20261017'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
obs=read(E/'A2_B2_EXISTING_OBSERVATIONS.json')['runs'];banks=read(E/'A2_B2_EXISTING_OFFLINE_BANK_FILES.json')['files'];parents=sorted({Path(x['path']).parent for x in banks if x['relative_to_N'].startswith('results/shadows/')});slots=[]
for folder in parents:
 meta=read(folder/'ITEM.json');inputs=[]
 for file in sorted(folder.glob('W?.txt')):
  with file.open() as f:header=f.readline().strip()
  inputs.append(dict(path=str(file),sha256=sha(file),first_line=header))
 slots.append(dict(path=str(folder),owner_metadata=meta,owner_metadata_sha256=sha(folder/'ITEM.json'),input_maps=inputs,source_prediction_files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in folder.glob('W?_predictions.csv')],leaf_owner_files=[dict(path=str(p),sha256=sha(p)) for p in folder.glob('W?_leaf_structure.csv')],score_files=[dict(path=str(p),sha256=sha(p)) for p in folder.glob('W?_scores.csv')]))
put(E/'A2_B2_FROZEN_SLOT_OWNER_MAPPING.json',dict(slots=slots,scope='Actual pre-existing18 frozen-slot banks,54 W-context predictions. Directory names are not assumed to be identical to raw actor source-update numbers; use ITEM plus serialized map and existing ledger.',support_limitation='Fixing captured leaf owners/predictions yields a same-support score diagnostic, not a new complete recursive PMFS run after Eq6 changes.'))
summary=dict(real_runs=len(obs),source_update_snapshots=sum(len(x['schema']['native_posterior_updates.csv']['update_ids']) for x in obs),source_snapshot_rows=sum(x['schema']['native_posterior_updates.csv']['rows'] for x in obs),consumed_windows=sum(x['schema']['native_window_consumption.csv']['consumed_windows'] for x in obs),recorded_confidence1_rows=sum(x['schema']['native_posterior_updates.csv']['confidence_one_rows'] for x in obs),direct_Omega_columns_available=False,actual_historical_candidate_owner_and_rng_bank_recovered=False,author_Sep18_candidate_bank_identified=False,existing_offline_banks=dict(slots=len(slots),W_context_prediction_files=sum(len(x['source_prediction_files']) for x in slots),identity='July2024 upstream with Pro NEW_SAFE_RNG control; not historical actor RNG or Sep18 source.'),native_capture_provenance_sha256=sha(N/'CAPTURE_PROVENANCE.json'),readonly_handoff_to_research2=True,new_experiments=0,new_source_or_parameter_changes=0)
assert summary['source_update_snapshots']==42 and summary['source_snapshot_rows']==33756 and summary['consumed_windows']==660 and len(slots)==18 and summary['existing_offline_banks']['W_context_prediction_files']==54
put(E/'HANDOFF_SUMMARY.json',summary)
report='''# Eq6单因素对照：既有A2/B2资产交接

已向研究2交接可用数据，本聊天不运行新物理世界或控制。原223/508文件冻结结果保持原样。此目录仅为现有资产索引，不是新实验，也不是论文基线PASS。

## 原闭环观测和后验

共同根目录：D:\\ZYC\\A-gas\\workspace\\PMFS_OFFICIAL_REPRO_AUDIT_20261016\\NATIVE7_MIN_RESEARCH_20261016。

`input_observations/P24_A2_WALL5_VALID_V2_R01`至R03，及`P24_B2_WALL5_VALID_V2_R01`至R03，保留gas、wind、pose、commands、TF、消费窗口和原生后验导出。脚本汇总为6回合、660消费窗、42次源更新、33756个后验格状态。EXPORT_RECEIPT明确这些来自已发生的原消息，不是新轨迹；SOURCE_IDENTITY指向July2024 2e140670家族，不能改称September源版本。

关键文件是`native_window_consumption.csv`和`native_posterior_updates.csv`。后者有hit_log_odds、hit_confidence、估计风和source_probability，**没有Omega列**，也没有完整的每个消费窗后地图。6组后验中confidence==1的行数为0；这不等于精确Omega已恢复。若反演旧alpha，必须声明为受浮点/截断影响的反演值，核对当次weight参数，不能伪造原内部状态。alpha==0也可能隐藏舍入后的极小正权重。

机读索引：A2_B2_EXISTING_OBSERVATIONS.json；原文件实际SHA、schema、原始CDR身份及binary身份所在位置均已列出。

## 已有候选预测和评分

`results/shadows/P24_A2.../Uxxx`和B2对应目录中，已有18个冻结时刻、54套W风情境预测。每套包含W0/1/2.txt、*_predictions.csv、*_scores.csv、*_leaf_structure.csv、RNG位置和Gaussian表。ITEM.json、LEDGER.json用于实际槽位/源更新映射，不能只按U目录名猜编号。

这些预测属于**July2024 upstream + Pro提供安全串行RNG的新离线控制**。CAPTURE_PROVENANCE和RNG_REPLAY_NOTE明确不是历史actor的随机流，也不是作者September实现的预测库。另`capture_parity/A2_base_capture_*`及B2/角度fixture有六组录制器前后字节一致检查；它证明被动记录不改变该新控制输出，不能补回原闭环历史候选。

完整非零稀疏hit图需要按输入map合法自由格解释，缺失位置为0；占据格的整数计数不应当作概率，见原DATA_SCHEMA。现有owner支持可用于限定的同历史、同预测库评分对照；Eq6改变后重新运行递归细化，可能选择不同候选，因此固定bank不是完整PMFS重跑。

具体路径和实际SHA：A2_B2_EXISTING_OFFLINE_BANK_FILES.json、A2_B2_FROZEN_SLOT_OWNER_MAPPING.json。前者列543个匹配资产文件，并明确大型文件SHA是否现场计算；后者对54个实际预测文件另做了SHA及owner元数据索引。未找到可认证为原闭环完整owner/RNG库或September完整候选库的资产；这只是本次限定目录检查结论，不是所有归档不存在的证明。

## 非方形网格与源身份

上一轮官方缓存中的a8d5a764原样Grid2D.hpp、PMFSLib.cpp、Simulations.cpp/.hpp可直接供研究2取用，绝对路径、SHA和Git OID见RECTANGULAR_GRID_SOURCE_ENTRIES.json。它们是作者代码，并非本聊天新修复。AUTHOR_20240918_FIX.patch同时包含网格、随机数和旋转变化，不能直接套作Eq6单行补丁。

旧paper_component_probe.cpp只链接July/A6对象做过7×7数学控制，不是September非方形运行资格。端点、真实源和truth相关文件仍只供外部评价，不作为挑选参数/候选的依据。

当前缺失项是精确历史Omega逐次状态、原闭环完整候选owner/RNG银行、September同配置预测库。本次没有擅自补数、恢复运行或修改任何公式。研究2后续对照应明确以上层级。
'''
(E/'既有A2B2资产交接_zh.md').write_text(report,encoding='utf-8',newline='\n')
checks=[]
for old,name in [(OLD,'FINAL_FILES_MANIFEST_V2.json'),(LIT,'JOINT_FILES_MANIFEST.json')]:
 manifest=read(old/name)
 for x in manifest['files']:
  p=old/x['path'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'];checks.append(dict(path=str(p),matches=True))
put(E/'OLD_FROZEN_FILES_POSTCHECK.json',dict(files_checked=len(checks),all_actual_SHA_match=True))
files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in E.rglob('*') if p.is_file()]
put(E/'FILES_MANIFEST.json',dict(files=files,not_a_compressed_package=True))
for x in files:assert sha(E/x['path'])==x['sha256']
print(json.dumps(dict(summary=summary,handoff_files=len(files),old_frozen_files_checked=len(checks)),ensure_ascii=False))
