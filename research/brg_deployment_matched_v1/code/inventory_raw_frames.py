from pathlib import Path
import os,json,numpy as np
home=Path('/home/zyc'); raw=[]; cubes=[]
exclude={'.git','build','install','log','__pycache__','node_modules','wind','shared_workspace','ros2_ws'}
for current,dirs,files in os.walk(home):
    dirs[:]=[d for d in dirs if d not in exclude and 'house03' not in d.lower() and not d.startswith('SEALED')]
    path=Path(current)
    if len(path.relative_to(home).parts)>9:dirs[:]=[];continue
    if 'E2_CROSS_ENVIRONMENT_168_RUNS_20260925' in str(path) and 'OPEN_DISCOVERY' not in str(path):
        dirs[:]=[d for d in dirs if d=='OPEN_DISCOVERY']
    iterations=sorted(f for f in files if f.startswith('iteration_'))
    if iterations:
        row={'path':str(path),'frames':len(iterations),'first_names':iterations[:3],'last_names':iterations[-3:]}
        raw.append(row);print(json.dumps(row),flush=True)
    if 'concentration.npy' in files and any(k in str(path) for k in ('JTD_E2_K12','E2_CROSS_ENVIRONMENT_168_RUNS','r0_stochastic_benchmark_20260924','cess_d1r_168x16')):
        a=np.load(path/'concentration.npy',mmap_mode='r',allow_pickle=False)
        cubes.append({'path':str(path/'concentration.npy'),'shape':list(a.shape),'dtype':str(a.dtype),'raw_frames_retained':len(iterations)})
out={'raw_directories':raw,'cube_headers':cubes,'payloads_read':False,'sealed_concentrations_read':False}
dest=home/'brg_v1_raw_frames_inventory_20260928.json';dest.write_text(json.dumps(out,indent=2))
print('SAVED',dest,'RAW_DIRECTORIES',len(raw),'CUBE_HEADERS',len(cubes),flush=True)
