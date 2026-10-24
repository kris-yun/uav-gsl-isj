from pathlib import Path
import hashlib,json,os,shutil,subprocess,zipfile
R=Path(__file__).resolve().parent;W=R.parent;repo=W.parent;A=W/'O24_MULTIWORLD_BASELINE_20261024';registry=repo/'RESEARCH_DATA_REGISTRY_20261024'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def finalize():
 records=json.loads((R/'BATCH_LEDGER.json').read_text());complete=len(records)==12;out=repo/'_research/O24_SCREEN12_AUDIT_HANDOFF_20261024';out.mkdir(parents=True,exist_ok=True)
 for name in ['PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json','BATCH_CHECKPOINT.json','EPISODE_RESULTS.csv','SCENARIO_SUMMARY.csv','RNG_REPETITION_AUDIT.json','中文筛查报告.md','CONTROLLED_RNG_ADAPTER_DESIGN_ONLY.md','NAVIGATION_AND_TIMELINE_INPUT_MANIFEST.json','PRE_EXECUTION_METADATA_CORRECTION.json']:
  if(R/name).exists():shutil.copyfile(R/name,out/name)
 for p in(A/'AUDIT_DELIVERY').glob('*'):
  if p.is_file():shutil.copyfile(p,out/p.name)
 for x in records:
  dest=out/'per_run_QA'/x['role'];dest.mkdir(parents=True,exist_ok=True)
  C=Path(x['archive']['source_case'])
  for name in ['FINAL_RUN_QA.json','CPP_READOUT.json','ARCHIVE_RECEIPT.json','CASE_META.json','EXECUTION_COMPLETE.json']:
   if(C/name).exists():shutil.copyfile(C/name,dest/name)
 for name in ['SAFE_CLEANUP_BEFORE_AFTER.md','O24_VS_H24_H26_SOURCE_AND_PARAMETER_DIFF.md','EXPERIMENT_VERSION_IDENTITY_MATRIX.csv','FINAL_REPRODUCTION_RECEIPT.json']:
  shutil.copyfile(registry/name,out/name)
 for name in ['analyze_completed_case.py','run_batch_host.py','run_batch_host_LAUNCHED_V1.py','run_case_guest.py','summarize_screen12.py','finalize_delivery.py','RESTORE_SCREEN12.py','CONTROLLER_SOURCE_PROVENANCE.json']:
  if(R/name).exists():shutil.copyfile(R/name,out/name)
 status=dict(status='SCREEN12_COMPLETE'if complete else'SCREEN12_STOPPED_PARTIAL_EVIDENCE',completed=len(records),actual_independent_worlds_claim=False,original_O24_ELF_unchanged=True,new_worlds=0,preregistration_sha256=sha(R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json'));(out/'DELIVERY_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
 # Isolated Git index: preserve the user's working tree, staged files and branch.
 gitrec={};branch='research/o24-screen12-20261024';tmp=R/'delivery_tmp';tmp.mkdir(exist_ok=True);env=os.environ.copy();env.update(GIT_INDEX_FILE=str(tmp/'index'),GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
 def git(*args):
  q=subprocess.run(['git',*args],cwd=repo,env=env,capture_output=True,text=True,timeout=120);assert q.returncode==0,q.stderr;return q.stdout.strip()
 try:
  head=git('rev-parse','HEAD');ref=subprocess.run(['git','rev-parse','--verify','refs/heads/'+branch],cwd=repo,env=env,capture_output=True,text=True);parent=ref.stdout.strip()if ref.returncode==0 else head;git('read-tree',parent);git('add','-f','--',out.relative_to(repo).as_posix());tree=git('write-tree');commit=git('commit-tree',tree,'-p',parent,'-m','Audit O24 official lineage and record bounded paper-stop native screening');git('update-ref','refs/heads/'+branch,commit,parent if ref.returncode==0 else'0'*40);push=git('-c','credential.interactive=never','push','origin',branch);assert git('rev-parse','HEAD')==head;gitrec=dict(status='COMMIT_PUSHED_WITHOUT_CHECKOUT',commit=commit,branch=branch,url='https://github.com/kris-yun/uav-gsl-isj/commit/'+commit,current_worktree_branch_unchanged=True,push_output=push)
 except Exception as e:gitrec=dict(status='GIT_DELIVERY_UNCONFIRMED_EVIDENCE_PRESERVED',error=str(e))
 (R/'GITHUB_DELIVERY_RECEIPT.json').write_text(json.dumps(gitrec,ensure_ascii=False,indent=2)+'\n')
 dest=Path('C:/Users/50176/Downloads')/('O24_SCREEN12_'+('COMPLETE'if complete else'PARTIAL')+'_FULL_EVIDENCE_20261024.zip');assert not dest.exists();files=[]
 for p in out.rglob('*'):
  if p.is_file():files.append((p,'review/'+p.relative_to(out).as_posix()))
 for x in records:
  p=Path(x['archive']['archive']);assert sha(p)==x['archive']['archive_sha256'];files.append((p,'full_runs/'+p.name))
 pilot=W/'O24_PAPER_STOP_A2_20261024'
 for p in(pilot/'cases/PAPERSTOP_A2_R01').rglob('*'):
  if p.is_file():files.append((p,'technical_failure_preserved/A2_START_R01/'+p.relative_to(pilot/'cases/PAPERSTOP_A2_R01').as_posix()))
 for name in ['EXECUTION_COMPLETE.json','TECHNICAL_RESTART_AMENDMENT.json','ADAPTER_DIFFS.json']:
  files.append((pilot/name,'technical_failure_preserved/'+name))
 for c in ['A2','B2','C3','D4','E3']:
  for name in ['WORLD_QUALIFICATION.json','ALL_FRAMES_RECHECKED_SHA256.csv.gz','GENERATION_CONFIG.yaml','ACTUAL_MAP_METADATA.json']:
   p=A/'G0_AE'/c/name
   if p.exists():files.append((p,'physical_asset_identity/'+c+'/'+name))
 for p in[A/'SAME_INPUT_AUDIT/SAME_INPUT_CPP_VERDICT.json',R/'GITHUB_DELIVERY_RECEIPT.json',repo/'_deliverables/PMFS_O24_FROZEN_CODE_63114565_VERIFIED_20261019.zip']:
  files.append((p,'support/'+p.name))
 manifest=[dict(path=n,sha256=sha(p),bytes=p.stat().st_size)for p,n in files];temp=dest.with_suffix('.zip.partial')
 with zipfile.ZipFile(temp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for p,n in files:z.write(p,n)
  z.writestr('MANIFEST_SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
 with zipfile.ZipFile(temp)as z:
  for x in manifest:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
 os.replace(temp,dest);receipt=dict(**status,archive=str(dest),archive_sha256=sha(dest),bytes=dest.stat().st_size,files=len(files),full_outer_member_SHA_verified=True,all_case_archives_previously_full_member_SHA_verified=True,github=gitrec);(R/'FINAL_DELIVERY_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');dest.with_suffix('.zip.sha256').write_text(receipt['archive_sha256']+'  '+dest.name+'\n');print(json.dumps(receipt,ensure_ascii=False));return receipt
if __name__=='__main__':finalize()
