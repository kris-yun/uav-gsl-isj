import json
from pathlib import Path
import numpy as np
root=Path('/home/zyc/PF_DEI_V3_NATIVE_TRACE_BATCH_SMOKE_20260828')
rows=json.loads((root/'manifest.json').read_text())['rows']
carriers=[]; seeds=[]
for x in rows:
    if x['carrier_id'] not in carriers: carriers.append(x['carrier_id'])
    if x['seed'] not in seeds: seeds.append(x['seed'])
S,M=len(carriers),len(seeds); physical=np.zeros((S,M,30)); src=[]
for i,c in enumerate(carriers):
    for j,s in enumerate(seeds):
        a=np.loadtxt(root/f'{c}_seed{s}.csv',delimiter=','); physical[i,j]=a[a[:,1]==0,2]
    src.append(next(x['source_xyz'] for x in rows if x['carrier_id']==c))
h=lambda n: str(n)*64
np.savez_compressed(root/'v3_batch_bank.npz',candidate_physical_ppm=physical,sample_time_s=np.arange(30)*.1+.1,pose_xyz_m=np.tile(np.asarray(src[0]),(30,1)),source_xyz_m=np.asarray(src),geometry_prior=np.ones(S)/S,source_id=np.asarray(carriers),transport_id=np.asarray(['member_101','member_211']),transport_seed=np.asarray(seeds,dtype=np.int64),house=np.asarray('House01'),run_seed=np.asarray(314159,dtype=np.int64),source_support_sha256=np.asarray('4fec448feed607ea8c63148750ae9a610cf2e837a3df30808a256402c2d3a402'),transport_manifest_sha256=np.asarray(h(0)),trajectory_sha256=np.asarray(h(1)),query_binary_sha256=np.asarray(h(2)),gaden_source_sha256=np.asarray(h(3)),gaden_config_sha256=np.asarray(h(4)),overlay_sha256=np.asarray(h(5)))
print('bank',physical.shape)
