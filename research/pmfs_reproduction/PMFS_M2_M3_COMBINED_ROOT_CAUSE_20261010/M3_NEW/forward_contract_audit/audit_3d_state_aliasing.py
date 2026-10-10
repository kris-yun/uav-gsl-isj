"""Read-only descriptive audit of 392 frozen 3D states; no integration/query/forward.

Filaments repeated in snapshots are pooled *state records*, not independent
trajectories. Height-conditioned wind comparisons retain each actual fine-CFD
XY voxel, thereby separating vertical aliasing from 2D horizontal coarsening.
"""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,struct
from pathlib import Path
import numpy as np
SCRIPT_DIR=Path(__file__).resolve().parent;ROOT=SCRIPT_DIR.parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--m1',type=Path,default=ROOT/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010')
p.add_argument('--m2',type=Path,default=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010')
p.add_argument('--out',type=Path,default=SCRIPT_DIR)
args=p.parse_args();M1=args.m1;M2=args.m2;WORK=args.out
WORK.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(SCRIPT_DIR/'source'))
from verify_raw_receiver_queries import occupancy,snapshot
F=np.float32
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def writecsv(path,rs):
    if not rs:return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def stats(a):
    a=np.asarray(a,dtype=np.float64)
    if not len(a):return {'count':0}
    q=np.quantile(a,[0,.05,.25,.5,.75,.95,1])
    return dict(count=len(a),mean=float(a.mean()),std=float(a.std()),minimum=float(q[0]),p05=float(q[1]),q25=float(q[2]),median=float(q[3]),q75=float(q[4]),p95=float(q[5]),maximum=float(q[6]))
