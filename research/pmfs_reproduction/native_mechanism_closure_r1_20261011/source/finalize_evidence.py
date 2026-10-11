from common_n import *
import os,csv,shutil,numpy as np
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011')
parent=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
for cid in ['C7','K2']:
 src=parent/f'native_reference_evidence/realizations/{cid}_0';dest=RAW/f'support/OFF_original/{cid}_0';dest.mkdir(parents=True,exist_ok=True)
 for p in src.iterdir():
  if p.name=='ALL_FRAME_SHA256_AND_TIME.csv' or p.name.startswith('RNG.'):shutil.copy2(p,dest/p.name)
(CORE/'source/portable').mkdir(parents=True,exist_ok=True)
shutil.copy2(WORK/'verify_native_mechanism_bundle.py',CORE/'source/portable/verify_native_mechanism_bundle.py')
excluded={str(D/'factorial'/r['logical_directory'].split('/factorial/')[1]).lower() for r in load(CORE/'OWN_WIND_STORAGE_DEDUPLICATION.json')['records']}
size=0
for directory,dirs,files in os.walk(D):
 dirs[:]=[n for n in dirs if str(Path(directory)/n).lower() not in excluded]
 size+=sum((Path(directory)/n).stat().st_size for n in files)
corebytes=sum(p.stat().st_size for p in CORE.rglob('*') if p.is_file());rawbytes=sum(p.stat().st_size for p in RAW.rglob('*') if p.is_file());final=load(CORE/'runtime_ledgers/COLD_FRESH_LEDGER.json')
qualified=[]
for sub in [D/'factorial',D/'fresh/realizations']:
 qualified.extend(load(p) for p in sub.glob('*/QUALIFICATION.json'))
assert len(qualified)==38 and all(r['physical_qualification']=='PASS' for r in qualified)
calls=final['native_2D_forward_calls'];assert calls==11268 and calls<24000;assert final['offline_wall_s']<1800
disk=size+corebytes+rawbytes+315529864;assert disk<6442450944
rss_values=[r['peak_RSS_bytes'] for r in qualified if 'peak_RSS_bytes' in r]
rss_values += [r['peak_RSS_bytes'] for r in final['records']+load(CORE/'runtime_ledgers/COLD_NATIVE_LEDGER.json')['records']]
rss_values += [r[s]['sampled_process_group_peak_RSS_bytes'] for r in qualified for s in ['generation','native_response'] if s in r]
rss=max(rss_values);assert rss<1610612736
dump(CORE/'FINAL_RESOURCE_AND_EXECUTION_SUMMARY.json',dict(status='REGISTERED_BUDGETS_MET',physical_calls=38,technical_physics_retries=0,native_2D_forward_calls=calls,offline_native_wall_s=final['offline_wall_s'],primary_histories=18,primary_updates=54,physics_qualified=38,peak_recorded_RSS_bytes=rss,unique_data_bytes=size,core_bytes=corebytes,raw_bytes=rawbytes,approved_external_binary_bytes=315529864,current_new_unique_bytes_including_package_sources=disk,cap_new_disk_bytes=6442450944,VM_root_free_bytes=load(CORE/'RUNTIME_CLOSEOUT.json')['root_free'],owned_running_processes=load(CORE/'RUNTIME_CLOSEOUT.json')['owned_processes'],navigation_goals=0,new_CFD=0,network_training=0,elapsed_task_wall_s=time.time()-load(WORK/'ENTRY_TIME.json')['start_unix'],note='Count includes preserved incorrect thin-initialization shadow, point technical corrections, anchors, and all primary histories; copied ready point artifacts not counted twice. Archive/review copies will be included in final packaging accounting.'))
dump(CORE/'STAGE_COMPLETION_DECISION.json',dict(A='PASS_NATIVE_ANCHORS_AND18_COMPLETE_CORE_HISTORIES',B='PASS_SAME_BANK_READOUT_AND_OPERATOR_COMPARISONS',C='PASS2_FULL_OFF_PLUS30_FACTORIAL_INTERVENTIONS',D='PASS_FIXED_LIBRARY_ATTRIBUTION_BOUNDED_CAUSAL_SCOPE',E='PASS6_PRECOMMITTED_NEW_REALIZATIONS_ALL_ENDPOINTS',overall='CONSTITUENT_MECHANISM_SUPPORT_WITH_COUNTEREXAMPLES',full_map_treatment='NOT_TESTED',next='STOP_FOR_INDEPENDENT_REVIEW'))
write=CORE/'TECHNICAL_RESULT_AUTHORITY_zh.md'
write.write_text('''# 主结果与技术影子分支

主原生结果：QUALIFIED_N0_COMPLETE_MAP_RESULTS.csv、QUALIFIED_FRESH_N0_COMPLETE_MAP_RESULTS.csv，RAW/support/native全部18条历史。主点源：QUALIFIED_N_POINT_*。NATIVE_*无QUALIFIED前缀及N_POINT_*为初始化修正前技术影子，保留以解释修复，不计主要端点。原历史E3/B4冻结成功及错误收敛并未变化。

第一次薄入口错误在于把未初始化相位0与预加载缓存结合；原算法Gaussian懒初始化发生在初始释放之后，相位19。修正冷入口只恢复原Uniform状态并由原函数按原顺序初始化。冷锚点包括图、释放点、初始缓存/顺序、RNG与评分全匹配；10点图的ready初态明确。

OTHER技术问题：代码include路径、序列化列名、HGFS不支持symlink、资源计数重复CFD副本、协调器错误消息的路径字符串替换。相应原日志与修复源码保留。新物理气体38次均合格，无新物理重试，无通过更换种子救结果。

核验脚本为只读Python、NumPy；不得自动运行包中实验启动脚本或未知二进制。接下来等待独立审核，不启动新的实验。
''',encoding='utf-8')
for p in WORK.glob('*.py'):shutil.copy2(p,CORE/'source'/p.name)
for folder in [CORE,RAW]:
 manifest={p.relative_to(folder).as_posix():sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='FILE_SHA256_MANIFEST.json'}
 dump(folder/'FILE_SHA256_MANIFEST.json',manifest)
print(json.dumps(dict(status='MANIFESTS_READY',gas_calls=38,native_calls=calls,RSS=rss,unique_data_bytes=size,package_source_bytes=corebytes+rawbytes)))
