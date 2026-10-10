from pathlib import Path
import json,csv,hashlib,subprocess,shutil,ast,collections

root=Path(__file__).resolve().parents[2]
out=root/'outputs/PMFS_OFFICIAL_SCENARIO_STATIC_QUALIFICATION_20261009'
def js(n):return json.loads((out/n).read_text(encoding='utf-8'))
pmfs=js('OFFICIAL_PMFS_CONFIG_RAW.json');test=js('OFFICIAL_GADEN_CONFIG_RAW.json');vgr=js('VGR_LOCAL_STATIC_AUDIT.json');winds=js('WIND_NUMERICAL_AUDIT.json')
wind_by={g['group']:g for g in winds};inventory=[];matrix=[]
defaults={}
for n in ast.walk(ast.parse(pmfs['launch'])):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='SetLaunchConfiguration':
        kw={x.arg:x.value for x in n.keywords}
        if all(isinstance(kw.get(k),ast.Constant) for k in ['name','value']):defaults[kw['name'].value]=kw['value'].value

def add(row,qualification):
    inventory.append(row);matrix.append(dict(id=row['id'],category=row['category'],decision=row['decision'],**qualification,blockers=row['blockers'],evidence=row['evidence']))

for r in pmfs['rows']:
    g=wind_by[r['wind_prefix']];support=r['source_support'];name=r['simulation_id'];sim=r['simulation']
    params=dict(defaults);params.update(sim)
    is_c1=name=='C1';blocked=not support['source_supported']
    candidate_role='A_FIXED_WIND_CANDIDATE' if name.startswith(('A','E')) else 'B_3D_TRANSPORT_CANDIDATE'
    if blocked:candidate_role='C_GEOMETRY_DIAGNOSTIC_CANDIDATE'
    reason=[]
    if blocked:reason.append('SOURCE_OUTSIDE_NATIVE_2D_SUPPORT')
    if not is_c1:reason+=['OFFICIAL_CASE_GAS_RECORD_MISSING','OFFICIAL_DERIVED_3D_RELEASE_GRID_MISSING','ACTUAL_FRAME_TIMES_AND_RAW_ROS_EVENTS_NOT_CAPTURED']
    if sim['allow_looping']:reason.append('OFFICIAL_PERIODIC_GAS_PLAYBACK_NOT_INDEPENDENT_CONTINUOUS_SEQUENCE')
    category='C' if is_c1 else 'D'
    basez=r['basic']['robots'][0]['position'][2];sensorz=basez+.5
    row=dict(id=r['id'],family='PMFS_OFFICIAL',configuration=r['simulation_config'],version='4e141e162551e674f2f30ddb8859136c72139aac',
        source_xyz=json.dumps(r['source_xyz']),source_type='point',map=r['map_config'],source_3d_release_free='PASS_FROZEN_C1' if is_c1 else 'HOLD',
        source_2d_supported=support['source_supported'],candidate_free_cells=support['num_free_after_prune'],source_candidate_indices=json.dumps(support['source_indices']),
        wind_raw_frames=len(g['frames']),wind_distinct_numeric_fields=g['unique_velocity_numeric_fields'],wind_raw_numeric_change=g['observed_numerical_variation'],
        physical_wind_regime=('STATIC_SINGLE_FIELD' if len(g['frames'])==1 else 'RAW_TRANSIENT_THEN_FINAL_FIELD_HELD;_LATE_PLAYBACK_CONTRACT_TO_VERIFY'),
        gas_frames='FROZEN_CLEAN_C1_BANK_AVAILABLE' if is_c1 else 0,actual_gas_time_trace=is_c1,raw_ROS_events_bound='FROZEN_R7_ONLY' if is_c1 else 'NOT_CAPTURED',
        initial_iteration=r['gaden']['gaden_player']['ros__parameters']['initial_iteration'],gas_playback_loop=sim['allow_looping'],
        declared_sensor_z_m=sensorz,source_sensor_height_gap_m=abs(sensorz-r['source_xyz'][2]),
        source_discrimination_power=params['sourceDiscriminationPower'],forward_noise_stdev=params['filament_movement_stdev'],
        potential_role=candidate_role,category=category,decision='HOLD',blockers=';'.join(reason),evidence='OFFICIAL_PMFS_CONFIG_RAW.json#'+r['id'])
    add(row,dict(source_XYZ_and_3D_release='PASS_FROZEN_C1' if is_c1 else 'HOLD_NO_MATCHING_GENERATED_GRID',
        PMFS_candidate_support='PASS_STATIC' if not blocked else 'FAIL',wind_field_values='PASS_STATIC_CSV_CONTENT',
        wind_gas_observation_physical_time='PASS_FROZEN_R7_ONLY' if is_c1 else 'HOLD',TF_and_clocks='PASS_FROZEN_R7_N1_ONLY' if is_c1 else 'HOLD_NOT_CAPTURED',
        diffusion_generation_lineage='PASS_FROZEN_C1_DECLARED_REVISION' if is_c1 else 'HOLD_NO_RESOLVED_GENERATION',
        sensor_response_and_units='PASS_FROZEN_R7_N1_ONLY' if is_c1 else 'HOLD_DECLARED_PARAMS_ONLY',source_blind_observation_contract='HOLD_NEW_CASE_NOT_EXECUTED',
        independent_realizations='HOLD_ONE_FROZEN_CASE' if is_c1 else 'HOLD',observability='HOLD',native_localization='R7_FAILURE_FROZEN' if is_c1 else 'NOT_RUN'))

