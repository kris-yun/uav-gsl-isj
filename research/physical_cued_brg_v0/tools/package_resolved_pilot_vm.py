"""P1-only auditable review, preserving raw pose/goal/belief/event logs."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
PILOT=Path('/mnt/hgfs/workspace/_staging/BRG_NATIVE615_PILOT_P1_V2_20260927')
DEST=Path('/mnt/hgfs/workspace/_staging/BRG_NATIVE615_P1_REVIEW_20260927.zip')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 result=json.loads((PILOT/'P1_RESULT.json').read_text());assert result['stage']=='P1_COMPLETE_STOP' and result['scored_runs']==16
 assert not DEST.exists();files={}
 def addfolder(path,arc):
  for p in path.rglob('*'):
   if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix!='.pyc':files[arc+'/'+str(p.relative_to(path))]=p
 addfolder(PILOT,'pilot');addfolder(ROOT/'pilot_contract_resolved','cases')
 addfolder(Path('/mnt/hgfs/workspace/_staging/BRG_NATIVE615_PILOT_P1_20260927'),'historical_p0_v1_infrastructure_batch_excluded_from_main')
 addfolder(Path('/home/zyc/brg_closedloop_20260927/vgr_execution_v2/vgr_bridge'),'execution/vgr_bridge')
 addfolder(ROOT/'amendment','amendment')
 for part in ['pmfs_brg','integration']:
  addfolder(ROOT/part,'execution/'+part)
 for n in ['bind_native_case_vm.py','run_bound_case_vm.sh','run_resolved_p0_p1_vm.py','evaluate_closed_loop.py','freeze_resolved_pilot_vm.py','prepare_native_legal_support_vm.py','bind_native_bank_views_vm.py','rebuild_h01_native_bank_vm.py','train.py','align_full_support_training.py']:
  files['execution/tools/'+n]=ROOT/'tools'/n
 for n in ['h03_native_legal_bank.npz','LEGAL_MASKS_COMPLETE.json','LEGAL_SUPPORT_COMPLETE.json']+[f'env_{e}_occupancy.u8' for e in range(3)]+['h03_occupancy.u8']:
  files['legal_support/'+n]=ROOT/'legal_support_v2'/n
 for n in ['PRE_FORWARD_FREEZE.json','BANK_COMPLETE.json']:files['H01_rebuild_provenance/'+n]=ROOT/'h01_native_rebuild'/n
 for n in ['PRE_FORWARD_FREEZE.json','BANK_COMPLETE.json']:files['original_cache_provenance/'+n]=ROOT/'full_support'/n
 for variant in ['gru','brg','ungated']:
  for n in ['best.pt','run_config.json','routes.json','history.json','summary.json']:files['weights/'+variant+'/'+n]=ROOT/'trained_full'/variant/n
 files['CHECKPOINT_FREEZE.json']=ROOT/'CHECKPOINT_FREEZE.json';files['software_common615_result.json']=ROOT/'software_common615_result.json'
 hashes={name:sha(p) for name,p in sorted(files.items())};manifest=''.join(h+'  '+name+'\n' for name,h in hashes.items())
 with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name,p in sorted(files.items()):z.write(p,name)
  z.writestr('SHA256SUMS',manifest)
 review={'path':str(DEST),'bytes':DEST.stat().st_size,'sha256':sha(DEST),'entries':len(files),'all_raw_pilot_logs_retained':True,'new_plumes':0,'full_campaign_started':False}
 (PILOT/'REVIEW_PACKAGE.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps(review,indent=2))
if __name__=='__main__':main()