occ=occupancy(M2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv')
windpath=M2/'frozen_B4_inputs/derived_B4/wind/wind_iteration_10'
raw=windpath.read_bytes();assert struct.unpack_from('<ii',raw)==(3,0)
wind=np.frombuffer(raw,dtype='<f4',offset=8).reshape(int(np.prod(occ['dimensions'])),3)
pmfsrows=rows(M1/'snapshot/input.csv');free=np.array([int(r['occupancy'])==1 for r in pmfsrows])
nativewind=np.array([[float(r['u']),float(r['v'])] for r in pmfsrows])
meta=json.loads((M1/'snapshot/metadata.json').read_text());assert meta['width']==34 and meta['height']==45
dx,dy,dz=map(int,occ['dimensions']);sensor_k=int(np.trunc((F(-.2)-occ['minimum'][2])/occ['cell_size']))
source_k=int(np.trunc((F(-.5)-occ['minimum'][2])/occ['cell_size']))
allstates=[];frameinfo=[]
for b in sorted((M2/'native_reference_evidence/realizations').iterdir()):
    if not b.is_dir():continue
    manifest={int(r['frame']):r for r in rows(b/'ALL_FRAME_SHA256_AND_TIME.csv')}
    for path in sorted((b/'bank').glob('iteration_*'),key=lambda p:int(p.name.split('_')[-1])):
        fr=int(path.name.split('_')[-1]);assert sha(path)==manifest[fr]['SHA256']
        d=snapshot(path);assert d['wind_index']==10
        p=d['filaments'][:,:3];n=len(p)
        ijk=np.trunc((p-occ['minimum'])/occ['cell_size']).astype(np.int64)
        in3d=np.all((ijk>=0)&(ijk<occ['dimensions']),axis=1)
        assert in3d.all(),f'out-of-3D-bound centres in {b.name}/{path.name}'
        idx=ijk[:,0]+ijk[:,1]*dx+ijk[:,2]*dx*dy
        physical=occ['data'][ijk[:,2],ijk[:,0],ijk[:,1]]
        actual=wind[idx].astype(np.float64)
        at_sensor=wind[ijk[:,0]+ijk[:,1]*dx+sensor_k*dx*dy].astype(np.float64)
        at_source=wind[ijk[:,0]+ijk[:,1]*dx+source_k*dx*dy].astype(np.float64)
        # Grid2D uses float vectors/metadata. Native integer conversion truncates.
        grid=np.trunc((p[:,:2]-np.array([F(meta['origin_x']),F(meta['origin_y'])]))/F(meta['cell_size'])).astype(np.int64)
        ingrid=(grid[:,0]>=0)&(grid[:,0]<34)&(grid[:,1]>=0)&(grid[:,1]<45)
        ci=grid[:,0]+grid[:,1]*34
        projected_free=np.zeros(n,dtype=bool);projected_free[ingrid]=free[ci[ingrid]]
        native=np.full((n,2),np.nan);native[ingrid]=nativewind[ci[ingrid]]
        # cols x,y,z,sigma,cell,ingrid,free3d,free2d,u,v,w,u_sensor,v_sensor,w_sensor,u_source,v_source,w_source,u_native,v_native
        a=np.column_stack([d['filaments'],ci,ingrid,physical==0,projected_free,actual,at_sensor,at_source,native])
        allstates.append((b.name,a))
        frameinfo.append(dict(bank=b.name,frame=fr,physical_time_s=float(manifest[fr]['physical_snapshot_time_s']),filament_state_records=n,
                              physical_nonfree_centres=int((physical!=0).sum()),projected_outside_2D=int((~ingrid).sum()),
                              projected_inbounds_nonfree_2D=int((ingrid&~projected_free).sum()),
                              outside_strict_declared_world_AABB=int((np.any((p<occ['minimum'])|(p>occ['maximum']),axis=1)).sum()),
                              below_declared_minimum_any_axis=int((np.any(p<occ['minimum'],axis=1)).sum()),SHA256=sha(path)))
assert len(frameinfo)==392
writecsv(WORK/'THREED_SNAPSHOT_PROJECTION_COUNTS.csv',frameinfo)
bybank={name:np.concatenate([a for name2,a in allstates if name2==name]) for name in sorted({name for name,a in allstates})}
bysource={s:np.concatenate([a for name,a in allstates if name.startswith(s+'_')]) for s in ['C7','K2']}
summary=[];hist=[];cellsummary=[];arrays={**bybank,**bysource,'ALL':np.concatenate(list(bysource.values()))}
for name,a in arrays.items():
    for label,mask in [('all',np.ones(len(a),bool)),('critical_y_1_7_2_7',(a[:,1]>=1.7)&(a[:,1]<=2.7)),('native_free_2D',a[:,7]==1),('critical_y_and_native_free',(a[:,1]>=1.7)&(a[:,1]<=2.7)&(a[:,7]==1))]:
        v=a[mask];uv=v[:,8:10];ref=v[:,11:13];src=v[:,14:16]
        err=np.linalg.norm(uv-ref,axis=1);errsrc=np.linalg.norm(uv-src,axis=1);speed=np.linalg.norm(uv,axis=1);refspeed=np.linalg.norm(ref,axis=1)
        strong=(speed>1e-6)&(refspeed>1e-6)
        cosine=(np.sum(uv[strong]*ref[strong],axis=1)/(speed[strong]*refspeed[strong]))
        summary.append(dict(group=name,scope=label,state_records=len(v),heights=stats(v[:,2]),
          sensor_plane_separation_abs_m=stats(abs(v[:,2]+.2)),vertical_w_m_s=stats(v[:,10]),
          actual_vs_same_fineXY_sensor_height_horizontal_error_m_s=stats(err),actual_vs_same_fineXY_source_height_horizontal_error_m_s=stats(errsrc),
          actual_horizontal_speed_m_s=stats(speed),horizontal_error_relative_to_actual_speed=stats(err/np.maximum(speed,1e-6)),
          horizontal_sensor_direction_difference_deg=stats(np.degrees(np.arccos(np.clip(cosine,-1,1)))),
          actual_sensor_opposite_horizontal_halfplane_count=int((cosine<0).sum()),actual_sensor_direction_comparable_count=int(strong.sum()),
          actual_vs_native_2D_field_horizontal_error_m_s=stats(np.linalg.norm(uv[v[:,5]==1]-v[v[:,5]==1,17:19],axis=1)),
          projected_outside_native_2D=int((v[:,5]==0).sum()),projected_inside_nonfree_native_2D=int(((v[:,5]==1)&(v[:,7]==0)).sum()),
          physical_nonfree_3D_centres=int((v[:,6]==0).sum())))
        zvox=np.trunc((v[:,2]-occ['minimum'][2])/occ['cell_size']).astype(int)
        c=np.bincount(zvox,minlength=dz)
        for k,count in enumerate(c):
            hist.append(dict(group=name,scope=label,z_voxel=k,z_min=float(occ['minimum'][2]+k*occ['cell_size']),z_max=float(occ['minimum'][2]+(k+1)*occ['cell_size']),state_records=int(count),fraction=float(count/max(len(v),1))))
    for ci in range(1530):
        v=a[(a[:,5]==1)&(a[:,4]==ci)]
        if not len(v):continue
        z=v[:,2];winderror=np.linalg.norm(v[:,8:10]-v[:,11:13],axis=1)
        cellsummary.append(dict(group=name,cell_index=ci,grid_i=ci%34,grid_j=ci//34,native_free=int(free[ci]),
          x_center=float(F(meta['origin_x'])+F(ci%34+.5)*F(.25)),y_center=float(F(meta['origin_y'])+F(ci//34+.5)*F(.25)),
          state_records=len(v),z_mean=float(z.mean()),z_std=float(z.std()),z_p05=float(np.quantile(z,.05)),z_median=float(np.median(z)),z_p95=float(np.quantile(z,.95)),
          actual_u_mean=float(v[:,8].mean()),actual_v_mean=float(v[:,9].mean()),actual_w_mean=float(v[:,10].mean()),
          fineXY_sensor_height_u_mean=float(v[:,11].mean()),fineXY_sensor_height_v_mean=float(v[:,12].mean()),
          height_horizontal_wind_error_mean=float(winderror.mean()),height_horizontal_wind_error_median=float(np.median(winderror))))
writecsv(WORK/'FILAMENT_HEIGHT_HISTOGRAM.csv',hist);writecsv(WORK/'CELL_CONDITIONAL_HEIGHT_AND_WIND.csv',cellsummary)
# Source-conditioned z distributions in identical nativeXY cells: no performance
# selection and no claim of independent particle counts. Every eligible cell is retained.
comparisons=[]
for ci in range(1530):
    distributions=[];vs=[]
    for s in ['C7','K2']:
        v=bysource[s][(bysource[s][:,5]==1)&(bysource[s][:,4]==ci)];vs.append(v)
        zvox=np.trunc((v[:,2]-occ['minimum'][2])/occ['cell_size']).astype(int)
        c=np.bincount(zvox,minlength=dz).astype(float);distributions.append(c/max(len(v),1))
    if min(map(len,vs))<20:continue
    p,q=distributions;m=(p+q)/2
    def kl(p,m):
        mask=p>0;return float(np.sum(p[mask]*np.log2(p[mask]/m[mask])))
    y=float(F(meta['origin_y'])+F(ci//34+.5)*F(.25));js=(kl(p,m)+kl(q,m))/2
    comparisons.append(dict(cell_index=ci,native_free=int(free[ci]),y_center=y,in_critical_y_band=int(1.7<=y<=2.7),
      C7_state_records=len(vs[0]),K2_state_records=len(vs[1]),C7_z_mean=float(vs[0][:,2].mean()),K2_z_mean=float(vs[1][:,2].mean()),
      absolute_z_mean_difference_m=float(abs(vs[0][:,2].mean()-vs[1][:,2].mean())),height_distribution_JS_bits=js,
      height_distribution_total_variation=float(np.abs(p-q).sum()/2)))
writecsv(WORK/'SAME_XY_SOURCE_CONDITIONAL_HEIGHT_DISTRIBUTION.csv',comparisons)
# Same *fine 0.1m CFD XY voxel* conditional distributions, not merely sharing a
# 0.25m native cell. This removes fine-XY wind sampling from the height contrast.
fine_records=[];selected={};fineids={}
for s,a in bysource.items():
    a=a[(a[:,1]>=1.7)&(a[:,1]<=2.7)&(a[:,7]==1)]
    xy=np.trunc((a[:,:2]-occ['minimum'][:2])/occ['cell_size']).astype(int)
    selected[s]=a;fineids[s]=xy[:,0]+xy[:,1]*dx
for fci in sorted(set(fineids['C7']).intersection(set(fineids['K2']))):
    vv=[selected[s][fineids[s]==fci] for s in ['C7','K2']]
    if min(map(len,vv))<20:continue
    h=[]
    for v in vv:
        kz=np.trunc((v[:,2]-occ['minimum'][2])/occ['cell_size']).astype(int)
        h.append(np.bincount(kz,minlength=dz)/len(v))
    p,q=h;m=(p+q)/2
    row=dict(fineCFD_XY_index=int(fci),fine_i=int(fci%dx),fine_j=int(fci//dx),
      C7_state_records=len(vv[0]),K2_state_records=len(vv[1]),
      C7_z_mean=float(vv[0][:,2].mean()),K2_z_mean=float(vv[1][:,2].mean()),
      absolute_z_mean_difference_m=float(abs(vv[0][:,2].mean()-vv[1][:,2].mean())),
      height_distribution_JS_bits=(kl(p,m)+kl(q,m))/2,
      height_distribution_total_variation=float(abs(p-q).sum()/2),
      C7_actual_u_mean=float(vv[0][:,8].mean()),C7_actual_v_mean=float(vv[0][:,9].mean()),
      K2_actual_u_mean=float(vv[1][:,8].mean()),K2_actual_v_mean=float(vv[1][:,9].mean()),
      source_conditioned_mean_horizontal_wind_difference_m_s=float(np.linalg.norm(vv[0][:,8:10].mean(axis=0)-vv[1][:,8:10].mean(axis=0))))
    fine_records.append(row)
writecsv(WORK/'SAME_FINE_CFD_XY_SOURCE_CONDITIONAL_HEIGHT.csv',fine_records)
result=dict(verdict='DESCRIPTIVE_3D_STATE_ALIASING_CONFIRMED_NOT_CAUSAL_ATTRIBUTION',new_forwards=0,new_gas=0,new_ROS=0,
  snapshot_count=len(frameinfo),pooled_filament_state_records=sum(r['filament_state_records'] for r in frameinfo),
  states_are_correlated_snapshots_not_independent_sample_size=True,snapshot_SHA256_passed=392,wind_SHA256=sha(windpath),
  compare_definition='At each actual filament XY fine-CFD voxel, compare current wind at its actual Z voxel versus sameXY fixed sensor-Z=-.2m; source-Z=-.5m also described. No dynamics are reintegrated.',
  summaries=summary,source_conditioned_same_cell_Z_distribution=dict(minimum_state_records_each_source=20,
    complete_eligible_cells=len(comparisons),native_free_cells=sum(r['native_free'] for r in comparisons),
    critical_band_native_free_cells=sum(r['native_free'] and r['in_critical_y_band'] for r in comparisons),
    all_native_free_JS_bits=stats([r['height_distribution_JS_bits'] for r in comparisons if r['native_free']]),
    critical_band_native_free_JS_bits=stats([r['height_distribution_JS_bits'] for r in comparisons if r['native_free'] and r['in_critical_y_band']]),
    critical_band_native_free_absolute_source_mean_Z_difference_m=stats([r['absolute_z_mean_difference_m'] for r in comparisons if r['native_free'] and r['in_critical_y_band']])),
  same_fine_CFD_XY_source_conditioning=dict(scope='critical_y_band_and_native_free_2D',minimum_state_records_each_source=20,complete_eligible_fineXY_voxels=len(fine_records),
    height_distribution_JS_bits=stats([r['height_distribution_JS_bits'] for r in fine_records]),
    absolute_source_mean_Z_difference_m=stats([r['absolute_z_mean_difference_m'] for r in fine_records]),
    source_conditioned_mean_horizontal_wind_difference_m_s=stats([r['source_conditioned_mean_horizontal_wind_difference_m_s'] for r in fine_records])),
  coordinate_predicate_note=dict(native_3D_cell_nonfree_centres=sum(r['physical_nonfree_centres'] for r in frameinfo),
    outside_strict_declared_world_AABB=sum(r['outside_strict_declared_world_AABB'] for r in frameinfo),
    below_declared_minimum_any_axis=sum(r['below_declared_minimum_any_axis'] for r in frameinfo),
    explanation='Native float coordinatesToIndices uses integer truncation and a rounded voxel extent. Native free-cell support is not identical to strict declared min/max AABB; these counts are preserved rather than silently changing the predicate.'),
  limits=['Frozen 49 snapshots per realization; frames and filaments are temporally correlated.','This is occupancy/count conditioned P(Z) for filament centres, not ppm-weighted receptor likelihood.','Velocity comparisons at saved states establish representational aliasing, not a proven cause of source ranking.','Wind10 is static during these observations; no time-varying wind hypothesis is established.'])
(WORK/'THREED_STATE_ALIASING_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='summaries'},ensure_ascii=False,indent=2))
