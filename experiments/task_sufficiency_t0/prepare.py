"""Read-only reuse of qualified S2/S2X; source-blind connected routes and native query."""
import csv,hashlib,json,subprocess,tarfile,shlex
from pathlib import Path
import numpy as np
import pandas as pd
from collections import deque
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'evidence/task_sufficiency_t0_20261003'; OUT.mkdir(parents=True,exist_ok=True)
SRC=Path(__file__).parent; OLD=Path(r'D:\ZYC\A-gas\_worktrees\mdbil-d0-20261001'); REM='/home/zyc/task_sufficiency_t0_20261003'; HOST='zyc@192.168.111.128'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout
def ssh(s):return run(['ssh',HOST,'source /opt/ros/humble/setup.bash && export LD_LIBRARY_PATH=/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH && '+s])
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def main():
 protocol={'cases':{'H01/s0':0,'H01/s1':2,'H02/s0':4,'H02/s1':6},'alias_note':'s0/s1 are fixed fast wind/gas contexts, NOT source labels; each case contains both S1 and S2', 'time_s':[100,700,2],'flight_z_request_m':.2,'route':'largest connected free-cell slice; source-blind 1m lattice waypoints joined by 4-connected shortest paths; 0.2 m/s, repeat','history_s':40,'stride_s':10,'horizons_s':[10,30],'hit_ppm':.001,'split':'4-fold leave-one-replicate-per-source out; train3 independent realizations/source; no test-driven tuning','models':['raw','statistics','generic','source_only','joint'],'latent_dim':8,'training_seed':61003,'epochs':160,'loss_joint':'CE(source)+BCE(future hits)+0.1 MSE(log1p concentration)+0.01 latent L2+0.1 matched-time same-source/context variance across training realizations','gate':'rank noninferior >=3/4; median rank improvement>0 OR median AUC gain>=.05 vs raw; mean 10/30 Brier and NLL improve vs source_only; conditional realization probe decreases vs generic and joint source probe >=.75','nuisance_probe':'heldout realizations only; conditional on source, classify four replicate IDs using nonoverlapping early vs late windows separated by >=70s; diagnostic temporal extrapolation, not unseen-ID generalization','no_new_simulation':True}
 save('PROTOCOL_FROZEN.json',protocol)
 ssh('mkdir -p '+REM)
 run(['scp',str(SRC/'query.cpp'),HOST+':'+REM+'/query.cpp'])
 build="""import pathlib,subprocess,shlex
b=pathlib.Path('/home/zyc/ocb_r2_seeded_gaden'); f=(b/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text().splitlines(); inc=next(x.split(' = ',1)[1] for x in f if x.startswith('CXX_INCLUDES')); lib=b/'install/gaden_common/lib'; bsc=b/'build/gaden_common/third_party/gaden_core/third_party/libbsc'
subprocess.run(['g++','-std=c++20','-O3','-DGADEN_ROS=1']+shlex.split(inc)+['REMDIR/query.cpp','-L'+str(lib),'-Wl,-rpath,'+str(lib),'-Wl,-rpath,'+str(bsc),'-Wl,-rpath-link,'+str(bsc),'-lgaden','-o','REMDIR/query'],check=True)
""".replace('REMDIR',REM)
 (OUT/'build_native.py').write_text(build);run(['scp',str(OUT/'build_native.py'),HOST+':'+REM+'/build_native.py']); print(ssh('source /opt/ros/humble/setup.bash && python3 '+REM+'/build_native.py'),flush=True)
 save('RUNTIME.json',{'native_lib_sha256':ssh('sha256sum /home/zyc/ocb_r2_seeded_gaden/install/gaden_common/lib/libgaden.so').split()[0],'query_sha256':ssh('sha256sum '+REM+'/query').split()[0],'source_sha256':sha(SRC/'query.cpp'),'adapter':'native PlaybackSimulation::LoadIteration/SampleWind/SampleConcentration; occupancy LOS and 3-sigma cutoff unchanged'})
 routes={}
 for house in ['House01','House02']:
  occ='/mnt/hgfs/workspace/GADEN_files/scenarios/'+house+'/OccupancyGrid3D.csv';ssh(REM+'/query '+occ+' '+REM+'/'+house+'_free.csv');run(['scp',HOST+':'+REM+'/'+house+'_free.csv',str(OUT)])
  free=pd.read_csv(OUT/(house+'_free.csv')); points={(int(r.ix),int(r.iy)):(r.x,r.y,r.z) for r in free.itertuples()}; remaining=set(points); comps=[]
  while remaining:
   start=min(remaining); seen={start}; q=deque([start]);remaining.remove(start)
   while q:
    p=q.popleft()
    for n in [(p[0]+1,p[1]),(p[0]-1,p[1]),(p[0],p[1]+1),(p[0],p[1]-1)]:
     if n in remaining:remaining.remove(n);seen.add(n);q.append(n)
   comps.append(seen)
  legal=max(comps,key=len); way=sorted(p for p in legal if p[0]%10==0 and p[1]%10==0); assert len(way)>10
  path=[way[0]]
  for target in way[1:]+way[:1]:
   q=deque([path[-1]]);prev={path[-1]:None}
   while target not in prev:
    p=q.popleft()
    for n in [(p[0]+1,p[1]),(p[0]-1,p[1]),(p[0],p[1]+1),(p[0],p[1]-1)]:
     if n in legal and n not in prev:prev[n]=p;q.append(n)
   tail=[];p=target
   while prev[p] is not None:tail.append(p);p=prev[p]
   path.extend(reversed(tail))
  routes[house]=np.array([points[path[(k*4)%(len(path)-1)]] for k in range(301)])
  pd.DataFrame(routes[house],columns=['x','y','z']).to_csv(OUT/(house+'_route.csv'),index=False)
 selected=[]
 for phase,rl in [('S2',OLD/'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'),('S2X',OLD/'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv')]:
  for r in csv.DictReader(rl.open(encoding='utf-8-sig'),delimiter='\t'):
   ci=int(r['config_index'] if phase=='S2' else r['parent_s2_config_index'])
   if ci not in protocol['cases'].values():continue
   folder=Path(r'C:\GADEN_OCB_R2_ARCHIVE')/('s2_discovery' if phase=='S2' else 's2x_matched_source')/r['run_id']; m=json.loads((folder/'RUN_MANIFEST.json').read_text());t=pd.read_csv(folder/'RECORD_TIMELINE.tsv',sep='\t'); times=np.arange(100,701,2); idx=np.searchsorted(t.internal_simulation_time_s,times,side='right')-1
   r.update(phase=phase,context=next(k for k,v in protocol['cases'].items() if v==ci),replicate=int(r['run_id'].rsplit('_r',1)[1]),folder=str(folder),manifest_sha256=sha(folder/'RUN_MANIFEST.json')); selected.append(r)
   route=pd.DataFrame(routes[r['house']],columns=['x','y','z']);route.insert(0,'record_index',idx);route.insert(0,'time',times);route.to_csv(OUT/(r['run_id']+'.route.csv'),index=False)
   hashes=pd.read_csv(folder/'OUTPUT_SHA256SUMS.tsv',sep='\t');
   # Archive selected native bytes with verified hashes; avoid modifying original archive.
   with tarfile.open(OUT/'stage.tar','w') as tar:
    for i in sorted(set(idx)):
     p=folder/f'iteration_{i}'; digest=sha(p); expected=hashes.loc[hashes['name']==p.name,'sha256'].iloc[0];assert digest==expected,(p,digest,expected);tar.add(p,arcname=r['run_id']+'/'+p.name)
    for p in (folder/'wind').iterdir():tar.add(p,arcname=r['run_id']+'/wind/'+p.name)
   existing=OUT/(r['run_id']+'.observations.csv')
   if existing.exists() and len(pd.read_csv(existing))==301: print(r['run_id']+' verified existing query',flush=True);continue
   run(['scp',str(OUT/'stage.tar'),HOST+':'+REM+'/stage.tar']); run(['scp',str(OUT/(r['run_id']+'.route.csv')),HOST+':'+REM+'/route.csv']);ssh('tar -xf '+REM+'/stage.tar -C '+REM)
   occ='/mnt/hgfs/workspace/GADEN_files/scenarios/'+r['house']+'/OccupancyGrid3D.csv'
   assert ssh('sha256sum '+occ).split()[0]==m['asset_checks']['occupancy_sha256']
   ssh(REM+'/query '+occ+' '+REM+'/'+r['run_id']+' '+REM+'/route.csv '+REM+'/observations.csv');run(['scp',HOST+':'+REM+'/observations.csv',str(OUT/(r['run_id']+'.observations.csv'))]); print(r['run_id']+' queried',flush=True)
   cleanup="import pathlib,shutil; root=pathlib.Path('"+REM+"').resolve(); p=(root/'"+r['run_id']+"').resolve(); assert p.parent==root and p.name.startswith('ocb_r2_'); shutil.rmtree(p)"
   ssh('python3 -c '+shlex.quote(cleanup))
 save('RUNS.json',selected)
 assert len(selected)==32 and len({r['master_seed'] for r in selected})==32
 print('32 independent realizations complete',flush=True)
if __name__=='__main__':main()
