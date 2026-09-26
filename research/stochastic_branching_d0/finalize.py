#!/usr/bin/env python3
import csv,hashlib,json,shutil,tarfile,zipfile
from pathlib import Path
root=Path('/home/zyc/stochastic_branching_d0_20260926');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['D0_RESULT.json','input_inventory.csv','mean_preserving_residual_null_500.csv']
assert {p.name for p in (root/'result').iterdir()}==set(names)
assert {p.name for p in (root/'repeat').iterdir()}==set(names)
comp={name:{'first_sha256':sha(root/'result'/name),'repeat_sha256':sha(root/'repeat'/name),'byte_identical':(root/'result'/name).read_bytes()==(root/'repeat'/name).read_bytes()} for name in names}
assert all(x['byte_identical'] for x in comp.values())
assert len(list(csv.DictReader((root/'result/mean_preserving_residual_null_500.csv').open())))==500
record={'pass':True,'files':comp,'scientific_analyzer_modified':False,'infrastructure_only_patch':False,'freeze_commit':(root/'freeze_commit.txt').read_text().strip()}
(root/'DETERMINISTIC_REPEAT.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
review=root/'review';review.mkdir(exist_ok=False)
for name in ['protocol','execution','contracts','result','repeat','PREFLIGHT.json','DETERMINISTIC_REPEAT.json','freeze_commit.txt','analysis.log','repeat.log','self_test.log','git_state_before_execution.txt']:
    p=root/name
    if p.is_dir():shutil.copytree(p,review/name,ignore=shutil.ignore_patterns('__pycache__'))
    else:shutil.copy2(p,review/name)
old=Path('/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz')
shutil.copy2(old,review/old.name)
with tarfile.open(old) as tf:
    for member in tf.getmembers():
        prefix='R0_STOCHASTIC_BENCHMARK_REVIEW_20260924/compact_data/'
        if member.isfile() and member.name.startswith(prefix):
            p=review/'inputs/compact_data'/member.name[len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(member).read())
provenance={'freeze_commit':record['freeze_commit'],'branch':'research/stochastic-branching-d0-20260926','package_sha256':'cd21c750bdfc2138f3c5c218f3708a3d14608db9c92528541eeff26a8be70650','R0_archive_sha256':sha(old),'source_count':18,'realizations_per_source':16,'new_simulations':0,'PMFS_runs':0,'neural_training':0,'historical_evidence_modified':False,'analyzer_modified':False,'infrastructure_only_patch':False,'recompute':'python3 protocol/analyze_branching_d0.py --data-root inputs --seed-matrix contracts/R0_SEED_MATRIX_18x16.tsv --out-dir independent_result','inventory_paths':'Original VM canonical paths retained in input_inventory.csv; packaged equivalents under inputs/compact_data.'}
(review/'EXECUTION_PROVENANCE.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
files=[p for p in sorted(review.rglob('*')) if p.is_file()]
(review/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(review))+'\n' for p in files))
archive=root/'STOCHASTIC_BRANCHING_D0_REVIEW_20260926.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(review.rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(review)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for line in z.read('SHA256SUMS').decode().splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==expected
metadata={'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'verified_internal_files':len(files)}
(root/'REVIEW_PACKAGE.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':json.loads((root/'result/D0_RESULT.json').read_text())['decision'],'deterministic_repeat':'PASS','package':metadata},indent=2))
