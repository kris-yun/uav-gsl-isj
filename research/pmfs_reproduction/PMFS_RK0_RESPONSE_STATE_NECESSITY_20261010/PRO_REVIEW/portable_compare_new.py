"""New, explicit portable comparisons; never edits/bypasses a frozen validator.

Main numeric tolerance remains rtol2e-12/atol3e-13. Histogram bin membership
is verified by exact integer keys/counts; label arithmetic is separately checked
against explicit float64 and float32 expression families. OpenCV versions are
reported as metadata, while native-map anchors establish numeric admission.
"""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np,cv2
RTOL=2e-12;ATOL=3e-13;MAP_ATOL=2e-7
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
INT_COLUMNS={'cell_index','grid_i','grid_j','native_free','state_records','fineCFD_XY_index','fine_i','fine_j','C7_state_records','K2_state_records','z_voxel','frame','filament_state_records','physical_nonfree_centres','projected_outside_2D','projected_inbounds_nonfree_2D','outside_strict_declared_world_AABB','below_declared_minimum_any_axis','in_critical_y_band'}
def same_number(x,y):return math.isclose(float(x),float(y),rel_tol=RTOL,abs_tol=ATOL)
def table(old,new,geometry=None):
    aa=rows(old);bb=rows(new);assert len(aa)==len(bb)
    maxabs=0.;labels=integers=numeric=0
    for i,(a,b) in enumerate(zip(aa,bb)):
        assert a.keys()==b.keys(),(old.name,i,'columns')
        for k in a:
            if k in INT_COLUMNS:
                assert int(a[k])==int(b[k]) and float(a[k])==int(a[k]) and float(b[k])==int(b[k]),(old.name,i,k)
                integers+=1
            elif geometry and k in ['z_min','z_max']:
                kz=int(a['z_voxel'])+(k=='z_max');origin,cell=geometry
                canonical64=float(origin)+int(kz)*float(cell)
                canonical32=float(np.float32(origin+np.float32(kz)*cell))
                assert any(same_number(a[k],v) for v in [canonical64,canonical32]),(old.name,i,k,'stored invalid label')
                assert any(same_number(b[k],v) for v in [canonical64,canonical32]),(old.name,i,k,'recomputed invalid label')
                # Labels may differ without bin membership changing. No blanket
                # larger tolerance is applied to physical numerical results.
                maxabs=max(maxabs,abs(float(a[k])-float(b[k])));labels+=1
            else:
                try:
                    x,y=float(a[k]),float(b[k]);assert same_number(x,y),(old.name,i,k,x,y)
                    maxabs=max(maxabs,abs(x-y));numeric+=1
                except ValueError:assert a[k]==b[k],(old.name,i,k)
    return dict(file=old.name,rows=len(aa),exact_integer_comparisons=integers,main_numeric_comparisons=numeric,derived_label_comparisons=labels,maximum_absolute_difference=maxabs)
