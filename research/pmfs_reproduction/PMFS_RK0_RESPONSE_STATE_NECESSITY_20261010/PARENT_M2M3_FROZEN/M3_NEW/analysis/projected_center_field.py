"""Common native-style centre-frequency field from existing 3D paths only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,importlib.util,math
import numpy as np
import cv2
W=Path(__file__).resolve().parent;B=W.parents[1]
M2=B/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010';M1=B/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
O=B/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010';D=O/'projected_center_field'
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def writecsv(p,rs):
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def analyse(m1,m2,out):
    inp=rows(m1/'snapshot/input.csv');meta=js(m2/'native_reference_evidence/FROZEN_METADATA.json');nx,ny=meta['width'],meta['height']
    free=np.array([r['occupancy']=='1' for r in inp]);shape=(ny,nx);mask=free.astype(np.float32).reshape(shape)
    origin=np.array([meta['origin_x'],meta['origin_y']],dtype=np.float32);cell=np.float32(meta['cell_size'])
    observed=1-1/(1+np.exp([float(r['logOdds']) for r in inp]));conf=np.array([float(r['confidence']) for r in inp])
    def blur(a):
        im=cv2.GaussianBlur(a.reshape(shape).astype(np.float32),(0,0),1.5,1.5)
        denom=cv2.GaussianBlur(mask,(0,0),1.5,1.5)
        return np.where(denom!=0,np.clip(im/np.where(denom==0,1,denom),0,1),im).astype(np.float32).ravel()
    def score(a):
        factors=1-.4*np.abs(observed-a.astype(float))*conf
        return math.fsum(math.log(float(f)) for f in factors[free])
    anchor=[]
    for job in ['T_true_fine','T_wrong_fine','W_true_fine','anchor_W_fine']:
        folder=m1/'evidence/forwards'/job/'maps';rawp=next(folder.glob('*_unblurred.f32'));p=next(p for p in folder.glob('*.f32') if '_unblurred' not in p.name)
        raw=np.fromfile(rawp,dtype='<f4');actual=np.fromfile(p,dtype='<f4');got=blur(raw)
        diff=float(np.max(np.abs(got-actual)));assert diff<=2e-7
        anchor.append(dict(job=job,blur_map_max_abs_difference=diff,score_log_difference=score(got)-score(actual),native_source_sha256=sha(p),python_cv2_version=cv2.__version__))
    sp=importlib.util.spec_from_file_location('raw',m2/'independent_raw_query_verify/verify_raw_receiver_queries.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
    fields={};bankrows=[];percell=[]
    for bank in sorted((m2/'native_reference_evidence/realizations').iterdir()):
        if not bank.is_dir():continue
        schedule=[s for s in rows(bank/'QUERY_PHYSICAL_LINEAGE.csv') if s['membership_branch']=='0']
        count=np.zeros(nx*ny,dtype=np.int64);cache={};events=[];outside=nonfree=total=0
        for s in schedule:
            frame=int(s['selected_frame'])
            if frame not in cache:cache[frame]=r.snapshot(bank/'bank'/('iteration_'+str(frame)))
            fil=cache[frame]['filaments'];xy=np.floor((fil[:,:2]-origin)/cell).astype(int)
            bounded=(xy[:,0]>=0)&(xy[:,0]<nx)&(xy[:,1]>=0)&(xy[:,1]<ny)
            index=xy[bounded,0]+xy[bounded,1]*nx
            unique=np.unique(index);count[unique]+=1
            total+=len(fil);outside+=int((~bounded).sum());nonfree+=int((~free[index]).sum())
        allraw=(count/50).astype(np.float32);masked=allraw.copy();masked[~free]=0
        fields[bank.name]=dict(ALL_XY=allraw,MASKED=masked)
        bankrows.append(dict(bank_id=bank.name,snapshots=50,unique_frames=len(cache),particle_snapshot_occurrences=total,
                            outside_2D_bounds_occurrences=outside,projected_nonfree_occurrences=nonfree,projected_nonfree_fraction=nonfree/total))
    resultrows=[];fieldout=[]
    for variant in ['MASKED','ALL_XY']:
        for cid in ['C7','K2']:
            raw=np.mean([fields[cid+'_0'][variant],fields[cid+'_1'][variant]],axis=0).astype(np.float32)
            blurred=blur(raw)
            for stage,arr in [('UNBLURRED',raw),('NATIVE_STYLE_BLURRED',blurred)]:
                log=score(arr);resultrows.append(dict(candidate_id=cid,variant=variant,stage=stage,native_style_log_similarity=log,native_style_similarity=math.exp(log)))
                for i in range(nx*ny):fieldout.append(dict(candidate_id=cid,variant=variant,stage=stage,cell_index=i,free=int(free[i]),frequency=float(arr[i])))
    pairs=[]
    for variant in ['MASKED','ALL_XY']:
        for stage in ['UNBLURRED','NATIVE_STYLE_BLURRED']:
            pair=[r for r in resultrows if r['variant']==variant and r['stage']==stage]
            assert [r['candidate_id'] for r in pair]==['C7','K2'];margin=pair[0]['native_style_log_similarity']-pair[1]['native_style_log_similarity']
            pairs.append(dict(variant=variant,stage=stage,C7_minus_K2_log_similarity=margin,selected='C7' if margin>1e-12 else 'K2' if margin<-1e-12 else 'TIE'))
    return dict(verdict='COMMON_CENTRE_FIELD_NATIVE_STYLE_COMPARISON_COMPLETED',new_forward_calls=0,new_GADEN_realizations=0,
      primary_variant='MASKED/NATIVE_STYLE_BLURRED',pairs=pairs,blur_anchors=anchor,
      comparability_limits=['Source points and grid/centre definition agree; physical generator, injection rate, record times and trajectories differ.',
        'This tests the score under common observable definition; no physical likelihood or official localization improvement is claimed.',
        'Python cv2 backend is anchored against native maps at tolerance2e-7; scalar source preference margins are reported.']),resultrows,fieldout,bankrows
if __name__=='__main__':
    D.mkdir(exist_ok=False)
    c=dict(pre_result_definition='3D centres projected onto exact native0.25m XY grid; every frozen50time occupiescell at leastone centre; two source-reference means; same nativeD=.4/logOdds/conf scoring.',
           primary='mask nonfree cells before same anchorednative1.5 Gaussian blur',secondary='retain all projected XY centres before blur to expose geometry support difference',
           new_simulation_or_seed=0,not_PID_conversion=True,readout_only=True)
    p=D/'CENTER_FIELD_FROZEN_CONTRACT.json';p.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8');(D/'CENTER_FIELD_PRE_SHA256.txt').write_text(sha(p),encoding='ascii')
    result,*tables=analyse(M1,M2,O)
    for name,t in zip(['CENTER_FIELD_SOURCE_SCORES.csv','CENTER_FIELD_PER_CELL.csv','PROJECTED_GEOMETRY_OCCURRENCES.csv'],tables):writecsv(D/name,t)
    (D/'CENTER_FIELD_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
