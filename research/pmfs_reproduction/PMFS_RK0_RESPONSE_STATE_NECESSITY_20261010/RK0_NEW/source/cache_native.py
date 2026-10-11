"""Read-only physical-data cache builder; no simulation, VM, ROS or scoring.

The caller must freeze a contract and supervise wall/RSS before calling
build_cache. This module has no executable default and does not launch a batch
when imported. Each reference frame is crossed with ten exact receptor poses.
Zero contribution pairs are retained in dense float32 arrays, and all raw
filament records are retained for the calibration denominator.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,hashlib,importlib.util,json,math,time,collections
import numpy as np

F=np.float32
REFERENCE_IDS=('C7_0','C7_1','K2_0','K2_1')
RTOL=5e-6
ATOL=3e-7

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,data):
    assert not path.exists(),str(path)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
def load_math(m2):
    path=m2/'independent_raw_query_verify/verify_raw_receiver_queries.py'
    spec=importlib.util.spec_from_file_location('rk0_frozen_native_raw_math',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,path

def pose_aliases(m2):
    path=m2/'observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv'
    schedule=rows(path);assert len(schedule)==51
    grouped={}
    for row in schedule:
        stop=int(row['stop_id']);point=np.array([F(float(row['sensor_'+k])) for k in ['x','y','z']],dtype=F)
        if stop in grouped:assert np.array_equal(grouped[stop],point),'one stop has different actual poses'
        else:grouped[stop]=point
    assert sorted(grouped)==list(range(10))
    points=np.stack([grouped[k] for k in range(10)]).astype('<f4')
    assert len({p.tobytes() for p in points})==10
    aliases=[]
    for row in schedule:
        block=int(row['block_id']);branch=int(row['membership_branch']);stop=int(row['stop_id'])
        aliases.append(dict(query_id=f'receiver_b{block}_v{branch}',block_id=block,membership_branch=branch,stop_id=stop,pose_index=stop))
    return points,aliases,path

def cutoff_and_contributions(filaments,points,desc,occ,raw):
    """Return native per-particle ppm, preserving all zero denominator records."""
    n=len(filaments);matrix=np.zeros((n,len(points)),dtype='<f4')
    eligible=np.zeros(len(points),dtype=np.int64);blocked=np.zeros(len(points),dtype=np.int64)
    positive=np.zeros(len(points),dtype=np.int64);totals=np.zeros(len(points),dtype='<f4')
    sigma=filaments[:,3]
    limit=np.divide(np.multiply(sigma,F(3),dtype=F),F(100),dtype=F)
    limit_sq=np.multiply(limit,limit,dtype=F)
    centre=np.empty(n,dtype=F)
    fixed_den=math.sqrt(float(F(F(8)*raw.PI_CUBED)))
    for i,s in enumerate(sigma):
        sd=float(s);denominator=fixed_den*sd*sd*sd
        moles=F(float(desc['total_moles'])/denominator)
        centre[i]=F(1e6*float(moles)/float(desc['all_gas_moles']))
    for receiver,point in enumerate(points):
        assert raw.cell_state(point,desc,occ)==0,'receiver not physically free'
        delta=np.subtract(filaments[:,:3],point,dtype=F)
        # The native sqrlength starts at float32 zero and adds x,y,z in order.
        squared=np.zeros(n,dtype=F)
        for axis in range(3):
            np.add(squared,np.multiply(delta[:,axis],delta[:,axis],dtype=F),out=squared)
        keep=np.flatnonzero(squared<limit_sq);eligible[receiver]=len(keep)
        total=F(0)
        for particle in keep:
            fil=filaments[particle]
            if not raw.los(point,fil[:3],desc,occ):blocked[receiver]+=1;continue
            distance_cm=F(F(100)*F(math.sqrt(float(squared[particle]))))
            exponent=F(-F(distance_cm*distance_cm)/F(F(F(2)*sigma[particle])*sigma[particle]))
            value=F(float(centre[particle])*math.exp(float(exponent)))
            matrix[particle,receiver]=value
            total=F(total+value)  # Original particle serial order; never pairwise np.sum for F.
            positive[receiver]+=int(value>0)
        totals[receiver]=total
    return matrix,totals,eligible,blocked,positive

def check_total(actual,expected,bank,query):
    actual=F(actual);expected=F(float(expected));absolute=abs(float(actual)-float(expected))
    assert absolute<=ATOL+RTOL*abs(float(expected)),(bank,query,float(actual),float(expected),absolute)
    return dict(absolute_ppm_difference=absolute,ULP_difference=abs(int(actual.view(np.uint32))-int(expected.view(np.uint32))))

def build_cache(m2:Path,out:Path,contract:dict):
    """Build four reference-only, cross-frame/pose caches under caller limits.

    Existing out must be empty. The fixed reference IDs are never extended to
    the 2/3 holdouts. 49 physical frames are computed once per reference;
    branch0's 50 planned-time events supply exposure multiplicity to the later
    h fit. The 51st membership alternative is an anchor, not extra fit weight.
    """
    m2=Path(m2);out=Path(out)
    if out.exists():assert not any(out.iterdir()),'refuse to overwrite nonempty cache directory'
    else:out.mkdir(parents=True)
    start=time.perf_counter();raw,math_path=load_math(m2)
    points,aliases,schedule_path=pose_aliases(m2);alias={a['query_id']:a for a in aliases}
    geometry=m2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv';occ=raw.occupancy(geometry)
    np.save(out/'RECEPTOR_POSES_STOP_ORDER.f32.npy',points,allow_pickle=False)
    write_csv(out/'RECEPTOR_ALIAS_51_TO_10.csv',aliases)
    contract_hash=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    inputs={str(schedule_path.relative_to(m2)):sha(schedule_path),str(geometry.relative_to(m2)):sha(geometry),str(math_path.relative_to(m2)):sha(math_path)}
    jobs=[];query_rows={};exposure_rows=[]
    for bank_id in REFERENCE_IDS:
        bank=m2/'native_reference_evidence/realizations'/bank_id
        qpath=bank/'QUERY_OUTPUT.csv';native=[q for q in rows(qpath) if q['query_id'].startswith('receiver_')]
        assert len(native)==51 and {q['query_id'] for q in native}==set(alias)
        for q in native:
            stop=alias[q['query_id']]['pose_index']
            assert np.array_equal(np.array([F(float(q[k])) for k in ['x','y','z']],dtype=F),points[stop])
        query_rows[bank_id]=native
        branch0=[q for q in native if alias[q['query_id']]['membership_branch']==0];assert len(branch0)==50
        exposures=collections.Counter(int(q['frame']) for q in branch0)
        assert len(exposures)==49 and sum(exposures.values())==50 and sorted(exposures.values()).count(2)==1
        manifest_path=bank/'ALL_FRAME_SHA256_AND_TIME.csv';manifest={int(r['frame']):r for r in rows(manifest_path)}
        inputs[str(qpath.relative_to(m2))]=sha(qpath);inputs[str(manifest_path.relative_to(m2))]=sha(manifest_path)
        for frame in sorted({int(q['frame']) for q in native}):
            assert frame in exposures,'membership alternative uses unplanned snapshot'
            path=bank/'bank'/('iteration_'+str(frame));expected=manifest[frame]['SHA256'];assert sha(path)==expected
            inputs[str(path.relative_to(m2))]=expected
            exposure_rows.append(dict(reference_bank=bank_id,frame=frame,planned_time_exposure_weight=exposures[frame],filament_records=int(manifest[frame]['filaments']),weighted_filament_records=int(manifest[frame]['filaments'])*exposures[frame]))
            jobs.append(dict(bank_id=bank_id,frame=frame,path=path,expected_SHA256=expected,exposure=exposures[frame],expected_filaments=int(manifest[frame]['filaments'])))
    assert len(jobs)==196
    (out/'PRE_CACHE_INPUT_SHA256.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
    write_csv(out/'FIT_EXPOSURE_MULTIPLICITY.csv',exposure_rows)
    native_anchor=query_rows['C7_0'][0];first_frame=int(native_anchor['frame'])
    first=next(j for j in jobs if j['bank_id']=='C7_0' and j['frame']==first_frame)
    jobs=[first]+[j for j in jobs if j is not first]
    ledger=[];frame_records=[];anchor_records=[];global_abs=global_ulp=0;eligible_total=blocked_total=positive_total=0;weighted_records=0
    for number,j in enumerate(jobs):
        print(f'[RK0 CACHE {number+1}/196] {j["bank_id"]} frame={j["frame"]} cross_poses=10 fit_not_started',flush=True)
        desc=raw.snapshot(j['path']);assert len(desc['filaments'])==j['expected_filaments']
        assert desc['wind_index']==10 and desc['gas_type']==13 and np.array_equal(desc['dimensions'],occ['dimensions'])
        assert np.array_equal(desc['minimum'],occ['minimum']) and desc['cell_size']==occ['cell_size']
        matrix,totals,eligible,blocked,positive=cutoff_and_contributions(desc['filaments'],points,desc,occ,raw)
        if number==0:
            assert j['bank_id']=='C7_0' and j['frame']==first_frame
            a=check_total(totals[alias[native_anchor['query_id']]['pose_index']],native_anchor['ppm_float32'],'C7_0',native_anchor['query_id'])
            first_result=dict(status='PASS_FIRST_EXISTING_NATIVE_CPP_RECEIVER_TOTAL',reference_bank='C7_0',frame=first_frame,query_id=native_anchor['query_id'],computed_ppm=float(totals[alias[native_anchor['query_id']]['pose_index']]),native_ppm=float(F(float(native_anchor['ppm_float32']))),**a)
            (out/'FIRST_NATIVE_ANCHOR.json').write_text(json.dumps(first_result,indent=2)+'\n',encoding='utf-8')
            print('[RK0 FIRST NATIVE ANCHOR PASS] remaining reference cache permitted by caller contract',flush=True)
        frame_checks=[]
        for q in query_rows[j['bank_id']]:
            if int(q['frame'])!=j['frame']:continue
            pose=alias[q['query_id']]['pose_index'];comparison=check_total(totals[pose],q['ppm_float32'],j['bank_id'],q['query_id'])
            global_abs=max(global_abs,comparison['absolute_ppm_difference']);global_ulp=max(global_ulp,comparison['ULP_difference'])
            check=dict(reference_bank=j['bank_id'],query_id=q['query_id'],frame=j['frame'],pose_index=pose,cache_F32_ppm=float(totals[pose]),native_cpp_ppm=float(F(float(q['ppm_float32']))),**comparison)
            anchor_records.append(check);frame_checks.append(check)
        target=out/j['bank_id'];target.mkdir(exist_ok=True);filename='iteration_'+str(j['frame'])+'.npz';dest=target/filename;assert not dest.exists()
        np.savez_compressed(dest,filaments=desc['filaments'].astype('<f4'),contributions=matrix,native_totals=totals,cutoff_eligible=eligible,LOS_blocked=blocked,positive_contributors=positive,reference_frame=np.array(j['frame'],dtype='<i8'),planned_time_exposure_weight=np.array(j['exposure'],dtype='<i8'),total_moles=np.array(desc['total_moles'],dtype='<f4'),all_gas_moles=np.array(desc['all_gas_moles'],dtype='<f4'))
        n=len(desc['filaments']);pairs=matrix.size;nonzero=int(np.count_nonzero(matrix));eligible_total+=int(sum(eligible));blocked_total+=int(sum(blocked));positive_total+=nonzero;weighted_records+=n*j['exposure']
        ledger.append(dict(reference_bank=j['bank_id'],frame=j['frame'],snapshot_SHA256=j['expected_SHA256'],cache_file=dest.relative_to(out).as_posix(),cache_SHA256=sha(dest),cache_bytes=dest.stat().st_size,filament_records=n,planned_time_exposure_weight=j['exposure'],weighted_denominator_records=n*j['exposure'],cross_pose_pairs=pairs,strict_3sigma_eligible_pairs=int(sum(eligible)),LOS_blocked_pairs=int(sum(blocked)),positive_pairs=nonzero,zero_pairs=pairs-nonzero,wall_elapsed_s=time.perf_counter()-start))
        frame_records.append(dict(bank=j['bank_id'],frame=j['frame'],cache_relative_path=dest.relative_to(out).as_posix(),cache_SHA256=sha(dest),snapshot_SHA256=j['expected_SHA256'],exposure_weight=j['exposure'],filament_records=n,native_query_checks=frame_checks))
    assert len(anchor_records)==204 and len(ledger)==196
    write_csv(out/'CONTRIBUTION_CACHE_LEDGER.csv',ledger);write_csv(out/'CACHE_NATIVE_CPP_TOTAL_ANCHORS.csv',anchor_records)
    result=dict(status='PASS_REFERENCE_ONLY_CROSS_SNAPSHOT_NATIVE_PER_FILAMENT_CACHE',reference_ids=list(REFERENCE_IDS),unique_frames=196,unique_receptor_poses=10,receiver_members_per_bank=51,native_cpp_total_anchors=204,first_anchor_before_rest=True,cross_pose_pairs=sum(r['cross_pose_pairs'] for r in ledger),unique_particle_records=sum(r['filament_records'] for r in ledger),fit_exposure_weighted_records=weighted_records,positive_pairs=positive_total,zero_pairs=sum(r['zero_pairs'] for r in ledger),strict_3sigma_eligible_pairs=eligible_total,LOS_blocked_pairs=blocked_total,maximum_native_CPP_total_absolute_difference=global_abs,maximum_native_CPP_total_ULP_difference=global_ulp,wall_seconds=time.perf_counter()-start,actual_execution='Local decode/native readout arithmetic only; no physical generation, candidate forward, VM or ROS; no U/S fit or heldout state used',primitive_zero_denominator='All original reference filament records included; contrib matrix keeps explicit zero for cutoff/LOS/no-ppm pairs',exposure_rule='49 unique frames computed once, branch0 planned 50 exposure weights including one duplicate frame count2; correlated exposure weighting, not independent samples',canonical_contract_dict_SHA256=contract_hash,math_source_SHA256=sha(math_path),snapshot_input_SHA256=inputs,cache_total_bytes=sum(r['cache_bytes'] for r in ledger),fixed_native_anchor_tolerance=dict(relative=RTOL,absolute_ppm=ATOL))
    result.update(frames=frame_records,poses=[[float(x) for x in p] for p in points],pose_aliases=aliases,npz_schema={'filaments':'(N,4)float32 original x,y,z,sigma_cm, including every zero contribution record','contributions':'(N,10)float32 native ppm, zeros retained','native_totals':'(10,)float32 accumulation in native particle order','planned_time_exposure_weight':'scalar int64, branch0 exposure count'})
    (out/'CONTRIBUTION_CACHE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