def run(root,recomputed,out):
    m3=root/'M3_NEW';m2=root/'M2_FROZEN';m1=m3/'M1_REFERENCE'
    stored=m3/'forward_contract_audit';occ=m2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv'
    lines=occ.read_text().splitlines();origin=np.float32(float(lines[0].split()[3]));cell=np.float32(float(lines[3].split()[1]));geometry=(origin,cell)
    out.mkdir(parents=True,exist_ok=True);tabs=[]
    for p in sorted(recomputed.glob('*.csv')):tabs.append(table(stored/p.name,p,geometry if p.name=='FILAMENT_HEIGHT_HISTOGRAM.csv' else None))
    # Emulate only NumPy2 weak-scalar label promotion. Integer memberships,
    # fractions and state counts are copied intact, clearly marked emulation.
    hh=rows(stored/'FILAMENT_HEIGHT_HISTOGRAM.csv');maxdiff=0.;different=0
    for r in hh:
        for k,offset in [('z_min',0),('z_max',1)]:
            v=float(np.float32(origin+np.float32(int(r['z_voxel'])+offset)*cell))
            diff=abs(v-float(r[k]));different+=diff!=0;maxdiff=max(maxdiff,diff);r[k]=repr(v)
    em=out/'NUMPY2_LABEL_ARITHMETIC_EMULATION_ONLY.csv'
    with em.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(hh[0]));w.writeheader();w.writerows(hh)
    emcheck=table(stored/'FILAMENT_HEIGHT_HISTOGRAM.csv',em,geometry)
    inp=rows(m1/'snapshot/input.csv');free=np.array([int(r['occupancy'])==1 for r in inp]);shape=(45,34);mask=free.astype(np.float32).reshape(shape)
    observed=np.array([1-1/(1+math.exp(float(r['logOdds']))) for r in inp]);conf=np.array([float(r['confidence']) for r in inp]);assert (conf>=0).all() and (conf<=1).all()
    gb=lambda a:cv2.GaussianBlur(np.asarray(a,dtype=np.float32).reshape(shape),(0,0),1.5,1.5)
    den=gb(mask);anchors=[]
    for job in ['T_true_fine','T_wrong_fine','W_true_fine','anchor_W_fine']:
        d=m1/'evidence/forwards'/job/'maps';pre=next(d.glob('*_unblurred.f32'));post=next(p for p in d.glob('*.f32') if '_unblurred' not in p.name)
        raw=np.fromfile(pre,dtype='<f4');native=np.fromfile(post,dtype='<f4');num=gb(raw)
        got=np.clip(np.divide(num,den,out=num.copy(),where=den!=0),0,1).ravel();err=abs(got-native);assert err.max()<=MAP_ATOL
        weight=.4*conf/(1-.4*conf)
        def logscore(a):return math.fsum(math.log1p(-.4*float(conf[i])*abs(float(observed[i])-float(a[i]))) for i in np.flatnonzero(free))
        logdiff=abs(logscore(got)-logscore(native));bound=math.fsum(float(weight[i])*float(err[i]) for i in np.flatnonzero(free))
        assert logdiff<=bound+ATOL
        anchors.append(dict(job=job,native_map_SHA256=sha(post),maximum_absolute_field_difference=float(err.max()),actual_absolute_log_score_difference=logdiff,derived_Lipschitz_log_score_bound=bound))
    manifest=json.loads((root/'SHA256_MANIFEST.json').read_text());assert all(sha(root/n)==h for n,h in manifest.items())
    proenv=json.loads((out.parent/'handoff/ENVIRONMENT.json').read_text())
    result=dict(verdict='PASS_MAIN_VALUES_INTEGER_BIN_MEMBERSHIPS_AND_EXPLICIT_LABEL_TYPE_FAMILIES',old_verifiers_modified=False,
      old_validator_claim='Frozen validators remain byte-identical. This new checker does not relabel an original version/byte-comparison failure as original-validator PASS.',
      immutable_combined_SHA_members=len(manifest),environment=dict(local_opencv=cv2.__version__,PRO_opencv=proenv['opencv'],opencv_version_literal_equal=cv2.__version__==proenv['opencv'],local_numpy=np.__version__,PRO_numpy=proenv['numpy']),
      main_numeric_tolerance=dict(relative=RTOL,absolute=ATOL),derived_histogram_rule='Exact group/scope/z_voxel/state_records; exact physical count/fraction rule. Labels must match explicit float64 or float32 formulas at original numeric tolerance.',
      recomputed_tables=tabs,numpy2_label_emulation=dict(status='PASS_EXPLICIT_FLOAT32_ARITHMETIC_FAMILY_NOT_NEW_RAW_STATE_RECOMPUTATION',different_labels=different,maximum_label_difference_m=maxdiff,integer_membership_and_counts_unchanged=True,comparison=emcheck),
      native_blur_anchor_field_tolerance=MAP_ATOL,native_blur_anchors=anchors,
      score_tolerance_proposal='For an admitted per-cell map difference e_i, |delta logscore| <= sum_i (D*c_i/(1-D*c_i))*e_i, D=.4. Report actual maps/bound; source-margin sign is robust only beyond the sum of the two source bounds. Do not enlarge every table tolerance or hide version mismatch.',new_forwards=0,new_gas=0,new_ROS=0)
    (out/'PORTABLE_COMPARISON_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--combined-root',type=Path,required=True);p.add_argument('--recomputed',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.combined_root,a.recomputed,a.out),indent=2))