for r in test:
    wp=r['wind_prefix'];matching=[]
    for g in winds:
        if g['source']['revision']!='ccb02e959a45a188e4b6c78792e197633fc64f1c':continue
        if any(str(Path(f['path']).with_suffix('')).rsplit('_',1)[0]==wp for f in g['frames']):matching.append(g)
    g=matching[0] if matching else None
    row=dict(id=r['id'],family='GADEN_TEST_ENV',configuration=r['sim_path'],version='ccb02e959a45a188e4b6c78792e197633fc64f1c',
        source_xyz=json.dumps(r['source_xyz']),source_type=r['source_type'],map='NO_GENERATED_PMFS_NAVIGATION_MAP',source_3d_release_free='HOLD',
        source_2d_supported='HOLD',candidate_free_cells='',source_candidate_indices='',wind_raw_frames=len(g['frames']) if g else 0,
        wind_distinct_numeric_fields=g['unique_velocity_numeric_fields'] if g else None,wind_raw_numeric_change=g['observed_numerical_variation'] if g else None,
        physical_wind_regime='RAW_NUMERIC_VARIATION_ONLY' if g and g['observed_numerical_variation'] else 'RAW_STATIC_OR_UNIFORM_FORMAT_TO_BIND',
        gas_frames=0,actual_gas_time_trace=False,raw_ROS_events_bound='NOT_CAPTURED',initial_iteration=r['scene']['playback_initial_iteration'],
        gas_playback_loop=r['scene']['playback_loop']['loop'],declared_sensor_z_m='',source_sensor_height_gap_m='',source_discrimination_power='',forward_noise_stdev='',
        potential_role='B_TIME_VARYING_CANDIDATE' if r['scenario']=='10x6_empty_room' else 'A_OR_B_CONFIG_CANDIDATE',
        category='D',decision='HOLD',blockers='PROCESSED_3D_AND_2D_MAPS_MISSING;GAS_AND_RAW_EVENT_TIME_CONTRACT_MISSING;PMFS_ENV_BINDING_NOT_PROVIDED'+
        (';DISTRIBUTED_LINE_SOURCE_NOT_UNKNOWN_POINT_SOURCE' if r['source_type']=='line' else ''),evidence='OFFICIAL_GADEN_CONFIG_RAW.json#'+r['id'])
    add(row,dict(source_XYZ_and_3D_release='HOLD',PMFS_candidate_support='HOLD',wind_field_values='PASS_STATIC_CSV_CONTENT' if g else 'HOLD',
        wind_gas_observation_physical_time='HOLD',TF_and_clocks='HOLD',diffusion_generation_lineage='HOLD_UNEXECUTED_CONFIG_ONLY',
        sensor_response_and_units='HOLD',source_blind_observation_contract='HOLD',independent_realizations='HOLD',observability='HOLD',native_localization='NOT_RUN'))

