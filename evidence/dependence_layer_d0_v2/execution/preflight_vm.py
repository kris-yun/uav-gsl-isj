#!/usr/bin/env python3
"""Read-only input integrity preflight; no scientific scoring."""
import csv,hashlib,json,platform,tarfile
from pathlib import Path
import numpy as np
import pandas as pd
root=Path('/home/zyc/dependence_layer_d0_v2_20260926')
data=Path('/home/zyc/r0_stochastic_benchmark_20260924')
archive=Path('/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)=='030c7aa814c4edfe0c6912bb4fc7faf36970142911e0f6c28822f2dd39049c1e'
for line in (root/'protocol/SHA256SUMS.txt').read_text().splitlines():
    expected,name=line.split('  ',1)
    assert sha(root/'protocol'/name)==expected,name
with tarfile.open(archive,'r:gz') as tf:
    prefix='R0_STOCHASTIC_BENCHMARK_REVIEW_20260924/'
    lines=tf.extractfile(prefix+'SHA256SUMS.txt').read().decode().splitlines()
    for line in lines:
        expected,name=line.split('  ',1)
        assert hashlib.sha256(tf.extractfile(prefix+name.removeprefix('./')).read()).hexdigest()==expected,name
    for name in ('R0_SEED_MATRIX_18x16.tsv','R0_ARTIFACT_SHA256.tsv'):
        assert tf.extractfile(prefix+'repo/'+name).read()==(root/'contracts'/name).read_bytes()
    sm=list(csv.DictReader((root/'contracts/R0_SEED_MATRIX_18x16.tsv').open(),delimiter='\t'))
    art={(r['source_id'],int(r['replicate']),int(r['rng_seed'])):r for r in csv.DictReader((root/'contracts/R0_ARTIFACT_SHA256.tsv').open(),delimiter='\t')}
    assert len(sm)==len(art)==288
    sources={r['source_id'] for r in sm}
    assert len(sources)==18 and len({int(r['rng_seed']) for r in sm})==288
    assert all({int(r['replicate']) for r in sm if r['source_id']==sid}==set(range(1,17)) for sid in sources)
    assert len(list(data.glob('*/rep_*/pooled.npy')))==288
    inventory=[]
    for r in sm:
        sid=r['source_id'];rep=int(r['replicate']);seed=int(r['rng_seed'])
        rel=f'{sid}/rep_{rep:02d}_seed_{seed}/pooled.npy'; p=data/rel
        expected=art[(sid,rep,seed)]['pooled_sha256']
        assert sha(p)==expected
        assert hashlib.sha256(tf.extractfile(prefix+'compact_data/'+rel).read()).hexdigest()==expected
        z=np.load(p,allow_pickle=False)
        assert z.shape==(10,30) and np.isfinite(z).all() and (z>=0).all()
        inventory.append({'source_id':sid,'replicate':rep,'rng_seed':seed,'path':str(p),'bytes':p.stat().st_size,'sha256':expected})
record={'pass':True,'sources':18,'replicates_per_source':16,'realizations':288,'historical_archive_sha256':sha(archive),'historical_archive_files_verified':len(lines),'all_pooled_match_archive_and_committed_R0_inventory':True,'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'inventory':inventory}
(root/'PREFLIGHT.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('V2_INPUT_PREFLIGHT_PASS 18x16 arrays=288')
