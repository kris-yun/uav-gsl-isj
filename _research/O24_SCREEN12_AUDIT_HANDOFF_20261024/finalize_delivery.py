from pathlib import Path
import hashlib,json,os,shutil,subprocess,zipfile
R=Path(__file__).resolve().parent;W=R.parent;repo=W.parent;A=W/'O24_MULTIWORLD_BASELINE_20261024';registry=repo/'RESEARCH_DATA_REGISTRY_20261024'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def finalize():
 for x in json.loads((R/'domain_audit/MANIFEST_SHA256.json').read_text()):assert sha(R/'domain_audit'/x['path'])==x['sha256'],x['path']
 # Fresh read-only report code; the watcher may have imported an earlier version.
 import importlib.util
 spec=importlib.util.spec_from_file_location('final_report_latest',R/'summarize_screen12.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.summarize()
 spec_nav=importlib.util.spec_from_file_location('nav_report_latest',R/'summarize_navigation_cost.py');nav=importlib.util.module_from_spec(spec_nav);spec_nav.loader.exec_module(nav);nav.summarize()
 records=json.loads((R/'BATCH_LEDGER.json').read_text());complete=len(records)==12;qualified=sum(x['QA']['qualification'].startswith('PASS')for x in records);technical=len(records)-qualified;out=repo/'_research/O24_SCREEN12_AUDIT_HANDOFF_20261024';out.mkdir(parents=True,exist_ok=True)
 for name in ['PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json','BATCH_CHECKPOINT.json','EPISODE_RESULTS.csv','SCENARIO_SUMMARY.csv','RNG_REPETITION_AUDIT.json','中文筛查报告.md','CONTROLLED_RNG_ADAPTER_DESIGN_ONLY.md','NAVIGATION_AND_TIMELINE_INPUT_MANIFEST.json','PRE_EXECUTION_METADATA_CORRECTION.json','RESUME_AMENDMENT_R3.json','RESUME_AMENDMENT_R4.json','ROLE_EXECUTION_OVERRIDES_R4.json','TECHNICAL_PREGOAL_ATTEMPTS.json','DOMAIN_SUPPLEMENT_RECEIPT.json','COLLECTION_RECOVERY_R5.json','B2_LEGAL_PROXY_POSTERIOR_AUDIT.csv','B2_LEGAL_PROXY_POSTERIOR_AUDIT.json','audit_B2_legal_proxy_posterior.py']:
  if(R/name).exists():shutil.copyfile(R/name,out/name)
 for name in ['NAVIGATION_AND_COST_SUMMARY.csv','summarize_navigation_cost.py','PAPER_TIMEBASE_COMPARISON.md']:
  shutil.copyfile(R/name,out/name)
 for p in(A/'AUDIT_DELIVERY').glob('*'):
  if p.is_file():shutil.copyfile(p,out/p.name)
 for x in records:
  dest=out/'per_run_QA'/x['role'];dest.mkdir(parents=True,exist_ok=True)
  C=Path(x['archive']['source_case'])
  for name in ['FINAL_RUN_QA.json','CPP_READOUT.json','ARCHIVE_RECEIPT.json','CASE_META.json','EXECUTION_COMPLETE.json']:
   if(C/name).exists():shutil.copyfile(C/name,dest/name)
 for name in ['SAFE_CLEANUP_BEFORE_AFTER.md','O24_VS_H24_H26_SOURCE_AND_PARAMETER_DIFF.md','EXPERIMENT_VERSION_IDENTITY_MATRIX.csv','FINAL_REPRODUCTION_RECEIPT.json','CANONICAL_DATA_INDEX.json','ARCHIVE_MANIFEST_SHA256.json','RESTORE_ARCHIVED_DATA.py','O24_QUALIFIED_NATIVE_EVIDENCE.md','SCIENTIFIC_CONCLUSION_FOR_PRO.md','INVENTORY_COMPLETE.json']:
  shutil.copyfile(registry/name,out/name)
 for name in ['analyze_completed_case.py','run_batch_host.py','run_batch_host_LAUNCHED_V1.py','run_batch_host_RESUME_R3.py','run_batch_host_RESUME_R4.py','run_batch_host_RESUME_R5.py','run_case_guest.py','run_case_guest_R4.py','process_ownership_R4.py','summarize_screen12.py','finalize_delivery.py','RESTORE_SCREEN12.py','CONTROLLER_SOURCE_PROVENANCE.json','prepare_resume_R3.py','prepare_resume_R4.py','recovery_gate_guest.py','reproduce_complete_bundle.py','make_pro_complete_readme.py']:
  if(R/name).exists():shutil.copyfile(R/name,out/name)
 for folder in ['domain_audit','recovery']:
  for p in(R/folder).rglob('*'):
   if p.is_file()and '__pycache__'not in p.parts:
    dest=out/folder/p.relative_to(R/folder);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 pregoal=json.loads((R/'TECHNICAL_PREGOAL_ATTEMPTS.json').read_text())if(R/'TECHNICAL_PREGOAL_ATTEMPTS.json').exists()else[]
 source_eligible=sum(x['QA']['qualification'].startswith('PASS')and x['QA'].get('source_domain_class')=='LEGAL'for x in records)
 source_excluded=sum(x['QA']['qualification'].startswith('PASS')and x['QA'].get('source_domain_class')=='EXCLUDED_DIAGNOSTIC_ONLY'for x in records)
 status=dict(status=('SCREEN12_ALL_SLOTS_ACCOUNTED_WITH_TECHNICAL_ABORTS'if technical else'SCREEN12_COMPLETE')if complete else'SCREEN12_STOPPED_PARTIAL_EVIDENCE',accounted_slots=len(records),qualified_scientific_runs=qualified,technical_abort_slots=technical,preserved_extra_zero_goal_startups=len(pregoal),preserved_prior_pilot_technical_attempts=1,prior_pilot_attempt_scope='Historical failed A2 pilot was separately authorized before screen12; archived separately and not counted as a new screen12 goal.',completed=len(records),completed_field_scope='Accounted preregistered slots, including explicitly retained technical aborts; not the number of completed localization runs.',actual_independent_worlds_claim=False,original_O24_ELF_unchanged=True,new_worlds=0,preregistration_sha256=sha(R/'PREREGISTERED_SCREEN12_R2_INPUT_FINAL.json'));(out/'DELIVERY_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
 status.update(validated_native_runs=qualified,source_domain_qualified_runs=source_eligible,source_excluded_diagnostic_runs=source_excluded,qualified_scientific_runs_field_scope='Legacy field means complete native numerical replay QA, not source-domain eligibility. Use source_domain_qualified_runs for source-supported inference cases.')
 (out/'DELIVERY_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
 spec2=importlib.util.spec_from_file_location('pro_readme_latest',R/'make_pro_complete_readme.py');module2=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(module2);module2.write(out)
 # Isolated Git index: preserve the user's working tree, staged files and branch.
 gitrec={};branch='research/o24-screen12-20261024';tmp=R/'delivery_tmp';tmp.mkdir(exist_ok=True);env=os.environ.copy();env.update(GIT_INDEX_FILE=str(tmp/'index'),GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
 def git(*args):
  q=subprocess.run(['git',*args],cwd=repo,env=env,capture_output=True,text=True,timeout=120);assert q.returncode==0,q.stderr;return q.stdout.strip()
 try:
  head=git('rev-parse','HEAD');ref=subprocess.run(['git','rev-parse','--verify','refs/heads/'+branch],cwd=repo,env=env,capture_output=True,text=True);parent=ref.stdout.strip()if ref.returncode==0 else head;git('read-tree',parent);git('add','-f','--',out.relative_to(repo).as_posix());tree=git('write-tree');commit=git('commit-tree',tree,'-p',parent,'-m','Audit O24 official lineage and record bounded paper-stop native screening');git('update-ref','refs/heads/'+branch,commit,parent if ref.returncode==0 else'0'*40);push=git('-c','credential.interactive=never','push','origin',branch);assert git('rev-parse','HEAD')==head;gitrec=dict(status='COMMIT_PUSHED_WITHOUT_CHECKOUT',commit=commit,branch=branch,url='https://github.com/kris-yun/uav-gsl-isj/commit/'+commit,current_worktree_branch_unchanged=True,push_output=push)
 except Exception as e:gitrec=dict(status='GIT_DELIVERY_UNCONFIRMED_EVIDENCE_PRESERVED',error=str(e))
 (R/'GITHUB_DELIVERY_RECEIPT.json').write_text(json.dumps(gitrec,ensure_ascii=False,indent=2)+'\n')
 dest=Path('C:/Users/50176/Downloads')/('O24_SCREEN12_'+('ACCOUNTED'if complete and technical else'COMPLETE'if complete else'PARTIAL_R4')+'_FULL_EVIDENCE_20261024.zip')
 if dest.exists():
  import datetime
  dest=dest.with_name(dest.stem+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')+'.zip')
 files=[]
 for p in out.rglob('*'):
  if p.is_file():files.append((p,'review/'+p.relative_to(out).as_posix()))
 for x in records:
  p=Path(x['archive']['archive']);assert sha(p)==x['archive']['archive_sha256'];files.append((p,'full_runs/'+p.name))
 for x in pregoal:
  a=x['original_entry']['archive'];p=Path(a['archive']);assert sha(p)==a['archive_sha256'];files.append((p,'pre_goal_technical_attempts/'+p.name))
 pilot=W/'O24_PAPER_STOP_A2_20261024'
 for p in(pilot/'cases/PAPERSTOP_A2_R01').rglob('*'):
  if p.is_file():files.append((p,'technical_failure_preserved/A2_START_R01/'+p.relative_to(pilot/'cases/PAPERSTOP_A2_R01').as_posix()))
 for name in ['EXECUTION_COMPLETE.json','TECHNICAL_RESTART_AMENDMENT.json','ADAPTER_DIFFS.json']:
  files.append((pilot/name,'technical_failure_preserved/'+name))
 for c in ['A2','B2','C3','D4','E3']:
  for name in ['WORLD_QUALIFICATION.json','ALL_FRAMES_RECHECKED_SHA256.csv.gz','GENERATION_CONFIG.yaml','ACTUAL_MAP_METADATA.json']:
   p=A/'G0_AE'/c/name
   if p.exists():files.append((p,'physical_asset_identity/'+c+'/'+('HISTORICAL_PRECHECK_MAP_METADATA.json'if name=='ACTUAL_MAP_METADATA.json'else name)))
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
