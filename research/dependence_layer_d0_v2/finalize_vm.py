#!/usr/bin/env python3
"""Verify exact repeat and package independently recomputable review data."""
import csv,hashlib,json,shutil,tarfile,zipfile
from pathlib import Path
root=Path('/home/zyc/dependence_layer_d0_v2_20260926')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['input_inventory.csv','within_source_surrogates_500.csv','D0_RESULT.json']
assert {p.name for p in (root/'result').iterdir()}==set(names)
assert {p.name for p in (root/'repeat').iterdir()}==set(names)
files={name:{'first_sha256':sha(root/'result'/name),'repeat_sha256':sha(root/'repeat'/name),'byte_identical':(root/'result'/name).read_bytes()==(root/'repeat'/name).read_bytes()} for name in names}
assert all(r['byte_identical'] for r in files.values())
assert len(list(csv.DictReader((root/'result/within_source_surrogates_500.csv').open())))==500
record={'pass':True,'files':files,'freeze_commit':(root/'freeze_commit.txt').read_text().strip(),'analyzer_changed_after_freeze':False}
(root/'DETERMINISTIC_REPEAT.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
review=root/'review';review.mkdir(exist_ok=False)
for name in ['protocol','execution','contracts','result','repeat','PREFLIGHT.json','DETERMINISTIC_REPEAT.json','freeze_commit.txt','analysis.log','repeat.log','self_test.log','git_state_before_execution.txt']:
    p=root/name
    if p.is_dir():shutil.copytree(p,review/name,ignore=shutil.ignore_patterns('__pycache__'))
    else:shutil.copy2(p,review/name)
old=Path('/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz')
shutil.copy2(old,review/old.name)
with tarfile.open(old,'r:gz') as tf:
    prefix='R0_STOCHASTIC_BENCHMARK_REVIEW_20260924/compact_data/'
    for member in tf.getmembers():
        if member.isfile() and member.name.startswith(prefix):
            p=review/'inputs/compact_data'/member.name[len(prefix):]
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(member).read())
provenance={'branch':'research/dependence-layer-d0-v2-20260926','freeze_commit':record['freeze_commit'],'source_package_sha256':'6b7ca5909b76bb41568d5046819f1178df99fee1f0d144460dab2f2517bd60c5','R0_archive_sha256':sha(old),'new_simulations':0,'PMFS_runs':0,'neural_training':0,'historical_R0_modified':False,'scientific_analyzer_modified':False,'V1_status':'previously executed as exploratory, superseded because attribution controls were insufficient','recompute':'python3 protocol/analyze_dependence_layers_d0.py --data-root inputs --seed-matrix contracts/R0_SEED_MATRIX_18x16.tsv --out-dir independent_result','input_inventory_paths':'Original VM paths retained; packaged equivalent under inputs/compact_data.'}
(review/'EXECUTION_PROVENANCE.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
items=[p for p in sorted(review.rglob('*')) if p.is_file()]
(review/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(review))+'\n' for p in items))
archive=root/'DEPENDENCE_LAYER_D0_V2_REVIEW_20260926.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(review.rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(review)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for line in z.read('SHA256SUMS').decode().splitlines():
        expected,name=line.split('  ',1)
        assert hashlib.sha256(z.read(name)).hexdigest()==expected
metadata={'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'verified_internal_files':len(items)}
(root/'REVIEW_PACKAGE.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':json.loads((root/'result/D0_RESULT.json').read_text())['decision'],'deterministic_repeat':'PASS','package':metadata},indent=2))