for r in vgr['recordings']:
    geom=r['occupancy3d'];support=r['source_support'];h=r['sampled_headers'][0]
    grid_matches=geom is not None and geom['dimensions']==h.get('dimensions') and all(abs(a-b)<1e-6 for a,b in zip(geom['minimum'],h.get('env_min',[])))
    row=dict(id=r['id'],family='VGR_EXISTING_WINDOWS',configuration=r['path'],version='ORIGINAL_LOCAL_RECORD_GENERATOR_REVISION_UNRESOLVED',
        source_xyz=json.dumps(r['source_xyz']),source_type='point_from_header',map='evidence/vgr_geometry/'+r['house']+'/occupancy.yaml',
        source_3d_release_free='RELATED_GRID_FREE' if geom and geom['source_free'] else 'RELATED_GRID_NONFREE_OR_OUTSIDE',
        source_2d_supported=support['source_supported'] if support else 'HOLD',candidate_free_cells='',source_candidate_indices=json.dumps(support['source_indices']) if support else '',
        wind_raw_frames=len(r['wind_samples']),wind_distinct_numeric_fields=r['distinct_sampled_numeric_winds'],wind_raw_numeric_change=r['distinct_sampled_numeric_winds']>1,
        physical_wind_regime='SELECTED_STORED_WIND_VALUES_DIFFER;_PHYSICAL_TIME_UNQUALIFIED',gas_frames=r['frames'],actual_gas_time_trace=False,
        raw_ROS_events_bound='NOT_ATTACHED_TO_RECORD',initial_iteration='',gas_playback_loop='UNQUALIFIED',declared_sensor_z_m='',source_sensor_height_gap_m='',
        source_discrimination_power='',forward_noise_stdev='',potential_role='B_CANDIDATE_OR_GEOMETRY_DIAGNOSTIC',category='D',decision='HOLD',
        blockers='RESOLVED_GENERATOR_AND_ACTUAL_TIME_TRACE_MISSING;NO_RAW_ROS_TF_BINDING;NO_START_POSE_BOUND_TO_PMFS_PRUNE;RELATED_3D_GRID_PROVENANCE_NOT_RELEASE_CONTRACT',
        evidence='VGR_LOCAL_STATIC_AUDIT.json#'+r['id'])
    add(row,dict(source_XYZ_and_3D_release='HOLD_RELATED_POINT_GRID_ONLY',PMFS_candidate_support='FAIL_STATIC' if support and not support['source_coarse_free'] else 'HOLD_START_POSE_REQUIRED',
        wind_field_values='PASS_SAMPLED_DENSE_BINARY' if r['wind_samples'] else 'HOLD',wind_gas_observation_physical_time='HOLD_NO_TIME_IN_LEGACY_HEADER',
        TF_and_clocks='HOLD',diffusion_generation_lineage='HOLD',sensor_response_and_units='HOLD',source_blind_observation_contract='HOLD',
        independent_realizations='HOLD_SEEDS_NOT_BOUND_TO_GENERATION',observability='HOLD',native_localization='NOT_RUN_THIS_ROUND',
        related_grid_header_match=grid_matches))

old=root/'outputs/PMFS_R6_CAUSE_TRIAGE_20261009/EXISTING_RECORD_QUALIFICATION.csv'
with old.open(encoding='utf-8-sig') as f:previous=list(csv.DictReader(f))
guest=js('GUEST_STATIC_INVENTORY.json')
current={e['path']:e for r in guest['roots'] for e in r['entries'] if 'frame_count' in e}
for r in previous:
    if r['platform']!='VM' or r['path'] not in current:continue
    id='GUEST_'+r['path'].split('/hcmc_v1_independent_data_20260922/',1)[-1].split('/FilamentSimulation')[0].replace('/','_')
    row=dict(id=id,family='EXISTING_GUEST_INDEPENDENT_BANK',configuration=r['path'],version='PREVIOUS_R6_AUDIT_REUSED',source_xyz=r['source_xyz'],source_type='point',
        map='PREVIOUS_R6_ONLY',source_3d_release_free='HOLD',source_2d_supported='HOLD',candidate_free_cells='',source_candidate_indices='',
        wind_raw_frames='',wind_distinct_numeric_fields='',wind_raw_numeric_change='UNQUALIFIED',physical_wind_regime='PREVIOUS_WIND_RELEASE_CONTRACT_HOLD',
        gas_frames=current[r['path']]['frame_count'],actual_gas_time_trace=False,raw_ROS_events_bound='NOT_ATTACHED',initial_iteration='',gas_playback_loop='UNQUALIFIED',
        declared_sensor_z_m='',source_sensor_height_gap_m='',source_discrimination_power='',forward_noise_stdev='',potential_role='D_PREVIOUS_HOLD',category='D',decision='HOLD',
        blockers=r['reason'],evidence='evidence/previous_R6_record_qualification.csv#'+id)
    add(row,dict(source_XYZ_and_3D_release='HOLD',PMFS_candidate_support='HOLD',wind_field_values='PREVIOUS_RECORD_ONLY',wind_gas_observation_physical_time='HOLD',
        TF_and_clocks='HOLD',diffusion_generation_lineage='HOLD',sensor_response_and_units='HOLD',source_blind_observation_contract='HOLD',
        independent_realizations='HOLD',observability='HOLD',native_localization='NOT_RUN_THIS_ROUND'))
