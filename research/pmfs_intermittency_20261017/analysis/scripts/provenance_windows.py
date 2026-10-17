from pathlib import Path
import json,csv,subprocess,hashlib,os,datetime
R=Path(__file__).resolve().parents[1];W=R.parent;A=W/'PMFS_OFFICIAL_REPRO_AUDIT_20261016';P=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';gitdir=A/'source_metadata/GSL_humble_vm.git';pin='2e1406708e9e95f1fd0e4b591ebddddf55f7a023';env=dict(os.environ,GIT_NO_LAZY_FETCH='1');q=subprocess.run(['git','--git-dir='+str(gitdir),'ls-tree','-r',pin],capture_output=True,check=True,env=env);rows=[]
for line in q.stdout.decode().splitlines():
 left,name=line.split('\t');mode,typ,sha=left.split()
 if not (name.startswith('Environment_config/PMFS/') or ('PMFS' in name and name.startswith('gsl_server/'))):continue
 rows.append(dict(path=name,author_public_asset=True,commit=pin,git_blob_sha1=sha,type=typ,author_original_trial_raw='UNVERIFIED_NOT_SUPPLIED'))
with (R/'lineage/PUBLIC_2024_GIT_TREE.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
matches=[]
for file in ['PMFSLib.cpp','MovingStatePMFS.cpp','PMFS_utils.cpp']:
 name=next(a['path'] for a in rows if a['path'].endswith('/'+file));original=A/'paper_baseline_2024/original'/name;actual=W/'B4_NATIVE_AUDIT_20261017/inputs/historical_source/NR16/actual_h24_v2'/name;blob=original.read_bytes();gitsha=hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest();expected=next(a['git_blob_sha1'] for a in rows if a['path']==name);matches.append(dict(file=name,exported_matches_pinned_git_blob=gitsha==expected,git_blob_sha1=expected,export_sha256=hashlib.sha256(blob).hexdigest(),b4_actual_matches_export=actual.exists() and actual.read_bytes()==blob));assert gitsha==expected
 # Public YAML/launch are small; preserve them, never copy complete worlds.
for a in rows:
 name=a['path'];src=A/'paper_baseline_2024/original'/name
 if a['type']=='blob' and src.exists() and (name.endswith('.yaml') or name.endswith('.py') or name.endswith('.cpp') or name.endswith('.hpp')):
  dst=R/'lineage/official_2024'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
(R/'lineage/PINNED_2024_CORE_PARITY.json').write_text(json.dumps(matches,indent=2))
idx=json.loads((P/'CASE_INDEX.json').read_text());pro=[]
for e in idx['cases']:
 root=P/e['native_path']
 for p in root.rglob('*'):
  if not p.is_file():continue
  pro.append(dict(path=str(p),relative_path=p.relative_to(P).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,is_author_original=False,world_re_generated_locally=True,case=e['case'],physical_group=e['group'],wind_run_identity=e['identity'],implementation_commit='4e141e162551e674f2f30ddb8859136c72139aac',source_z=e['metadata']['source_xyz'][2],sensor_z=e['metadata']['sensor_xyz'][2],threshold_ppm=.1,gas_time='PHYSICAL_FRAME_TIME.csv',source_support='results/geometry20.json',mechanism_use='FIXED_HISTORY_SOURCE_SCORE_AFTER_SOURCE_SENSOR_QUALIFICATION'))
for p in (W/'B4_NATIVE_AUDIT_20261017/inputs').rglob('*'):
 if p.is_file() and 'previous_native_raw' not in str(p):
  pro.append(dict(path=str(p),relative_path='b4_anchor/'+p.relative_to(W/'B4_NATIVE_AUDIT_20261017/inputs').as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,is_author_original='historical_source' in str(p),world_re_generated_locally=True,case='B4',physical_group='B4_20261009_REUSED',wind_run_identity='2024_LOCAL_GMRF_PUBLIC_CLOCK5',implementation_commit=pin,source_z=-.5,sensor_z=-.2,threshold_ppm=.1,gas_time='NONLOOP_PHYSICAL_PUBLIC_CLOCK5',source_support='B4_ANCHOR_448_FREE',mechanism_use='CONTACT_HISTORY_EXACT_SOURCE_FORWARD_MISSING'))
keys=list(dict.fromkeys(k for r in pro for k in r))
with (R/'00_ASSET_AND_VERSION_PROVENANCE.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(pro)
print(json.dumps(dict(public_2024_tree_assets=len(rows),input_files_hashed=len(pro),core_parity=matches),indent=2))
