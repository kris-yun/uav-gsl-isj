"""Source-blind MIPO patch export. No truth file or performance artifact is read."""
import argparse, csv, gzip, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path
import numpy as np

R2 = Path('/home/zyc/ros2_ws/tnqc_r2_six_offline_20260921_authoritative')
BASE = Path('/mnt/hgfs/workspace/GADEN_files/scenarios')
CONFIG = {'House01':'2,4-1_fast','House02':'3,5-1_fast','House03':'1-2,5_fast'}
RUNTIME = 'b24da77fd24bd5ea2cbb33caf856f80b9d7670e4'
RAW = '/dev/shm/house1_raw_query'
PLAYER = '/dev/shm/house2_gaden_install/gaden_player/lib/gaden_player/player'
OVERLAY = Path('/home/zyc/ros2_ws/tnqc_h01_pipeline_20260921/verified_native_v2/runtime_overlay/vgr_bridge')
OFFSETS = [-.6,-.4,-.2,0.,.2,.4,.6]

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def write(p,x):
    Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')

def rows(p):
    with open(p,newline='') as f: return list(csv.DictReader(f))

class Occupancy:
    def __init__(self,p):
        vals=[]; meta={}
        for line in Path(p).read_text().splitlines():
            line=line.strip()
            if not line or line==';':continue
            if line.startswith('#'):meta[line.split()[0].split('(')[0]]=line.split()[1:]
            else:vals.extend(map(int,line.split()))
        self.lo=np.array(list(map(float,meta['#env_min'][:3])))
        self.n=np.array(list(map(int,meta['#num_cells'][:3])))
        self.cs=float(meta['#cell_size'][0])
        self.grid=np.array(vals).reshape(self.n[2],self.n[0],self.n[1])
        assert set(np.unique(self.grid)) <= {0,1,2}

    def flag(self,x,y,z):
        ix=np.floor((np.array([x,y,z])-self.lo)/self.cs).astype(int)
        if np.any(ix<0) or np.any(ix>=self.n):return 'OUT_OF_BOUNDS'
        return str(self.grid[ix[2],ix[0],ix[1]])

    def clearance(self,x,y,z):
        if self.flag(x,y,z)!='0':return -1.
        iz=int(math.floor((z-self.lo[2])/self.cs))
        blocks=np.argwhere(self.grid[iz]!=0)
        p=np.array([x,y]); lower=self.lo[:2]+blocks*self.cs
        dist=np.linalg.norm(np.maximum(np.maximum(lower-p,p-(lower+self.cs)),0),axis=1)
        bounds=np.min(np.concatenate([p-self.lo[:2],self.lo[:2]+self.n[:2]*self.cs-p]))
        return float(min(bounds,dist.min() if len(dist) else math.inf))

