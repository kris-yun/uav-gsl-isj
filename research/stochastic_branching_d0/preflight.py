#!/usr/bin/env python3
"""Read-only schema/hash checks. Does not calculate branching scores."""
import csv,hashlib,io,json,platform,tarfile
from pathlib import Path
import numpy as np
import pandas as pd
root=Path('/home/zyc/stochastic_branching_d0_20260926')
code=root/'protocol';data=Path('/home/zyc/r0_stochastic_benchmark_20260924')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=Path('/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz')
assert sha(archive)=='030c7aa814c4edfe0c6912bb4fc7faf36970142911e0f6c28822f2dd39049c1e'
for line in (code/'SHA256SUMS.txt').read_text().splitlines():
    expected,name=line.split('  ',1);assert sha(code/name)==expected,name
with tarfile.open(archive,'r:gz') as tf:
    prefix='R0_STOCHASTIC_BENCHMARK_REVIEW_20260924/'
    lines=tf.extractfile(prefix+'SHA256SUMS.txt').read().decode().splitlines()
    for line in lines:
        expected,name=line.split('  ',1)
        assert hashlib.sha256(tf.extractfile(prefix+name.removeprefix('./')).read()).hexdigest()==expected,name
    for name in ['R0_SEED_MATRIX_18x16.tsv','R0_ARTIFACT_SHA256.tsv']:
        assert tf.extractfile(prefix+'repo/'+name).read()==(root/'contracts'/name).read_bytes(),name
    sm=list(csv.DictReader((root/'contracts/R0_SEED_MATRIX_18x16.tsv').open(),delimiter='\t'))
    artifacts={ (r['source_id'],int(r['replicate']),int(r['rng_seed'])):r for r in csv.DictReader((root/'contracts/R0_ARTIFACT_SHA256.tsv').open(),delimiter='\t')}
    assert len(sm)==288 and len(artifacts)==288
    pairs={(r['source_id'],int(r['replicate'])) for r in sm};assert len(pairs)==288
    sids={r['source_id'] for r in sm};assert len(sids)==18
    assert len({int(r['rng_seed']) for r in sm})==288
    assert all({int(r['replicate']) for r in sm if r['source_id']==s}==set(range(1,17)) for s in sids)
    assert len(list(data.glob('*/rep_*/pooled.npy')))==288
    inventory=[]
    for r in sm:
        sid=r['source_id'];rep=int(r['replicate']);seed=int(r['rng_seed'])
        rel=f'{sid}/rep_{rep:02d}_seed_{seed}/pooled.npy';p=data/rel
        expected=artifacts[(sid,rep,seed)]['pooled_sha256']
        assert sha(p)==expected,rel
        assert hashlib.sha256(tf.extractfile(prefix+'compact_data/'+rel).read()).hexdigest()==expected,rel
        z=np.load(p,allow_pickle=False)
        assert z.shape==(10,30) and np.isfinite(z).all() and (z>=0).all(),rel
        inventory.append({'source_id':sid,'replicate':rep,'rng_seed':seed,'path':str(p),'bytes':p.stat().st_size,'sha256':expected,'shape':[10,30],'dtype':str(z.dtype)})
record={'pass':True,'source_count':18,'realizations_per_source':16,'total_realizations':288,'archive_sha256':sha(archive),'historical_archive_inventory_files_verified':len(lines),'all_pooled_match_historical_archive_and_committed_R0_inventory':True,'contract_hashes':{p.name:sha(p) for p in (root/'contracts').iterdir() if p.is_file()},'protocol_hashes':{p.name:sha(p) for p in code.iterdir() if p.is_file()},'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'platform':platform.platform()},'inventory':inventory}
(root/'PREFLIGHT.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('DATA_AND_PACKAGE_PREFLIGHT_PASS sources=18 replicates=16 arrays=288 historical_files='+str(len(lines)))
