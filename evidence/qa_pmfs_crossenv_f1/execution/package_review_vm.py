#!/usr/bin/env python3
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path('/home/zyc/qa_pmfs_crossenv_f1_20260926')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['CANDIDATE_SCORES.csv','TARGET_METRICS.csv','SOURCE_METRICS.csv','ENVIRONMENT_METRICS.csv','F1_RESULT.json']
assert {p.name for p in (ROOT/'result').iterdir()}==set(names)
assert {p.name for p in (ROOT/'repeat').iterdir()}==set(names)
record={name:{'first_sha256':sha(ROOT/'result'/name),'repeat_sha256':sha(ROOT/'repeat'/name),'byte_identical':(ROOT/'result'/name).read_bytes()==(ROOT/'repeat'/name).read_bytes()} for name in names}
assert all(v['byte_identical'] for v in record.values())
(ROOT/'DETERMINISTIC_REPEAT.json').write_text(json.dumps({'pass':True,'files':record},indent=2,sort_keys=True)+'\n')
review=ROOT/'review';review.mkdir(exist_ok=False)
for name in ['protocol','execution','g7_amendment','historical','audit','reference_freeze','result','repeat','PRE_TARGET_FREEZE.json','DETERMINISTIC_REPEAT.json','asset_audit_commit.txt','pre_target_freeze_commit.txt','self_test.log','reference_fit.log','scoring.log','repeat.log']:
    p=ROOT/name
    if p.is_dir():shutil.copytree(p,review/name,ignore=shutil.ignore_patterns('__pycache__'))
    else:shutil.copy2(p,review/name)
# The raw archive has been historically verified; concentration tensors and
# manifests in this package permit independent recomputation of all QA scores.
old=Path('/home/zyc/JTD_E2_RAW_180_20260925.tar.gz');shutil.copy2(old,review/old.name)
provenance={'branch':'research/qa-pmfs-crossenv-f1-20260926','asset_audit_commit':(ROOT/'asset_audit_commit.txt').read_text().strip(),'pre_target_freeze_commit':(ROOT/'pre_target_freeze_commit.txt').read_text().strip(),'provided_core_modified':False,'new_plumes':0,'closed_loop_runs':0,'networks_trained':0,'sealed_House01_or_House03_read':False,'reference_only_selection':True,'historical_JTD_result_reused_as_input_to_QA':False,'G7_amendment_sha256':sha(ROOT/'execution/G7_PRE_TARGET_AMENDMENT.md'),'raw_archive_sha256':sha(old),'target_reference_tensors':'historical/JTD_E2_REFERENCE_12x10x30.npy and historical/JTD_E2_FRESH_TARGET_10x30.npy','GH_nodes':40,'historical_JTD_targets_previously_inspected':True,'target_values_excluded_from_QA_pre_target_freeze':True}
(review/'EXECUTION_PROVENANCE.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
files=[p for p in sorted(review.rglob('*')) if p.is_file()]
(review/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(review))+'\n' for p in files))
archive=ROOT/'QA_PMFS_CROSSENV_F1_REVIEW_20260926.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(review.rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(review)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for line in z.read('SHA256SUMS').decode().splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==expected
meta={'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'verified_internal_files':len(files)}
(ROOT/'REVIEW_PACKAGE.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':json.loads((ROOT/'result/F1_RESULT.json').read_text())['decision'],'deterministic_repeat':'PASS','package':meta},indent=2,sort_keys=True))
