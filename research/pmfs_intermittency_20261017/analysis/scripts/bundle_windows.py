from pathlib import Path
import csv,json,zipfile,shutil,hashlib,time,datetime,re
R=Path(__file__).resolve().parents[1];W=R.parent;P=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';D=R/'DELIVERY';D.mkdir(exist_ok=False);(D/'evidence').mkdir();A=D/'analysis';A.mkdir();idx=json.loads((P/'CASE_INDEX.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def archive(name,files):
 q=D/'evidence'/name
 with zipfile.ZipFile(q,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  for source,relative in files:z.write(source,str(relative).replace('\\','/'))
 with zipfile.ZipFile(q) as z:assert z.testzip() is None
 print(name,q.stat().st_size,flush=True)
for e in idx['cases']:
 root=P/'cases'/e['case'];archive('native20_'+e['case']+'.zip',[(p,p.relative_to(W)) for p in root.rglob('*') if p.is_file()])
shared=[]
for n in ['CASE_INDEX.json','geometry_reference','physical_assets','native_pmfs']:
 p=P/n;files=[p] if p.is_file() else [q for q in p.rglob('*') if q.is_file()]
 shared.extend((q,q.relative_to(W)) for q in files)
for n in ['portable_recompute.py','native_analysis.py','portable_clock_gate.py','portable_geometry_gate.py','portable_wind_chain.py','cdr_grid.py','cdr_wind.py']:
 p=P.parent/n;shared.append((p,p.relative_to(W)))
archive('native20_shared.zip',shared)
hist=W/'PMFS_OFFICIAL_REPRO_AUDIT_20261016';folders=[p for p in (hist/'EXT5_3H_20261016_112419/observations').iterdir() if (p/'native_window_consumption.csv').exists()];folders+=list((hist/'PRO_NATIVE_PMFS_EXPORT').glob('P24_*_WALL5_VALID_V2_R0*'));files=[]
for folder in folders:
 for p in folder.iterdir():
  if p.is_file():files.append((p,p.relative_to(W)))
archive('historical46.zip',files)
shutil.copyfile(W/'B4_NATIVE_AUDIT_20261017/B4原生实查_间歇接触机制与逐格重放_20261017.zip',D/'evidence/b4_anchor.zip')
for name in ['scripts','cpp','lineage']:shutil.copytree(R/name,A/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for n in ['EXECUTION_CONTRACT.md','PROTOCOL_FROZEN.md','CAUSAL_CHAIN_DECISION.md','DATA_IDENTITY_AND_ORIGINAL_RELEASE.md','MINIMUM_SUPPLEMENT.md','IMPLEMENTATION_AND_EVENT_SEMANTICS.md','FAILED_ATTEMPTS_AND_LIMITATIONS.md','00_ASSET_AND_VERSION_PROVENANCE.csv']:shutil.copyfile(R/n,A/n)
shutil.copyfile(R/'reproduce_all.py',D/'reproduce_all.py');shutil.copyfile(R/'README_给Pro先读.md',D/'README.md')
# Keep all actual outputs, excluding executables and copied input duplicates.
out=A/'results';out.mkdir()
for p in (R/'results').iterdir():
 if p.is_file():shutil.copyfile(p,out/p.name)
for name in ['native20_recomputed','wind20','controls']:
 shutil.copytree(R/'results'/name,out/name,ignore=shutil.ignore_patterns('*.f64','readout_input.txt','*_ordinary_meta.txt'))
for name in ['FINAL_QA.json','EXECUTION.json']:shutil.copyfile(R/'results/b4_recomputed'/name,out/('B4_'+name))
shutil.copytree(R/'results/b4_recomputed/results',out/'b4_recomputed/results',ignore=shutil.ignore_patterns('native_hit_experiment','native_readout','native_hit_history'))
# CTest expects the original receipt path.
shutil.copyfile(R/'results/b4_recomputed/FINAL_QA.json',out/'b4_recomputed/FINAL_QA.json')
shutil.copytree(R/'logs',A/'logs')
commands=[('start_b4.py','b4_execution.json',0),('portable_recompute.py --data PORTABLE_DATA --out native20_recomputed','native20.stdout',0),('prepare_native.py; cmake configure/build','build.stdout',0),('replay20.py [first full attempt]','replay20.stderr',1),('replay20.py [launch fallback incomplete]','replay20_retry.stderr',1),('replay20.py [literal/default fallback, numeric parity]','replay20_complete.stdout',0),('controls20.py [first serialization attempt]','controls20.stderr',1),('controls20.py [four frozen arms]','controls20_retry.stdout',0),('controls20.py [original-double native decoder]','controls20_final.stdout',0),('controls20.py [Beta intervals]','controls20_intervals.stderr',0),('cmake build ordinary_controls C++','build_controls.stdout',0),('controls20.py [final C++/NumPy differential]','controls20_cpp_final.stderr',0),('portable_clock_gate.py','results/clock20.json',0),('portable_geometry_gate.py','results/geometry20.json',0),('portable_wind_chain.py','wind20.stdout',0),('screen.py [46 historical, all20]','screen_final.stdout',0),('export_pid.py [rclpy deserialize, no node]','export_pid.stdout',0),('export_pid_no_ros.py [independent decoder]','results/PID_DECODER_QA.json',0),('stop_influence.py','stop_influence_final.stdout',0),('summarize.py','summarize.stdout',0),('ctest --test-dir build --output-on-failure','ctest_final.stdout',0),('provenance_windows.py','provenance.stdout',0)]
with (A/'COMMANDS_AND_EXIT_CODES.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['scientific_command','preserved_log_or_receipt','exit_code']);w.writerows(commands)
qa=json.loads((R/'results/FINAL_DECISION.json').read_text());parity=json.loads((R/'results/SOURCE_SCORE_PARITY.json').read_text());receipt=json.loads((R/'logs/b4_execution.json').read_text());cost=dict(new_worlds=0,new_ROS_nodes=0,new_ROS_episodes=0,new_physical_gas_calls=0,new_physical_seeds=0,source_epochs=41,fixed_history_factorial_readouts=656,b4_replay_wall_s=receipt['elapsed_s'],b4_CPU_RSS='NOT_MEASURED_FOR_FIRST_RUN',final_controls_wall_s=19.80,final_controls_user_s=4.56,final_controls_system_s=1.95,final_controls_max_RSS_kib=137088,resource_measurement_log='logs/controls20_cpp_final.stderr',native_candidate_logscore_max_abs_error=max(p['candidate_logscore_max_error'] for p in parity),ordinary_cpp_numpy_max_abs_error=max(p['ordinary_cpp_numpy_max_error'] for p in parity),scope='Offline compute only; diagnostic readouts are not new localization tasks. Wall clock includes HGFS I/O; first-run copying is not an algorithm runtime.')
(A/'COST_AND_RESOURCE_LEDGER.json').write_text(json.dumps(cost,indent=2));
# Correct row identity labels: adapted historical source is not author-original.
pr=A/'00_ASSET_AND_VERSION_PROVENANCE.csv';rr=list(csv.DictReader(pr.open(encoding='utf8')))
for row in rr:
 if row['relative_path'].startswith('b4_anchor/'):
  row['is_author_original']='evidence/official/' in row['relative_path']
  if 'historical_source' in row['relative_path'] or 'operator_harness' in row['relative_path']:row['world_re_generated_locally']='NOT_APPLICABLE_CODE'
with pr.open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,rr[0]);w.writeheader();w.writerows(rr)
manifest={p.relative_to(D).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(D.rglob('*')) if p.is_file()};(D/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(delivery=str(D),files=len(manifest),bytes=sum(a['bytes'] for a in manifest.values()),max_file_bytes=max(a['bytes'] for a in manifest.values())),indent=2))
