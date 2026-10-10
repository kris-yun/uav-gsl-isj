"""Read-only completed M1 audit; Python 3 + numpy. No VM, ROS, simulations or writes."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
import verify_m0_portable as portable

def js(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def verify(root):
    manifest=js(root/'SHA256_MANIFEST.json')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=root/'SHA256_MANIFEST.json'}
    assert actual==set(manifest),('unlisted or missing package members',actual^set(manifest))
    for name,digest in manifest.items():assert sha(root/name)==digest,name
    m0=root/'frozen_M0';result=portable.verify(m0)
    native=m0/'evidence/runtime/updates/update_2'
    meta=js(native/'metadata.json');data=rows(native/'input.csv');candidates=rows(native/'candidates.csv')
    n=len(data);width=meta['width'];free=np.array([r['occupancy']=='1' for r in data])
    assert int(free.sum())==447
    xy=np.column_stack([meta['origin_x']+(np.arange(n)%width+.5)*.25,
                        meta['origin_y']+(np.arange(n)//width+.5)*.25])
    probability=1.-1./(1.+np.exp([float(r['logOdds']) for r in data]))
    confidence=np.array([float(r['confidence']) for r in data])
    module=portable.load_m0(m0);_,stops=module.measure_events(m0/'evidence')
    direct=np.zeros(n,dtype=bool)
    for stop in stops:
        i,j=((np.array([stop['x'],stop['y']])-[meta['origin_x'],meta['origin_y']])/.25).astype(int)
        direct[i+j*width]=True
    assert direct.sum()==10 and free[direct].all()
    band=(xy[:,1]>=1.7)&(xy[:,1]<=2.7)
    masks=[free,free&~band,free&direct,free&~direct]
    saved=js(root/'M0_MASK_SENSITIVITY_RECOMPUTATION.json')['conditions']
    saved_p=rows(root/'M0_MASK_POSTERIOR_DIAGNOSTIC.csv')
    mask_checks=[]
    for mask,target in zip(masks,saved):
        # An alternate log-product computation checks the original direct-product recomputation.
        scores=np.zeros(n);pair={}
        for candidate in candidates:
            hit=np.frombuffer((native/candidate['map_file']).read_bytes(),dtype='<f4')
            factor=module.factors(probability,hit,confidence)
            assert np.all(np.isfinite(factor[mask])) and np.all(factor[mask]>0)
            score=math.exp(math.fsum(math.log(float(v)) for v in factor[mask]))
            scores[module.indices_for(candidate,width)]=score;pair[candidate['candidate_id']]=score
        posterior=np.where(free,scores/scores[free].sum(),0)
        mean=(xy*posterior[:,None]).sum(axis=0);index=int(posterior.argmax())
        metrics=dict(scoring_cells=int(mask.sum()),MAP_index=index,
                     wrong_over_true_region_score_ratio=pair['quadtree_23_37_1_1']/pair['quadtree_17_18_5_1'],
                     MAP_error_m=float(np.linalg.norm(xy[index]-[-3.2,-3.3])),
                     mean_error_m=float(np.linalg.norm(mean-[-3.2,-3.3])),
                     source_1m_probability=float(posterior[np.linalg.norm(xy-[-3.2,-3.3],axis=1)<=1].sum()),
                     variance=float(np.sum((xy-mean)**2,axis=1)@posterior))
        for key,value in metrics.items():
            if isinstance(value,int):assert value==target[key],key
            else:portable.same_number(value,target[key],key)
        stored=np.array([float(r['probability']) for r in saved_p if r['mask']==target['mask']])
        assert stored.shape==posterior.shape and np.allclose(stored,posterior,rtol=5e-12,atol=5e-15)
        mask_checks.append(dict(mask=target['mask'],max_posterior_abs_error=float(np.max(abs(stored-posterior)))))
    geometry=js(root/'M1_B_3D_RELEASE_SUPPORT_PRECHECK.json')
    occupancy=root/'evidence/physical/OccupancyGrid3D.csv';assert sha(occupancy)==geometry['occupancy_sha256']
    lines=occupancy.read_text(encoding='utf-8').splitlines()
    minimum=np.array(list(map(float,lines[0].split()[1:])));dims=np.array(list(map(int,lines[2].split()[1:])))
    step=float(lines[3].split()[1]);planes=[];plane=[]
    for line in lines[4:]:
        if line.strip()==';':
            if plane:planes.append(plane);plane=[]
        elif line.strip():plane.append(list(map(int,line.split())))
    if plane:planes.append(plane)
    occ=np.array(planes);assert occ.shape==(dims[2],dims[0],dims[1])
    for item in geometry['point_checks']:
        ijk=((np.array(item['XYZ'],dtype=np.float32)-minimum.astype(np.float32))/np.float32(step)).astype(int)
        assert ((ijk>=0)&(ijk<dims)).all() and ijk.tolist()==item['ijk']
        assert int(occ[ijk[2],ijk[0],ijk[1]])==item['occupancy']==0
    generated=[]
    for region in geometry['region_footprints']:
        x0,y0,x1,y1=region['bounds_xy'];z=int((np.float32(-.5)-np.float32(minimum[2]))/np.float32(step))
        count=0
        for i in range(dims[0]):
            if min(minimum[0]+(i+1)*step,x1)-max(minimum[0]+i*step,x0)<=1e-9:continue
            for j in range(dims[1]):
                if min(minimum[1]+(j+1)*step,y1)-max(minimum[1]+j*step,y0)<=1e-9:continue
                assert occ[z,i,j]==0;count+=1
                generated.append(dict(candidate=region['label'],voxel_i=i,voxel_j=j,voxel_k=z,
                                      occupancy=0,positive_area_overlap=True))
        assert count==region['overlapping_3D_voxels']==region['free_voxels'] and region['all_free']
    portable.compare_csv(root/'M1_B_SOURCE_FOOTPRINT_VOXELS.csv',generated)
    budget=js(root/'M1_A_FROZEN_FORWARD_BUDGET.json')
    assert budget['maximum_new_forward_calls']==len(budget['jobs'])==6
    assert budget['status'].startswith('WAITING_FOR_USER')
    for name,digest in budget['snapshot_file_hashes'].items():assert sha(root/'snapshot'/name)==digest,name
    assert sha(root/'evidence/source_before_parser_fix/m1_candidate_forward.cpp')==budget['entry_source_sha256']
    raw=(m0/'evidence/source/gsl/PMFS/internal/Simulations.cpp').read_bytes()
    copied=(root/'source/Simulations_native_with_state_access.cpp').read_bytes()
    assert copied.startswith(raw) and hashlib.sha256(raw).hexdigest()==budget['native_kernel_prefix_sha256']
    assert sha(root/'source/Simulations_native_with_state_access.cpp')==budget['isolated_native_kernel_with_accessors_sha256']
    suffix=copied[len(raw):].decode('utf-8')
    assert 'void r4_set_gaussian' in suffix and 'uint16_t r4_gaussian_index' in suffix
    provenance=js(root/'PREPARED_ENTRY_PROVENANCE.json')
    build=js(root/'NATIVE_CAPTURE_OBJECT_BUILD_RESULT.json')
    assert provenance['verdict']=='PASS_PREPARED_LOADER_NO_FORWARD_EXECUTION'
    assert provenance['budget_sha256']==sha(root/'M1_A_FROZEN_FORWARD_BUDGET.json')
    assert provenance['executable_sha256']==build['executable_sha256']
    assert build['new_forward_calls']==provenance['new_forward_calls']==0
    assert build['new_native_updates']==build['new_ROS_nodes']==0
    repair=js(root/'INPUT_PARSER_REPAIR.json');after=js(root/'POST_EXECUTION_VM_INTEGRITY.json')
    assert sha(root/'source/m1_candidate_forward.cpp')==repair['new_entry_sha256']==after['current_entry_sha256']
    assert repair['executable_sha256']==after['current_executable_sha256']
    assert repair['actual_forward_calls_before_repair']==0 and not repair['input_data_modified'] and not repair['native_kernel_modified']
    for line in repair['probe_stdout'].splitlines():
        decimal,hexadecimal=line.split(',');assert float(decimal).hex()==float.fromhex(hexadecimal).hex()
    approval=js(root/'M1_A_USER_BUDGET_APPROVAL.json')
    assert approval['answer']=='批准这6次二维候选计算' and approval['budget_sha256']==sha(root/'M1_A_FROZEN_FORWARD_BUDGET.json')
    ledger=js(root/'M1_A_EXECUTION_LEDGER.json')
    assert ledger['status']=='PASS_SIX_APPROVED_FORWARDS_CAPTURED_NO_POSTERIOR_UPDATE'
    assert ledger['attempted_calls']==ledger['completed_calls']==len(ledger['records'])==6
    assert ledger['prior_initialization_launches']==1 and ledger['prior_actual_forward_calls']==0
    assert ledger['combined_forward_wall_seconds']<120 and ledger['peak_RSS_bytes']<=536870912
    assert len(ledger['anchor_checks'])==2 and ledger['ROS_nodes']==ledger['native_updates']==ledger['new_3D_realizations']==0
    assert all(after['protected_dependency_checks'].values()) and all(after['snapshot_checks'].values())
    for job in budget['jobs']:
        folder=root/'evidence/forwards'/job['job'];record=js(folder/'RESULT.json')
        assert js(folder/'FORWARD_ENTERED.json')['forward_calls_entered']==1
        assert record['forward_calls']==1 and record['native_updates']==record['ROS_nodes']==0
        assert record['rng_before']==job['rng_before'] and record['gaussian_index_before']==job['gaussian_index_before']
        assert record['source_region']==[job[k] for k in ['origin_i','origin_j','size_i','size_j']]
        assert record['release_points']==2000 and record['captured_point_substitution'] is False
        candidate=rows(folder/'candidates.csv')[0];name=candidate['candidate_id']
        points=np.frombuffer((folder/candidate['points_file']).read_bytes(),dtype='<f4').reshape(-1,2)
        assert len(points)==2000 and np.isfinite(points).all()
        lo=np.array([meta['origin_x']+job['origin_i']*.25,meta['origin_y']+job['origin_j']*.25])
        hi=lo+[job['size_i']*.25,job['size_j']*.25]
        assert np.all(points>=lo-1e-6) and np.all(points<=hi+1e-6)
        for file in [candidate['map_file'],'maps/'+name+'_unblurred.f32']:
            hit=np.frombuffer((folder/file).read_bytes(),dtype='<f4')
            assert len(hit)==n and np.isfinite(hit).all() and np.all(hit>=0) and np.all(hit<=1+1e-6)
        if job['is_native_anchor']:
            anchor=root/'snapshot/anchors'/job['job'];row=js(anchor/'NATIVE_ROW.json')
            for actual_file,frozen_file in [(candidate['map_file'],row['map_file']),
                    ('maps/'+name+'_unblurred.f32','unblurred/'+name+'_unblurred.f32'),
                    (candidate['points_file'],row['points_file'])]:
                assert (folder/actual_file).read_bytes()==(anchor/frozen_file).read_bytes()
            assert record['rng_after']==row['rng_after'] and record['gaussian_index_after']==int(row['gaussian_index_after'])
            portable.same_number(record['score'],float(row['score']),'anchor_score',score=True)
    import analyse_m1
    calculated,scores,cells,regions=analyse_m1.analyse(root)
    portable.compare_json(js(root/'M1_A_RESULT.json'),calculated)
    for name,records in [('M1_A_RAW_SCORES.csv',scores),('M1_A_PER_CELL_DIFFERENCES.csv',cells),('M1_A_REGION_DIFFERENCES.csv',regions)]:
        portable.compare_csv(root/name,records)
    return dict(verdict='PASS_M1_MASK_REVIEW_ANCHORS_FAIR_1X1_AND_STATIC_3D_SUPPORT',package_hashes=len(manifest),
                frozen_M0_hashes=result['original_hashes'],portable_CSVs=result['derived_CSVs'],
                four_mask_checks=mask_checks,static_3D_points=3,static_3D_overlapping_voxels=len(generated),
                initialization_failures_before_any_forward=1,new_forward_calls=6,anchor_exact_matches=2,
                native_updates=0,new_ROS_nodes=0,new_3D_realizations=0,
                M1_A='WRONG_SOURCE_PREFERENCE_PERSISTS_IN_BOTH_RECORDED_STATES',physical_mechanism='HOLD',writes=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args();print(json.dumps(verify(args.root.resolve()),ensure_ascii=False,indent=2))
