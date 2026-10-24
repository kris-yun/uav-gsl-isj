"""Portable complete-bundle verification. No ROS, GADEN or new predictions.

Usage: python review/reproduce_complete_bundle.py /path/to/extracted_bundle
Writes a new QA extraction directory; never removes or overwrites input evidence.
"""
from pathlib import Path
import csv,hashlib,importlib.util,json,sys,tempfile,zipfile
root=Path(sys.argv[1]).resolve()
def digest(f):
 h=hashlib.sha256()
 while True:
  b=f.read(4*1024**2)
  if not b:break
  h.update(b)
 return h.hexdigest()
manifest=json.loads((root/'MANIFEST_SHA256.json').read_text())
for x in manifest:
 p=(root/x['path']).resolve();assert p.is_relative_to(root)
 with p.open('rb')as f:assert digest(f)==x['sha256'],x['path']
review=root/'review'
spec=importlib.util.spec_from_file_location('native_qa',review/'analyze_completed_case.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
index=json.loads((review/'RUN_EVIDENCE_INDEX.json').read_text())
out=Path(tempfile.mkdtemp(prefix='o24_readonly_replay_'))
results=[]
for x in index['runs']:
 archive=root/x['archive_in_bundle']
 with archive.open('rb')as f:assert digest(f)==x['archive_sha256']
 with zipfile.ZipFile(archive)as z:
  mm=json.loads(z.read('ARCHIVE_MANIFEST_SHA256.json'))
  for member in mm:
   with z.open(member['path'])as f:assert digest(f)==member['sha256'],member['path']
  target=out/x['role'];target.mkdir()
  for name in z.namelist():
   p=(target/name).resolve();assert p.is_relative_to(target),'Unsafe member path'
  z.extractall(target)
 expected=x['qualification']
 if expected.startswith('PASS'):
  qa=mod.analyze(target)
  assert qa['qualification']==expected,(x['role'],qa['qualification'],expected)
  for k in ['Top5_error_m','MAP_error_m','mean_error_m','variance_m2']:
   assert abs(qa['terminal'][k]-x['terminal'][k])<1e-8,(x['role'],k)
  result=dict(role=x['role'],status='PASS_NATIVE_SCORE_POSTERIOR_AND_READOUT_REPLAY',score_max_relative_error=qa['score_max_relative_error'],official_success=qa.get('official_success'))
 else:
  result=json.loads((target/'RUN_RESULT.json').read_text())
  owners=json.loads((target/'PROCESS_OWNERS_AND_MONITOR.json').read_text())
  if result['native_goal_count']>0:assert owners.get('forced')=='ISOLATION_FAILURE'
  else:assert not result.get('goal_accepted')and not(target/'runtime/native_posterior_updates.csv').exists()
  assert x['official_success']is None
  result=dict(role=x['role'],status='PASS_TECHNICAL_ABORT_EVIDENCE_PRESERVED',native_goal_count=result['native_goal_count'],excluded_from_localization_metrics=True)
 results.append(result)
receipt=dict(status='PASS_PORTABLE_FULL_MANIFEST_AND_NATIVE_OFFLINE_REPLAY',results=results,extraction_directory=str(out),new_ROS=0,new_gas_worlds=0,new_candidate_predictions=0)
(out/'OFFLINE_REPLAY_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
