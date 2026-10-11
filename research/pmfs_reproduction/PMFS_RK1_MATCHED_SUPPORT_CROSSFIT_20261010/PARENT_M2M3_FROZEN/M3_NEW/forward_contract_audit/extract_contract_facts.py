"""Read-only factual extraction. No candidate forward, gas generation or ROS."""
import sys
sys.dont_write_bytecode=True
import csv,hashlib,json,math,struct
from pathlib import Path
import numpy as np
WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[2]
M1=ROOT/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
M2=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
sys.path.insert(0,str(ROOT/'work/pmfs_m2_observation_discrimination_20261010/independent_raw_query_verify'))
from verify_raw_receiver_queries import occupancy,cell_state,snapshot

def csvrows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

occ=occupancy(M2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv')
wind_file=M2/'frozen_B4_inputs/derived_B4/wind/wind_iteration_10';raw=wind_file.read_bytes()
assert struct.unpack_from('<ii',raw)==(3,0)
field=np.frombuffer(raw,dtype='<f4',offset=8).reshape(int(np.prod(occ['dimensions'])),3)
pmfs=csvrows(M1/'snapshot/input.csv')
probe=[r for r in csvrows(M2/'native_reference_evidence/realizations/C7_0/QUERY_OUTPUT.csv') if r['query_id'].startswith('grid_b0_v0_c')]
lookup=[];max_vec_diff=0.
for row in probe:
    p=np.array([float(row[k]) for k in ['x','y','z']],dtype=np.float32)
    ijk=np.trunc((p-occ['minimum'])/occ['cell_size']).astype(int)
    ix=int(ijk[0]+ijk[1]*occ['dimensions'][0]+ijk[2]*occ['dimensions'][0]*occ['dimensions'][1])
    max_vec_diff=max(max_vec_diff,max(abs(float(field[ix,j])-float(row['wind_'+k])) for j,k in enumerate(['x','y','z'])))
    p[2]=np.float32(-.5);ijk=np.trunc((p-occ['minimum'])/occ['cell_size']).astype(int)
    ix=int(ijk[0]+ijk[1]*occ['dimensions'][0]+ijk[2]*occ['dimensions'][0]*occ['dimensions'][1])
    ci=int(row['query_id'].split('_c')[-1]);assert cell_state(p,occ,occ)==0
    lookup.append(dict(cell_index=ci,grid_i=ci%34,grid_j=ci//34,x=float(p[0]),y=float(p[1]),source_height=float(p[2]),
        source_height_u=float(field[ix,0]),source_height_v=float(field[ix,1]),source_height_w=float(field[ix,2]),
        frozen_sensor_height_u=float(pmfs[ci]['u']),frozen_sensor_height_v=float(pmfs[ci]['v']),physical_free_at_source_height=1))
assert max_vec_diff==0 and len(lookup)==447
with (WORK/'COMMON_SOURCE_HEIGHT_WIND_SLICE_PROPOSAL.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(lookup[0]));w.writeheader();w.writerows(lookup)

forward_facts=[]
for path in sorted((M1/'evidence/forwards').glob('*/RESULT.json')):
    r=json.loads(path.read_text());assert r['release_points']%5==0
    warm_iterations=r['release_points']//5-200
    forward_facts.append(dict(job=path.parent.name,released_centres=r['release_points'],inferred_warmup_steps=warm_iterations,
        warmup_dt_s=.2,warmup_model_duration_s=warm_iterations*.2,record_steps=200,record_dt_s=.1,record_duration_s=20,
        warmup_release_rate_per_model_second=25,record_release_rate_per_model_second=50))
sigma=[]
for bank in (M2/'native_reference_evidence/realizations').iterdir():
    if not bank.is_dir():continue
    for f in (bank/'bank').glob('iteration_*'):
        d=snapshot(f);sigma.extend(map(float,d['filaments'][:,3]))
sig=np.array(sigma)
manifest=csvrows(M2/'native_reference_evidence/realizations/C7_0/ALL_FRAME_SHA256_AND_TIME.csv')
first_index10=next(r for r in manifest if r['wind_index']=='10')
targets=csvrows(M2/'native_reference_evidence/realizations/C7_0/QUERY_PHYSICAL_LINEAGE.csv')
facts=dict(qualification='READ_ONLY_CONTRACT_EXTRACTION_NOT_MODEL_CAUSE_PROOF',new_forwards=0,new_gas=0,new_ROS=0,
    release=dict(PMFS_centres_per_record_step=5,PMFS_centres_per_record_second=50,PMFS_centres_per_warmup_second=25,GADEN_centres_per_second=7,
                 source_rate_ratio_record=50/7,source_rate_ratio_warmup=25/7),
    noise=dict(PMFS_sigma_velocity_m_s=.2,PMFS_record_dt_s=.1,PMFS_record_position_sigma_m=.02,PMFS_warmup_position_sigma_m=.04,
               GADEN_yaml_sigma=.02,GADEN_constructor_multiplier=10,GADEN_effective_sigma_velocity_m_s=.2,GADEN_dt_s=.1,GADEN_position_sigma_m=.02,
               statement='Horizontal recording noise scales match. GADEN adds independent z-axis draw; warmup PMFS displacement scale differs through doubled dt.'),
    buoyancy=dict(gas_type=13,name='smoke',specific_gravity=.89,initial_center_ppm=10,initial_terminal_velocity_m_s=9.8*(1-.89)*1.205*10e-6/(18*19e-6),
                   dependence='ConcentrationAtCenter decays with sigma^-3, so buoyancy velocity changes with packet age; no fixed .03798m/s for old filaments.'),
    footprint=dict(initial_sigma_cm=10,growth_gamma_cm2_s=15,observed_used_snapshot_sigma_cm_min=float(sig.min()),
                   observed_used_snapshot_sigma_cm_max=float(sig.max()),observed_used_snapshot_sigma_cm_median=float(np.median(sig)),
                   observed_3sigma_radius_m_min=float(sig.min()*3/100),observed_3sigma_radius_m_max=float(sig.max()*3/100),
                   pooled_sigma_count=len(sig),pooled_sigma_count_is_not_independent_sample_size=True,
                   PMFS_per_center_sigma_or_moles='ABSENT',PMFS_post_field_blur_sigma_cells=1.5,PMFS_post_field_blur_sigma_m=.375),
    chronology=dict(GADEN_first_saved_index10=dict(frame=int(first_index10['frame']),physical_time_s=float(first_index10['physical_snapshot_time_s'])),
                    actual_query_physical_target_min_s=min(float(r['target_physical_s']) for r in targets),actual_query_physical_target_max_s=max(float(r['target_physical_s']) for r in targets),
                    all_observation_period_wind_index=10,PMFS_fresh_candidate_initial_plume='empty, independent warmup',GADEN_initial_plume='empty at physical time0; queried after >322s of release history'),
    M1_saved_actual_forward_budgets=forward_facts,
    wind=dict(raw_wind_SHA256=sha(wind_file),raw_file_vs_saved_grid_xyz_max_abs=max_vec_diff,source_height_common_slice_all_447_cells_3D_free=True,
              source_height_slice_proposal_SHA256=sha(WORK/'COMMON_SOURCE_HEIGHT_WIND_SLICE_PROPOSAL.csv'),
              rule='Same z=-.5 table for both candidates; this is a new diagnostic control proposal, not a correction to frozen official N1 inputs.'),
    source_hashes={p.name:sha(p) for p in (WORK/'source').iterdir() if p.suffix in ['.cpp','.hpp']})
(WORK/'FORWARD_CONTRACT_FACTS.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in facts.items() if k!='source_hashes'},ensure_ascii=False,indent=2))
