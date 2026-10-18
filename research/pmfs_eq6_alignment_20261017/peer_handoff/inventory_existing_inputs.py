from pathlib import Path
import json,hashlib,csv,re,subprocess
E=Path(__file__).resolve().parent;ROOT=E.parent.parent/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016';N=ROOT/'NATIVE7_MIN_RESEARCH_20261016'
OLD=E.parent/'FSR_S2_PMFS_PAPER_BASELINE_AUDIT_V1_20261018';LIT=E.parent/'FSR_S2_PMFS_PAPER_DISCREPANCY_LITERATURE_V1_20261017'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
put(E/'PRECOMMIT.json',dict(scope='Read-only existing A2/B2 assets and rectangular-grid source handoff. Do not alter old223/508 files, implement an Eq6 variant or start ROS/physics/controls in this chat.',authorized_human_thread='01a12e11-68b9-7cd2-8b4b-961dd512a630',old_223_manifest_sha256=sha(OLD/'FINAL_FILES_MANIFEST_V2.json'),old_508_manifest_sha256=sha(LIT/'JOINT_FILES_MANIFEST.json')))
def item(p):
 return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p) if p.stat().st_size<=32*2**20 else None,live_sha_scope='actual bytes' if p.stat().st_size<=32*2**20 else 'not recomputed over32MiB in this read-only inventory')
obs=[]
for folder in sorted((N/'input_observations').iterdir()):
 if not folder.is_dir() or not re.search(r'P24_(A2|B2)_',folder.name):continue
 files=[item(p) for p in folder.iterdir() if p.is_file()];csvs={}
 for name in ['native_posterior_updates.csv','native_window_consumption.csv']:
  file=folder/name
  with file.open(newline='',encoding='utf-8-sig') as f:
   r=csv.DictReader(f);cols=r.fieldnames;rows=list(r)
  csvs[name]=dict(columns=cols,rows=len(rows),update_ids=sorted({int(row['update']) for row in rows}) if 'update' in cols else None,Omega_column_present=any('omega' in c.lower() for c in cols),confidence_one_rows=sum(float(row.get('hit_confidence','nan'))==1 for row in rows),consumed_windows=sum(row.get('status')=='CONSUMED' for row in rows))
 receipt=read(folder/'EXPORT_RECEIPT.json');case=receipt['case'];origin=ROOT/'runs'/folder.name
 identity=origin/'runtime/NATIVE_EXECUTABLE_IDENTITY.json'
 obs.append(dict(run=folder.name,case=case,path=str(folder),export_receipt=receipt,files=files,schema=csvs,origin_binary_identity=read(identity) if identity.exists() else None,source_identity_evidence=str(ROOT/'paper_baseline_2024/SOURCE_IDENTITY.json'),not_exact_author_original_experiment=True))
put(E/'A2_B2_EXISTING_OBSERVATIONS.json',dict(runs=obs,has_Omega=False,limitation='Post-source-update confidence/hit maps and raw consumption windows are available, but direct per-consumed-window Omega/map states are not present in these CSV schemas. Saturated confidence1 cannot be inverted to a unique finite Omega. No historical state synthesized.'))
q=subprocess.run(['rg','--files','--no-ignore',str(N)],capture_output=True,text=True,check=True)
paths=[Path(s) for s in q.stdout.splitlines()];banks=[]
for p in paths:
 rel=p.relative_to(N).as_posix()
 if re.search(r'(^|[/_])(A2|B2)(?=[/_.]|$)',rel) and p.suffix in ['.csv','.txt'] and ('capture_parity/' in rel or 'results/shadows/' in rel):
  if any(k in p.name for k in ['prediction','scores','posterior','rng','gaussian','leaf_structure']) or p.name.startswith('W'):
   with p.open(encoding='utf-8',errors='replace') as f:head=f.readline().strip()
   banks.append(dict(relative_to_N=rel,**item(p),first_line=head))
put(E/'A2_B2_EXISTING_OFFLINE_BANK_FILES.json',dict(files=banks,provenance='July2024 upstream plus Pro-supplied NEW_SAFE_RNG control and passive capture. Not original closed-loop owner/RNG predictions or Sep18 source binary.',identity_files={str(N/name):sha(N/name) for name in ['CAPTURE_PROVENANCE.json','RNG_REPLAY_NOTE.md','CAPTURE_PARITY.json','SOURCE_ARTIFACTS.json','DATA_SCHEMA_zh.md']}))
# Index the predictor map inputs/slot-to-case owner mapping, without interpreting evaluator truth.
ledger=read(N/'results/LEDGER.json');ledger_type=type(ledger).__name__;samples=ledger[:1] if isinstance(ledger,list) else {k:type(v).__name__ for k,v in ledger.items()}
put(E/'LEDGER_SCHEMA.json',dict(path=str(N/'results/LEDGER.json'),sha256=sha(N/'results/LEDGER.json'),top_type=ledger_type,top_shape=samples))
identity=read(ROOT/'paper_baseline_2024/SOURCE_IDENTITY.json');put(E/'P24_SOURCE_IDENTITY_SUMMARY.json',dict(file=str(ROOT/'paper_baseline_2024/SOURCE_IDENTITY.json'),sha256=sha(ROOT/'paper_baseline_2024/SOURCE_IDENTITY.json'),top_fields={k:v for k,v in identity.items() if not isinstance(v,(list,dict))},structured_fields={k:len(v) for k,v in identity.items() if isinstance(v,(list,dict))}))
native=read(N/'CAPTURE_PROVENANCE.json');put(E/'OFFLINE_CAPTURE_IDENTITY_SUMMARY.json',dict(file=str(N/'CAPTURE_PROVENANCE.json'),sha256=sha(N/'CAPTURE_PROVENANCE.json'),top_fields={k:v for k,v in native.items() if k!='files'},upstream_file_SHAs=native['files']))
sources=[]
for rel in ['source/AUTHOR_FIX_20240918/gsl_server/src/gsl_server/algorithms/Common/Grid2D.hpp','source/AUTHOR_FIX_20240918/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp','source/AUTHOR_FIX_20240918/gsl_server/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp','source/AUTHOR_FIX_20240918/gsl_server/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp']:
 p=OLD/rel;data=p.read_bytes();sources.append(dict(**item(p),git_blob_oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),commit='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533',notes='Exact author source, not a new local repair; old audit official tree/OID proof retained.'))
sources.append(dict(**item(E.parent/'FSR_S2_NATIVE_PMFS_SINGLE_V1_20261017/public_release_origin_D2/AUTHOR_20240918_FIX.patch'),notes='Whole author commit diff includes RNG, grid and rotation changes; do not treat as an Eq6-only patch.'))
put(E/'RECTANGULAR_GRID_SOURCE_ENTRIES.json',dict(files=sources,old_component_harness=dict(path=str(OLD/'paper_component_probe.cpp'),sha256=sha(OLD/'paper_component_probe.cpp'),scope='7x7July/A6 linked-object mathematical control only; not Sep18 rectangular-grid runtime qualification'),frozen_source_gate_still_HOLD=True))
print(json.dumps(dict(observation_runs=len(obs),case_rows=[dict(run=x['run'],case=x['case'],posterior_rows=x['schema']['native_posterior_updates.csv']['rows'],updates=x['schema']['native_posterior_updates.csv']['update_ids'],consumed=x['schema']['native_window_consumption.csv']['consumed_windows'],saturated_confidence_rows=x['schema']['native_posterior_updates.csv']['confidence_one_rows']) for x in obs],bank_file_count=len(banks),ledger_type=ledger_type,ledger_sample=samples),ensure_ascii=False))
