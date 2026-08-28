import csv, os, subprocess, hashlib, json
from pathlib import Path
import numpy as np

manifest=Path('/home/zyc/PF_DEI_V3_REGION_SUPPORT_20260828/source_region_3d_support_manifest.csv')
out=Path('/home/zyc/PF_DEI_V3_NATIVE_TRACE_BATCH_SMOKE_20260828'); out.mkdir(exist_ok=True)
env_path='/mnt/hgfs/workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv'
wind='/home/zyc/rmfe_cl_env/H01/wind'
probe='/tmp/probe_pat2/install/bin/gaden_probe'
ld='/opt/ros/humble/lib:/home/zyc/PF_DEI_V3_GADEN_BUILD/install/lib:/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc'
rows=[]
with manifest.open(newline='') as f:
    for r in csv.DictReader(f):
        if r['house']=='H01': rows.append(r)
rows=rows[:3]
seeds=[101,211]
records=[]
for r in rows:
    x,y=r['pmfs_x'],r['pmfs_y']; z=r['legal_heights_m'].split(';')[0]
    for seed in seeds:
        fn=out/f"{r['carrier_id']}_seed{seed}.csv"
        e=os.environ.copy(); e.update({'OMP_NUM_THREADS':'1','GADEN_RNG_SEED':str(seed),'LD_LIBRARY_PATH':ld})
        subprocess.run([probe,env_path,wind,x,y,z,str(fn),str(seed)],env=e,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        a=np.loadtxt(fn,delimiter=','); q0=a[a[:,1]==0,2]
        records.append({'carrier_id':r['carrier_id'],'seed':seed,'source_xyz':[float(x),float(y),float(z)],'trace_sha256':hashlib.sha256(fn.read_bytes()).hexdigest(),'q0_max':float(q0.max()),'q0_sum':float(q0.sum()),'finite':bool(np.all(np.isfinite(a)))})
(out/'manifest.json').write_text(json.dumps({'contract':'PF_DEI_V3_NATIVE_TRACE_BATCH_SMOKE','rows':records},indent=2,sort_keys=True)+'\n')
print(json.dumps({'rows':len(records),'all_finite':all(x['finite'] for x in records),'unique_traces':len({x['trace_sha256'] for x in records})},sort_keys=True))