shutil.copyfile(old,out/'evidence/previous_R6_record_qualification.csv')
assert len({r['id'] for r in inventory})==len(inventory)
def write_csv(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (out/name).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
write_csv('OFFICIAL_SCENARIO_INVENTORY.csv',inventory);write_csv('PHYSICAL_DATA_QUALIFICATION_MATRIX.csv',matrix)

selection=[next(r for r in pmfs['rows'] if r['id']==id) for id in ['PMFS_E3','PMFS_B4']]
selection_lock=dict(selection_before_new_outcomes=True,ids=[r['id'] for r in selection],basis='Native 2D support, fixed/non-looping control and different 3D environment; no observed localization outcome used',
    baseline='PMFS_E3',complex_candidate='PMFS_B4',native_tests_executed=0,new_gas_generations=0,new_seeds=0,new_CFD=0,
    source_coordinates_unchanged=True,official_maps_unchanged=True,baseline_algorithm='N1_ENGINEERING_ALIGNED_UPSTREAM_CORE_WITH_OFFICIAL_PER_CASE_PARAMETERS',
    historical_author_N0_reproduction='NOT_CLAIMED',timed_mechanism='HOLD_NO_QUALIFIED_LATE_PLAYBACK_TIME_VARYING_CASE',
    selected_cases=selection,launch_default_bindings=defaults,execution_authorization='STATIC_AUDIT_AND_PLAN_ONLY_STOP_FOR_INDEPENDENT_REVIEW')
(out/'TWO_SCENARIO_SELECTION_LOCK.json').write_text(json.dumps(selection_lock,indent=2),encoding='utf-8')
repo='D:/ZYC/A-gas/_reference_native_pmfs_upstream_20260923';pin='4e141e162551e674f2f30ddb8859136c72139aac'
bundled=[]
for r in selection:
    prefix='Environment_config/PMFS/scenarios/'+r['scenario']+'/'
    names=[r['wind_prefix']+('_0.csv' if r['scenario']=='E' else '_0.csv')]
    if r['scenario']=='B':names.append(r['wind_prefix']+'_10.csv')
    for n in r['simulation']['models']+r['simulation']['outlets_models']:
        names.append(prefix+'cad_models/'+Path(n).name)
    for n in names:
        b=subprocess.check_output(['git','-C',repo,'show',pin+':'+n])
        target=out/'evidence/selected_raw_assets'/r['simulation_id']/Path(n).name
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
        bundled.append(dict(git_path=n,revision=pin,evidence_file=target.relative_to(out).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
(out/'SELECTED_RAW_ASSET_INDEX.json').write_text(json.dumps(bundled,indent=2),encoding='utf-8')

asset_records=js('RAW_ASSET_HASHES.json')+js('VGR_ASSET_HASHES.json')+js('TEST_ENV_AND_SOURCE_HASHES.json')
unique={}
for r in asset_records:
    key=(r['provider'],r.get('repository',''),r.get('revision',''),r['path'])
    if key in unique:assert unique[key]['sha256']==r['sha256']
    unique[key]=r
(out/'SOURCE_ASSET_HASHES.json').write_text(json.dumps(list(unique.values()),indent=2),encoding='utf-8')
decision=dict(verdict='STATIC_AUDIT_PASS_EXECUTION_HOLD_PHYSICAL_MECHANISM_HOLD',inventory_rows=len(inventory),
    official_PMFS_configs=20,official_PMFS_static_source_supported=10,official_PMFS_static_source_excluded=10,
    official_GADEN_test_env_scenarios=7,VGR_houses=20,VGR_existing_recordings=77,guest_legacy_records_in_current_bounded_roots=len(inventory)-104,
    classification_counts=dict(collections.Counter(r['category'] for r in inventory)),decision_counts=dict(collections.Counter(r['decision'] for r in inventory)),
    ready_to_run_physically_qualified_cases=0,selected_pair=['PMFS_E3','PMFS_B4'],new_native_tests=0,new_generations=0,new_seeds=0,new_CFD=0,
    raw_source_assets_hashed=len(unique),original_R7_D0_D1_not_overwritten=True,
    next_action='STOP_FOR_INDEPENDENT_REVIEW_NO_AUTOMATIC_TEST_OR_GENERATION')
(out/'STATIC_QUALIFICATION_DECISION.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
print(json.dumps(decision))
