import hashlib
from pathlib import Path
import numpy as np

root=Path('/home/zyc/PF_DEI_V3_NATIVE_TRACE_SMOKE_20260828')
def read(path, seed):
    a=np.loadtxt(path, delimiter=',')
    # q=0 is the fixed source-relative query; retain its chronological prefix.
    return a[a[:,1]==0,2]

physical=np.stack([
    np.stack([read(root/'a.csv',101), read(root/'a2.csv',211)]),
    np.stack([read(root/'b.csv',101), read(root/'b2.csv',211)]),
])
T=physical.shape[-1]
z=np.asarray([[-7.1,-7.43,-0.669],[-7.0,-7.43,-0.669]],dtype=float)
payload=dict(
 candidate_physical_ppm=physical,
 sample_time_s=np.arange(T,dtype=float)*0.1+0.1,
 pose_xyz_m=np.tile(np.asarray([[-7.1,-7.43,-0.669]],dtype=float),(T,1)),
 source_xyz_m=z, geometry_prior=np.asarray([.5,.5]),
 source_id=np.asarray(['quadtree_0_0_2_2_cell0','quadtree_0_0_2_2_cell1']),
 transport_id=np.asarray(['member_101','member_211']), transport_seed=np.asarray([101,211],dtype=np.int64),
 house=np.asarray('House01'), run_seed=np.asarray(314159,dtype=np.int64),
 source_support_sha256=np.asarray('4fec448feed607ea8c63148750ae9a610cf2e837a3df30808a256402c2d3a402'),
 transport_manifest_sha256=np.asarray('0'*64), trajectory_sha256=np.asarray('1'*64), query_binary_sha256=np.asarray('2'*64),
 gaden_source_sha256=np.asarray('3'*64), gaden_config_sha256=np.asarray('4'*64), overlay_sha256=np.asarray('5'*64))
np.savez_compressed(root/'v3_smoke_bank.npz',**payload)
print(root/'v3_smoke_bank.npz', physical.shape)
