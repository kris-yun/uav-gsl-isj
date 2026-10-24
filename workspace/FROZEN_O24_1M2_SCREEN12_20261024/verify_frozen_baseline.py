"""Read-only frozen baseline guard. Never builds, repairs or launches ROS."""
from pathlib import Path
import argparse,hashlib,json,re,sys
def check(root, live_elf=None, method_manifest=None):
 root=Path(root).resolve()
 manifest=json.loads((root/'FREEZE_MANIFEST_SHA256.json').read_text(encoding='utf-8'))
 declared={r['path'] for r in manifest['files']}
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='FREEZE_MANIFEST_SHA256.json' and '__pycache__' not in p.parts}
 assert declared==actual,{'missing':list(declared-actual),'unexpected':list(actual-declared)}
 for row in manifest['files']:
  p=(root/row['path']).resolve();assert p.is_relative_to(root)
  b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
 lock=json.loads((root/'BASELINE_LOCK.json').read_text(encoding='utf-8'))
 assert lock['normal_stop']['value']==1.0 and lock['normal_stop']['unit']=='m2'
 src=json.loads((root/'FROZEN_SOURCE_IDENTITY_128.json').read_text(encoding='utf-8'))['files']
 assert len(src)==128
 for f in src:
  b=(root/'source_snapshot'/f['path']).read_bytes()
  assert hashlib.sha256(b).hexdigest()==f['sha256']
  assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['frozen_commit_blob']
 assert hashlib.sha256((root/'binaries/gsl_actionserver_node').read_bytes()).hexdigest()==lock['ELF_sha256']
 for c in json.loads((root/'FROZEN_CASES.json').read_text(encoding='utf-8')):
  p=json.loads((root/c['configuration_prefix']/'runtime/BASELINE_PARAMETER_GATE.json').read_text(encoding='utf-8'))['checked']
  assert p==c['GSL_parameters']
  assert p['convergence_thr']==1.0 and p['sourceDiscriminationPower']==0.2 and p['useWindGroundTruth'] is False
  assert p['noiseSTDev']==lock['baseline_core']['noiseSTDev_by_case'][c['case']]
 if live_elf:
  assert hashlib.sha256(Path(live_elf).read_bytes()).hexdigest()==lock['ELF_sha256'],'LIVE_ELF_MISMATCH'
 if method_manifest:
  m=json.loads(Path(method_manifest).read_text(encoding='utf-8'))
  assert m['baseline_freeze_identity']==lock['freeze_identity'],'BASELINE_IDENTITY_MISMATCH'
  assert m['baseline_lock_sha256']==hashlib.sha256((root/'BASELINE_LOCK.json').read_bytes()).hexdigest(),'BASELINE_LOCK_MISMATCH'
  assert m['status']=='PREREGISTERED_READY' and re.fullmatch('[0-9a-f]{64}',m.get('method_code_sha256','')),'METHOD_NOT_SUBMITTED_AND_FROZEN'
  assert m['shared_information_and_budget_contract_accepted'] is True,'SHARED_CONTRACT_NOT_ACCEPTED'
  assert m['normal_stop_variance_m2']==1.0,'STOP_PROTOCOL_MISMATCH'
 return {'status':'PASS_FROZEN_SOURCE_CONFIG_ELF_EVIDENCE','freeze_identity':lock['freeze_identity'],'files':len(declared),'source_files':128,'new_ROS':0}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parent));a.add_argument('--live-elf');a.add_argument('--method-manifest');args=a.parse_args()
 try:print(json.dumps(check(args.root,args.live_elf,args.method_manifest),ensure_ascii=False))
 except (AssertionError,KeyError,FileNotFoundError,ValueError) as e:print('REJECT_FROZEN_BASELINE_OR_COMPARISON: '+str(e),file=sys.stderr);sys.exit(2)
