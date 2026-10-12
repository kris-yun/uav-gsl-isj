"""Single registered repair: nested closed-OOB projection of the saved public basis.

Only old public geometry, face modes, mask and the frozen amendment are read.
No old conditioned wind path, plant source, CFD or gas is read.
"""
from pathlib import Path
import os, json, hashlib, time, resource, traceback, shutil
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import cg
from scipy.sparse.csgraph import connected_components

ROOT=Path(__file__).resolve().parent
OLD=Path('/mnt/hgfs/workspace/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011')
START=time.monotonic()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):(ROOT/name).write_text(json.dumps(obj,indent=2)+'\n')
def gate():
 if time.monotonic()-START >= 570: raise RuntimeError('PRE_FORWARD_COMPUTE_CAP_STOP')
 if shutil.disk_usage(ROOT).free < 4*1024**3:raise RuntimeError('DISK_RESERVE_STOP')
 if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()) > 800*1024**2:raise RuntimeError('CANDIDATE_DISK_GUARD_STOP')

def main():
 c=json.loads((ROOT/'REPAIR3_FROZEN_CONTRACT.json').read_text())
 assert sha(ROOT/'REPAIR3_FROZEN_CONTRACT.json')==(ROOT/'REPAIR3_FROZEN_CONTRACT.sha256').read_text().strip()
 assert c['counter']['this_repair']==3
 oldc=json.loads((OLD/'L1_PROSPECTIVE_MODEL_CONTRACT_REV1.json').read_text())
 assert sha(OLD/'L1_PROSPECTIVE_MODEL_CONTRACT_REV1.json')==c['base_contract_sha256']
 g=json.loads((OLD/'L1_GEOMETRY_META.json').read_text())
 nx,ny,nz=g['dims']; h=g['h']; lo=np.array(g['min']); hi=np.array(g['max']); dims=np.array([nx,ny,nz])
 states=np.fromfile(OLD/'geometry_states.u8',dtype=np.uint8)
 assert hashlib.sha256(states.tobytes()).hexdigest()==g['statesSHA']
 free=np.flatnonzero(states==0); N=len(free)
 node=np.fromfile(OLD/'free_node_index.i32',dtype='<i4')
 assert len(free)==g['Nfree'] and np.array_equal(node[free],np.arange(N))
 xyz=np.column_stack([free%nx,free//nx%ny,free//(nx*ny)])
 world=lo+h*(xyz+.5)
 mask=np.array([int(x) for x in (OLD/'native_mask.txt').read_text().split()]); ids=np.flatnonzero(mask)
 assert len(ids)==447 and sha(OLD/'native_mask.txt')==oldc['support']['mask_sha256']
 noheight=[]
 for idx in ids:
  i,j=divmod(int(idx),45); xy=np.array([-7.55+(i+.5)*.25,-7.88+(j+.5)*.25]); ix,iy=np.floor((xy-lo[:2])/h).astype(int)
  heights=[k for k in range(nz) if 0<=ix<nx and 0<=iy<ny and states[k*nx*ny+iy*nx+ix]==0]
  if not heights:noheight.append(int(idx))
 assert not noheight
 dump('STATIC_PUBLIC_INPUT_GATE.json',{'PASS':True,'native447':447,'no_free_height':noheight,'states_counts':{str(k):int(np.sum(states==k)) for k in (0,1,2)},'source_label_read':False,'CFD_read':False,'old_conditioned_paths_read':False,'input_hashes':{n:sha(OLD/n) for n in ('geometry_states.u8','free_node_index.i32','flow_faces.f32','OccupancyGrid3D.csv','native_mask.txt','C1B_PAST_LOCAL_WIND.csv')}})
 # S_new is S_old intersected with every OOB edge fixed to zero; no cell is relabelled.
 # Represent only free/free and original free/Outlet edges in the reduced matrix.
 arrays=[[] for _ in range(6)]
 def append(a,b,d,sign,ss,es):
  vals=(a,b,np.full(len(a),d),np.full(len(a),sign),np.full(len(a),ss),np.full(len(a),es))
  for parts,v in zip(arrays,vals):parts.append(v)
 steps=[1,nx,nx*ny]
 for d in range(3):
  inside=xyz[:,d]<dims[d]-1; orig=np.flatnonzero(inside); ncells=free[inside]+steps[d]; kinds=states[ncells]
  ff=kinds==0;append(orig[ff],node[ncells[ff]],d,1,2*d+1,2*d)
  out=kinds==2;append(orig[out],np.full(np.sum(out),-1),d,1,2*d+1,-1)
  neg=np.flatnonzero(xyz[:,d]>0); out=states[free[neg]-steps[d]]==2
  append(neg[out],np.full(np.sum(out),-1),d,-1,2*d,-1)
 a,b,axis,sign,ss,es=[np.concatenate(x).astype(np.int32) for x in arrays]
 E=len(a);inter=b>=0;edge=np.arange(E)
 D=sparse.csr_matrix((np.r_[np.ones(E),-np.ones(np.sum(inter))],(np.r_[a,b[inter]],np.r_[edge,edge[inter]])),shape=(N,E))
 L=(D@D.T).tocsr()
 adj=sparse.csr_matrix((np.ones(2*np.sum(inter)),(np.r_[a[inter],b[inter]],np.r_[b[inter],a[inter]])),shape=(N,N))
 nc,labels=connected_components(adj,directed=False);opencomp=set(labels[a[~inter]])
 pins=[int(np.flatnonzero(labels==comp)[0]) for comp in range(nc) if comp not in opencomp]
 if pins:L=L+sparse.csr_matrix((np.ones(len(pins)),(pins,pins)),shape=(N,N))
 M=sparse.diags(1/L.diagonal())
 edgepos=world[a].copy();edgepos[np.arange(E),axis]+=sign*h*.5
 B=np.memmap(OLD/'flow_faces.f32',dtype='<f4',mode='r',shape=(24,N,6))
 target=np.memmap(ROOT/'flow_faces.f32',dtype='<f4',mode='w+',shape=(24,N,6));target[:]=0
 rng=np.random.default_rng(oldc['RNG']['basis_seed'])
 waves=[None,(1,1,1),(2,1,1),(1,2,1),(1,1,2),(2,2,1),(2,1,2),(1,2,2)]
 rows=[]
 def project(v):
  rhs=D@v; count=[0]
  def callback(x):
   count[0]+=1
   if count[0]%10==0:gate()
  sol,info=cg(L,rhs,M=M,rtol=1e-10,atol=1e-11,maxiter=4000,callback=callback)
  residual=float(np.linalg.norm(L@sol-rhs)/max(np.linalg.norm(rhs),1e-20))
  if info or residual>1e-7:raise RuntimeError(f'CG_PROJECTION_RESIDUAL_STOP:{info}:{residual}')
  return v-D.T@sol,residual,count[0]
 def faces(v):
  f=np.zeros((N,6));f[a,ss]=sign*v;f[b[inter],es[inter]]=v[inter];return f
 def rms(f):return float(np.sqrt(np.mean(np.sum(((f[:,::2]+f[:,1::2])*.5)**2,axis=1))))
 for mode in range(24):
  gate();mt=time.monotonic();group,d=divmod(mode,3)
  raw=np.zeros(E);pick=axis==d
  if group==0:raw[pick]=sign[pick]
  else:
   phase=rng.uniform(0,2*np.pi);s=((edgepos-lo)/(hi-lo))@np.array(waves[group]);raw[pick]=np.cos(2*np.pi*s[pick]+phase)*sign[pick]
  direct,r1,it1=project(raw);fd=faces(direct);rd=rms(fd)
  row={'mode':mode,'raw_corrected_RMS':rd,'raw_projection_relative_residual':r1,'raw_CG_iterations':it1}
  if rd<1e-8:
   row['FAIL']='REGISTERED_RAW_MODE_DEGENERATE_NO_REPLACEMENT';rows.append(row);dump('BOUNDARY_MODE_PROGRESS.json',rows)
   raise RuntimeError(f'PRIOR_MODE_DEGENERATE_STOP:{mode}:RMS={rd}')
  # P_new P_old = P_new in the common original edge-L2 metric.
  # Old normalization is positive scalar per mode, so final RMS removes it.
  oldv=sign*np.asarray(B[mode,a,ss],dtype=np.float64)
  reused,r2,it2=project(oldv);fr=faces(reused);rr=rms(fr)
  if rr<1e-8:raise RuntimeError(f'REUSED_MODE_DEGENERATE_STOP:{mode}')
  fd/=rd;fr/=rr
  nested=float(np.linalg.norm(fr-fd)/np.linalg.norm(fd))
  row.update({'reused_projection_relative_residual':r2,'reused_CG_iterations':it2,'nested_normalized_relative_difference':nested,'reused_RMS_before_normalization':rr})
  if nested>2e-5:raise RuntimeError(f'NESTED_PROJECTION_FAIL:{mode}:{nested}')
  div=float(np.max(np.abs(np.sum(fr[:,1::2]-fr[:,::2],axis=1)/h)))
  if div>1e-5:raise RuntimeError(f'NORMALIZED_DIVERGENCE_FAIL:{mode}:{div}')
  target[mode]=fr.astype('<f4');target.flush()
  saved=np.asarray(target[mode],dtype=np.float64)
  div32=float(np.max(np.abs(np.sum(saved[:,1::2]-saved[:,::2],axis=1)/h)))
  # Every closed face must be an exact stored zero, not merely small in total.
  closed_max=0.;closed_count=0;continuity=0.
  for d in range(3):
   for side in (0,1):
    lim=0 if side==0 else dims[d]-1;atboundary=xyz[:,d]==lim
    rest=np.flatnonzero(~atboundary);delta=-steps[d] if side==0 else steps[d]
    obst=rest[states[free[rest]+delta]==1]
    closed=np.r_[np.flatnonzero(atboundary),obst]
    closed_count+=len(closed)
    if len(closed):closed_max=max(closed_max,float(np.max(np.abs(saved[closed,2*d+side]))))
  continuity=float(np.max(np.abs(saved[a[inter],ss[inter]]-saved[b[inter],es[inter]])))
  row.update({'saved_float32_maxdiv_per_s':div32,'closed_face_normal_max':closed_max,'closed_faces':closed_count,'internal_face_continuity_max':continuity,'mode_wall_s':time.monotonic()-mt})
  rows.append(row);dump('BOUNDARY_MODE_PROGRESS.json',rows)
  print(json.dumps(row),flush=True)
  if div32>1e-5 or closed_max!=0. or continuity!=0.:raise RuntimeError('STORED_BOUNDARY_DIVERGENCE_CONTINUITY_FAIL')
 node.astype('<i4').tofile(ROOT/'free_node_index.i32')
 receptor=np.array([-.9,.15,-.2]);ix=np.floor((receptor-lo)/h).astype(int);rn=int(node[ix[0]+nx*ix[1]+nx*ny*ix[2]])
 frac=(receptor-(lo+ix*h))/h
 H=np.stack([(1-frac[d])*target[:,rn,2*d]+frac[d]*target[:,rn,2*d+1] for d in (0,1)])
 if np.linalg.matrix_rank(H)!=2:raise RuntimeError('LOCAL_OBSERVATION_RANK_FAIL')
 np.save(ROOT/'CORRECTED_H.npy',H)
 for name in ('OccupancyGrid3D.csv','geometry_states.u8','L1_GEOMETRY_META.json','native_mask.txt','C1B_PAST_LOCAL_WIND.csv'):
  shutil.copy2(OLD/name,ROOT/name)
 dump('BOUNDARY_QUALIFICATION.json',{'PASS':True,'mode_count':24,'closed_normal_flux_exact_zero':True,'nested_proof':'S_new subset S_old under same original oriented edge metric implies orthogonal P_new P_old=P_new; normalized comparison tests each original raw mode','modes':rows,'all447_static_support_pass':True,'H_rank':2,'outlet_cells_unchanged':int(np.sum(states==2)),'old_conditioned_paths_used':False,'wind_reference_calls':0,'gas_calls':0,'native_goals':0,'geometry':g,'flow_faces_sha256':sha(ROOT/'flow_faces.f32')})

if __name__=='__main__':
 status='FAIL';error=None
 try:main();status='PASS'
 except Exception as e:
  error=str(e);traceback.print_exc()
 finally:
  dump('BOUNDARY_COMPUTE_RECEIPT.json',{'status':status,'error':error,'active_wall_s':time.monotonic()-START,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'gas_calls':0,'native_goals':0,'cumulative_repair':3})
 if status!='PASS':raise SystemExit(2)
