"""Read-only E3 evaluation addendum verification. Requires Python and numpy.
No ROS, gas generation, propagation simulation, source update, or output writes.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,hashlib,math
import numpy as np
P=Path(__file__).resolve().parent
def js(n):return json.loads((P/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=js('SHA256_MANIFEST.json')
for n,h in manifest.items():assert sha(P/n)==h,n
registered=js('evidence/ORIGINAL_E3_SHA256_MANIFEST.json')
lineage=js('EVIDENCE_COPY_LINEAGE.json')
for n,v in lineage.items():
 assert sha(P/n)==v['sha256'],n
 if v['original_relative_path']!='SHA256_MANIFEST.json':assert registered[v['original_relative_path']]==v['sha256']
pres=js('ORIGINAL_E3_PRESERVATION.json');review=js('REVIEW_RESULT.json');old=js('evidence/E3_RESULT.json');recheck=js('ORIGINAL_E3_VERIFIER_RESULT.json')
assert pres['original_manifest_file_count']==len(registered)==1183
assert pres['original_zip_sha256_before']==pres['original_zip_sha256_after']=='eceee3765b9c42bcb6c509682b2cbae606fbc673c6cfd72abbc266fd73b4a125'
assert old==recheck
assert old['normal_control']==pres['frozen_original_pre_registered_decision']=='FAIL_PRE_REGISTERED_1M_ERROR_GATE'
assert recheck['score_max_relative_error']<1e-12 and recheck['posterior_max_abs_error']<1e-12
assert review['decisions']['official_config_convergence_success']=='PASS'
assert review['decisions']['pre_registered_extra_1m_accuracy_target']=='FAIL_RETAINED'
assert review['decisions']['paper_multirun_statistical_reproduction'].startswith('HOLD')
assert review['decisions']['B4_execution']=='HOLD_PENDING_EXPLICIT_APPROVAL'
assert review['paper_threshold_counterfactual_stop_time_claimed'] is False
assert all(review[n]==0 for n in ['new_ROS_runs','new_gas_realizations','new_PMFS_updates','new_B4_runs'])
run=js('evidence/RUN_RESULT.json');assert run['native_goal_count']==1 and run['action_status']==4 and run['localization_success'] is True
assert run['result']=='NATIVE_ACTION_RETURNED'
cpp=js('CPP_SORT_RECOMPUTE.json');vm=js('VM_READONLY_STATUS.json');top=js('TOP5_METRIC_RECOMPUTATION.json')
assert cpp['arithmetic_only'] is True and cpp['new_PMFS_updates']==cpp['new_ROS_runs']==0
assert sha(P/'top5_sort_review.cpp')==cpp['source_sha256']
assert cpp['libstdcxx']==vm['GSL_libstdcxx']
assert vm['hashes']['GSL']==js('evidence/ENVIRONMENT_PREFLIGHT.json')['binaries']['/home/zyc/pmfs_official_alignment_r5_20261009/ws/install/gsl_server/lib/gsl_server/gsl_actionserver_node']
for name,path in {'E3_RUN_RESULT':'RUN_RESULT.json','E3_POSTERIOR':'update_1/posterior.f64','E3_RESULT_CSV':'native_results.csv','E3_LAUNCH_LOG':'launch.log'}.items():assert vm['hashes'][name]==sha(P/'evidence'/path)
assert vm['domain_processes']==[] and vm['GSL_pid_30258_present'] is False
assert all(v is False for v in vm['known_E3_pid_presence'].values())
assert vm['read_only'] is True and vm['new_ROS_runs']==vm['new_goals']==0
assert vm['bounded_core_files']==[] and vm['coredumpctl']['available'] is False
selected_table=list(csv.DictReader((P/'TOP5_SELECTED_CELLS.csv').open(encoding='utf-8',newline='')))
summary=[]
for number,name in enumerate(['update_0','update_1']):
 m=js(f'evidence/{name}/metadata.json');data=list(csv.DictReader((P/f'evidence/{name}/input.csv').open(encoding='utf-8',newline='')))
 posterior=np.frombuffer((P/f'evidence/{name}/posterior.f64').read_bytes(),dtype='<f8')
 assert len(posterior)==len(data)==m['width']*m['height'] and np.isfinite(posterior).all()
 free=np.array([int(d['occupancy'])==1 for d in data]);assert free.sum()==1132
 assert (posterior[~free]==0).all() and abs(posterior.sum()-1)<1e-12
 xy=np.column_stack([m['origin_x']+(np.arange(len(data))%m['width']+.5)*m['cell_size'],m['origin_y']+(np.arange(len(data))//m['width']+.5)*m['cell_size']])
 source=np.array([-4.,-1.9]);fullmean=(xy*posterior[:,None]).sum(axis=0)
 variance=float((np.sum((xy-fullmean)**2,axis=1)*posterior).sum())
 assert abs(variance-old['updates'][number]['variance'])<1e-12
 assert abs(np.linalg.norm(fullmean-source)-old['updates'][number]['mean_error_m'])<1e-12
 map_i=int(np.argmax(posterior));assert abs(np.linalg.norm(xy[map_i]-source)-old['updates'][number]['MAP_error_m'])<1e-12
 k=math.ceil(free.sum()*.05);capture=cpp['results'][name];ids=capture['selected_cell_indices'];assert len(ids)==len(set(ids))==k==57
 assert free[ids].all();unselected=np.setdiff1d(np.flatnonzero(free),ids)
 assert posterior[ids].min()>=posterior[unselected].max()
 assert np.all(np.diff(posterior[ids])<=0)
 x=y=s=0.
 for i in ids:x+=posterior[i]*float(np.float32(xy[i,0]));y+=posterior[i]*float(np.float32(xy[i,1]));s+=posterior[i]
 location=np.array([np.float32(x/s),np.float32(y/s)],dtype=np.float64)
 gt=np.array([np.float32(-4.),np.float32(-1.9)],dtype=np.float64)
 error=float(np.linalg.norm(location-gt))
 assert np.array_equal(location,np.array(capture['xy'])) and abs(error-capture['error_GT_float_m'])<1e-12
 assert abs(s-capture['selected_mass'])<1e-12
 exported=list(csv.DictReader((P/f'top5_inputs/{name}.csv').open(newline='')));assert len(exported)==len(data)
 for i,row in enumerate(exported):assert int(row['index'])==i and int(row['free'])==int(free[i]) and float(row['x'])==xy[i,0] and float(row['y'])==xy[i,1] and float(row['probability'])==posterior[i]
 table=[r for r in selected_table if r['update']==name];assert [int(r['cell_index']) for r in table]==ids
 assert top['updates'][number]['cutoff_tie'] is True
 assert int((P/f'evidence/{name}/COMPLETE.txt').read_text())==top['updates'][number]['complete_ROS_ns']>m['stamp_ns']
 summary.append(dict(update=name,top5_error_m=error,selected_cells=k,variance_m2=variance))
native=[float(x) for x in (P/'evidence/native_results.csv').read_text().split()]
assert len(native)==6 and abs(native[3]-summary[-1]['top5_error_m'])<5e-5
assert abs(native[5]-summary[-1]['variance_m2'])<5e-6 and native[1]<300
assert summary[-1]['variance_m2']<1.<1.5
assert old['final']['MAP_error_m']>1 and old['final']['mean_error_m']>1
params=(P/'evidence/resolved_GSL_parameters.yaml').read_text();assert 'convergence_thr: 1.5' in params
utils=(P/'evidence/PMFS_utils.cpp').read_text();mathcode=(P/'evidence/Math.cpp').read_text()
assert 'variance < settings.declaration.threshold' in utils and 'gridMetadata), 0.05)' in utils
assert 'file.close();' in utils and 'i < data.size() * proportionBest' in mathcode
assert 'return a.probability > b.probability;' in mathcode
driver=(P/'evidence/runtime_driver.py').read_text()
assert driver.index("q=result.result();status.update(result='NATIVE_ACTION_RETURNED'")<driver.index('save_status();stop_all();')
assert 'os.killpg(p.pid,signal.SIGINT)' in driver
timeline=js('TEARDOWN_TIMELINE.json');logs=(P/'evidence/launch.log').read_text().splitlines();lastline=0
for event in timeline['events']:
 assert event['launch_log_line']>lastline;lastline=event['launch_log_line']
 assert logs[lastline-1]==event['verbatim_log_line']
assert timeline['observed_stage']=='POST_RESULT_SIGINT_SHUTDOWN' and timeline['root_cause'].startswith('HOLD')
assert 1<timeline['first_subscription_error_minus_success_log_wall_s']<2
external=P.parent/'PMFS_E3_NATIVE_VALIDATION_20261009_SMALL.zip'
external_available=external.exists()
if external_available:
 assert sha(external)==pres['original_zip_sha256_after']
 frozen=P.parent/pres['original_folder'];assert all(sha(frozen/n)==h for n,h in registered.items())
print(json.dumps({'addendum_verification':'PASS','manifest_files':len(manifest),'copied_original_evidence_files':len(lineage),'original_external_ZIP_and_all_manifest_files_rechecked':external_available,'frozen_1m_FAIL_retained':True,'official_config_success':'PASS','updates':summary,'post_result_failure_stage':'CONFIRMED_SHUTDOWN','shutdown_root_cause':'HOLD','B4_execution':'HOLD_PENDING_APPROVAL','ROS_or_PMFS_runs_started':0},ensure_ascii=False))