def prepare(out):
    assert not (out/'anchors.csv').exists()
    (out/'raw').mkdir(exist_ok=True);(out/'logs').mkdir(exist_ok=True)
    frozen=json.loads((R2/'freeze/runtime_sha256.json').read_text())
    deps=json.loads((R2/'freeze/dependency_sha256.json').read_text())
    needed=[RAW,PLAYER,str(OVERLAY/'vgr_sim_node.py'),str(OVERLAY/'sensor_model.py'),str(OVERLAY/'sim_timebase.py')]
    verified={p:sha(p) for p in needed}
    assert all(verified[p]==frozen[p] for p in needed)
    # Verify the same GADEN libraries and preserve the frozen runtime binding record.
    for p,h in deps.items():
        if 'libgaden' in p or 'libbsc' in p:
            assert sha(p)==h
            verified[p]=h
    anchors=[]; cases=[]
    for house,config in CONFIG.items():
        occpath=BASE/house/'OccupancyGrid3D.csv';occ=Occupancy(occpath)
        gasbase=BASE/house/'gas_simulations'/config
        realization=sorted(p for p in gasbase.iterdir() if p.is_dir() and p.name.startswith('FilamentSimulation'))[0]
        frames={int(re.match(r'iteration_(\d+)',p.name)[1]):str(p) for p in realization.iterdir() if re.match(r'iteration_(\d+)',p.name)}
        maximum=max(frames)
        for seed in (0,1):
            case=f'{house}_seed{seed}';run=R2/'native'/(case+'_off_off')
            poses=rows(run/'sim_pose_trace.csv')
            # No sensor trace is read during anchor selection.
            options=[]
            for row in poses:
                p=[float(row[k]) for k in ('x','y','z')]
                options.append((float(row['t_sim_s']),p,occ.clearance(*p)))
            for target in (60,150,240):
                choice=None;window=15
                for window in (15,30):
                    pool=[x for x in options if abs(x[0]-target)<=window and x[2]>=0]
                    if pool:
                        choice=min(pool,key=lambda x:(-x[2],abs(x[0]-target),x[0]))
                    if choice is not None and choice[2]>=.70:break
                valid=choice is not None and choice[2]>=.70
                anchors.append(dict(case_id=case,House=house,seed=seed,anchor_id=f'anchor{target:03d}',
                    anchor_target_time_s=target,valid=int(valid),selection_window_s=window,
                    anchor_sim_time_s=choice[0] if valid else 'NA',
                    center_x_m=choice[1][0] if valid else 'NA',center_y_m=choice[1][1] if valid else 'NA',
                    center_z_m=choice[1][2] if valid else 'NA',clearance_m=choice[2] if choice else 'NA',
                    invalid_reason='' if valid else 'NO_FREE_NATIVE_POSE_WITH_CLEARANCE_GE_0.70'))
            cases.append(dict(case_id=case,House=house,seed=seed,config_id=config,realization_path=str(realization),
                max_iteration=maximum,occupancy_path=str(occpath),occupancy_sha256=sha(occpath),
                baseline_pose_path=str(run/'sim_pose_trace.csv'),baseline_pose_sha256=sha(run/'sim_pose_trace.csv'),
                backend='raw_house1_snapshot' if house=='House01' else 'gaden_frame_query',frames=frames))
    with (out/'anchors.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(anchors[0]),lineterminator='\n');w.writeheader();w.writerows(anchors)
    manifest=dict(contract='MIPO_V1_PROBE_DATA_CONTRACT_20260921',runtime_git_sha=RUNTIME,
        ros2_package_tree_sha=subprocess.check_output(['git','-C','/home/zyc/uav-gsl-isj','rev-parse',RUNTIME+':ros2_package'],text=True).strip(),
        definition_commit='2e21a5927b6e4ec1838017481165b0496bab2770',runtime_hashes=verified,
        anchor_sha256_before_query=sha(out/'anchors.csv'),valid_anchors=sum(a['valid'] for a in anchors),
        invalid_anchors=sum(not a['valid'] for a in anchors),cases=cases,
        clearance_definition='Exact horizontal Euclidean distance from native pose to closed blocked-cell squares at pose z; map exterior blocked. Raw occupancy 0 free, 1/2 blocked; no gas or source truth used.',
        time_mapping='step=round(query_sim_time/0.2); usable=max(1,max_iteration-1); iteration=((7919*(seed+1))%usable+step)%usable',
        samples='t=anchor_time + k*0.2, k=0..159 (last relative time 31.8s); time-major dx-major dy-minor',
        interpolation='None added; raw backend samples only',sensor_ppm_exported=False,
        sensor_ppm_limitation='No physical sensor-state history exists for each stationary patch point before the anchor. Independent resets would invent state; only raw concentration is exported.',
        truth_separation='Anchor/query script never opens truth_eval.json or endpoint/performance artifacts. Truth sidecar generated separately after raw freeze.')
    write(out/'manifest.json',manifest)
    print('ANCHORS_FROZEN',manifest['valid_anchors'],manifest['invalid_anchors'],manifest['anchor_sha256_before_query'],flush=True)

class RawBackend:
    def __init__(self,c,out):
        self.log=open(out/'logs'/(c['case_id']+'_backend.log'),'w')
        self.proc=subprocess.Popen([RAW,str(BASE/c['House']),c['realization_path']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
    def query(self,it,p):
        self.proc.stdin.write(f'{it} {p[0]:.17g} {p[1]:.17g} {p[2]:.17g}\n');self.proc.stdin.flush()
        line=self.proc.stdout.readline().strip();parts=line.split()
        if parts and parts[0]=='OK':return [float(x) for x in parts[1:5]],parts[5],''
        raise RuntimeError('raw query failed: '+line)
    def close(self):
        self.proc.stdin.close();self.proc.wait(timeout=20);self.log.close()

class FrameBackend:
    def __init__(self,c,out):
        import rclpy
        from rclpy.node import Node
        from gaden_msgs.srv import FrameQuery
        self.rclpy=rclpy;self.Request=FrameQuery.Request
        self.log=open(out/'logs'/(c['case_id']+'_backend.log'),'w')
        self.proc=subprocess.Popen([PLAYER,'--ros-args','-r','__node:=mipo_query_player','-r','__ns:=/mipo_probe','-p','num_simulators:=1',
            '-p','simulation_data_0:='+c['realization_path'],'-p','occupancyFile:='+str(BASE/c['House']/'OccupancyGrid3D.csv'),
            '-p','initial_iteration:=0','-p','player_freq:=1.0','-p','manual_iteration_mode:=true'],stdout=self.log,stderr=subprocess.STDOUT)
        rclpy.init();self.node=Node('mipo_export_query_only',namespace='/mipo_probe');self.client=self.node.create_client(FrameQuery,'frame_query')
        if not self.client.wait_for_service(timeout_sec=60):raise RuntimeError('FrameQuery unavailable')
    def query(self,it,p):
        req=self.Request();req.iteration=int(it);req.x,req.y,req.z=map(float,p)
        future=self.client.call_async(req)
        self.rclpy.spin_until_future_complete(self.node,future,timeout_sec=15)
        ans=future.result() if future.done() else None
        if ans is None:raise RuntimeError('FrameQuery timeout')
        if not ans.valid:return ['NA']*4,'NA',ans.error_message
        return [ans.concentration,ans.wind_u,ans.wind_v,ans.wind_w],'NA',''
    def close(self):
        self.node.destroy_node();self.rclpy.shutdown()
        self.proc.terminate()
        try:self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        self.log.close()

def query(out):
    m=json.loads((out/'manifest.json').read_text());assert sha(out/'anchors.csv')==m['anchor_sha256_before_query']
    anchors=rows(out/'anchors.csv');used={};audits={}
    for c in m['cases']:
        selected=[a for a in anchors if a['case_id']==c['case_id'] and a['valid']=='1']
        if not selected:continue
        occ=Occupancy(c['occupancy_path'])
        backend=(RawBackend if c['House']=='House01' else FrameBackend)(c,out)
        try:
            for a in selected:
                assert sha(out/'anchors.csv')==m['anchor_sha256_before_query']
                fname=f"{c['case_id']}_{a['anchor_id']}.csv.gz";path=out/'raw'/fname
                assert not path.exists()
                center=[float(a[k]) for k in ('center_x_m','center_y_m','center_z_m')]
                count=0;na=0
                with gzip.open(path,'wt',newline='') as f:
                    writer=None
                    for sample in range(160):
                        t=round(float(a['anchor_sim_time_s'])+sample*.2,6);step=round(t/.2)
                        usable=max(1,c['max_iteration']-1);it=((7919*(c['seed']+1))%usable+step)%usable
                        snapshot=c['frames'][str(it)];used[snapshot]=None
                        for dx in OFFSETS:
                            for dy in OFFSETS:
                                p=[center[0]+dx,center[1]+dy,center[2]];flag=occ.flag(*p)
                                values,windid,error=backend.query(it,p)
                                if error:na+=1
                                assert all(v=='NA' or math.isfinite(v) for v in values)
                                row={k:a[k] for k in ('case_id','House','seed','anchor_id','anchor_target_time_s','anchor_sim_time_s','center_x_m','center_y_m','center_z_m')}
                                row.update(sample_index=sample,frame_index=it,rel_time_s=round(sample*.2,6),query_sim_time_s=t,
                                    dx_m=dx,dy_m=dy,query_x_m=p[0],query_y_m=p[1],query_z_m=p[2],occupancy=flag,free=int(flag=='0'),
                                    raw_gaden_concentration_ppm=values[0],wind_x_mps=values[1],wind_y_mps=values[2],wind_z_mps=values[3],
                                    snapshot_id=Path(snapshot).name,wind_snapshot_id=windid,query_backend=c['backend'],backend_valid=int(not error),backend_error=error)
                                if writer is None:writer=csv.DictWriter(f,fieldnames=list(row),lineterminator='\n');writer.writeheader()
                                writer.writerow(row);count+=1
                assert count==7840
                audits[fname]=dict(rows=count,backend_na_rows=na)
                print('RAW_EXPORTED',fname,count,'backend_na_rows',na,flush=True)
        finally:backend.close()
    # Hash queried gas snapshots, occupancy, and all realization wind files; list every realization file.
    listing={}
    for c in m['cases']:
        root=Path(c['realization_path'])
        if str(root) in listing:continue
        listing[str(root)]=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size) for p in sorted(root.rglob('*')) if p.is_file()]
        used[c['occupancy_path']]=None
        for p in (root/'wind').rglob('*'):
            if p.is_file():used[str(p)]=None
    for i,p in enumerate(sorted(used)):
        used[p]=sha(p)
        if i%200==0:print('HASHING_DATA',i,len(used),flush=True)
    write(out/'gaden_data_listing.json',listing);write(out/'gaden_content_sha256.json',used)
    m['gaden_content_manifest_sha256']=sha(out/'gaden_content_sha256.json')
    m['gaden_listing_sha256']=sha(out/'gaden_data_listing.json');m['raw_files']=audits
    m['backend_limitations']='FrameQuery returns no separate wind snapshot id: NA. Requested gas iteration snapshot id is present. Invalid backend replies retained as NA with original error, never used to move anchors.'
    write(out/'manifest.json',m)
    print('QUERY_EXPORT_COMPLETE',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','query']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    globals()[a.phase](a.out)
