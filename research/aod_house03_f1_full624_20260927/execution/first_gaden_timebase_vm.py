#!/usr/bin/env python3
"""Exactly one first scheduled realization, followed by metadata-only time audit."""
import csv, hashlib, json, os, subprocess, time
from pathlib import Path

R=Path('/home/zyc/aod_house03_f1_full624_20260927')
TARGET_ROOT=Path('/home/zyc/ros2_ws/aod_house03_f1_full624_targets_20260927')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    freeze=json.loads((R/'PRE_TARGET_FREEZE.json').read_text());assert freeze['passed']
    for name,h in json.loads((R/'TEMPLATE_FREEZE.json').read_text())['arrays_sha256'].items():
        assert sha(R/'templates'/name)==h,name
    panel=list(csv.DictReader((R/'protocol/frozen/HOUSE03_FUTURE_GADEN_SEEDS_96.tsv').open(),delimiter='\t'))
    item=panel[0];assert item['source_id']=='pmfs_24_13' and int(item['realization_index'])==0
    run=TARGET_ROOT/'source_0_replica_0';run.mkdir(parents=True,exist_ok=False)
    real=run/'realization'  # Nonexistent new path: core cannot remove historical files.
    assert not real.exists()
    wind=list(csv.DictReader((R/'protocol/frozen/HOUSE03_WIND_HASHES_11.tsv').open(),delimiter='\t'))
    for row in wind:
        assert sha(row['preprocessed_path'])==row['preprocessed_sha256']
    wind_dir=str(Path(wind[0]['preprocessed_path']).parent)
    occ=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House03/OccupancyGrid3D.csv')
    assert sha(occ)=='ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af'
    options={
        'verbose':'false','wait_preprocessing':'false','sim_time':'510.0','time_step':'0.1',
        'num_filaments_sec':'7','variable_rate':'true','filament_stop_steps':'0',
        'ppm_filament_center':'10.0','filament_initial_std':'10.0','filament_growth_gamma':'15.0',
        'filament_noise_std':'0.01','gas_type':'10','temperature':'298.0','pressure':'1.0',
        'concentration_unit_choice':'1','occupancy3D_data':str(occ),'fixed_frame':'map',
        'wind_data':wind_dir,'wind_time_step':'1.0','allow_looping':'true',
        'loop_from_step':'1','loop_to_step':'10','source_position_x':item['x_m'],
        'source_position_y':item['y_m'],'source_position_z':item['z_m'],
        'save_results':'1','results_time_step':'0.5','results_min_time':'0.0',
        'writeConcentrations':'false','results_location':str(real)}
    binary=R/'timebase_logger/filament_simulator_timebase'
    command=[str(binary),'--ros-args']+[v for k,x in options.items() for v in ('-p',f'{k}:={x}')]
    env=dict(os.environ,GADEN_RNG_SEED=item['requested_seed'],AOD_TIME_AUDIT_DIR=str(run),
             AOD_RUN_ID='House03_pmfs_24_13_replica_0',ROS_DOMAIN_ID='229',
             OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    seeded_lib=Path('/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib/libgaden.so')
    env['LD_LIBRARY_PATH']=str(seeded_lib.parent)+':'+env.get('LD_LIBRARY_PATH','')
    linkage=subprocess.check_output(['ldd',str(binary)],env=env,text=True)
    loaded_gaden=next(line for line in linkage.splitlines() if 'libgaden.so =>' in line)
    assert loaded_gaden.split('=>',1)[1].strip().split()[0]==str(seeded_lib)
    build_provenance=json.loads((R/'timebase_logger/LOGGER_BUILD_PROVENANCE.json').read_text())
    assert sha(seeded_lib)==build_provenance['seeded_numerical_library_sha256']
    start=time.monotonic()
    (run/'RUN_CONFIGURATION.json').write_text(json.dumps(dict(manifest_row=item,options=options,
        command=command,pre_target_freeze=freeze,binary_sha256=sha(binary),wind_hashes=wind,
        runtime_ld_library_path=env['LD_LIBRARY_PATH'],runtime_linkage=linkage,
        runtime_seeded_numerical_library_sha256=sha(seeded_lib),
        concentration_values_read=False),indent=2)+'\n')
    with (run/'generation.log').open('w') as log:
        subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert 'Filament simulator finished correctly!' in (run/'generation.log').read_text()
    # No iteration content, filament coordinates, concentration or gas arrays read.
    times=list(csv.DictReader((run/'RESULT_TIME_MAP.tsv').open(),delimiter='\t'))
    release=list(csv.DictReader((run/'RELEASE_TIME_METADATA.tsv').open(),delimiter='\t'))
    enabled=next(r for r in release if r['event']=='release_enabled_first_step')
    actual=next((r for r in release if r['event']=='first_nonzero_filament_count'),None)
    checks=[]
    for t in range(50,501,50):
        match=[r for r in times if abs(float(r['physical_sim_time_s'])-t)<=1e-9]
        nearest=min(times,key=lambda r:abs(float(r['physical_sim_time_s'])-t))
        checks.append(dict(required_time_s=t,exact_match_count=len(match),match=match,
            nearest_writer_metadata_only=nearest,
            nearest_absolute_error_s=abs(float(nearest['physical_sim_time_s'])-t)))
    enabled_zero=abs(float(enabled['physical_sim_time_s']))<=1e-9
    actual_zero=actual is not None and abs(float(actual['physical_sim_time_s']))<=1e-9
    slots_ok=all(c['exact_match_count']==1 for c in checks)
    passed=enabled_zero and actual_zero and slots_ok
    audit=dict(passed=passed,decision='TIMEBASE_METADATA_VALID' if passed else 'AOD_F1_HOLD_TIMEBASE',
        actual_gaden_run_count=1,planned_gaden_run_count=96,wall_seconds=time.monotonic()-start,
        release_enabled=enabled,first_actual_nonzero_filament_metadata=actual,
        release_enabled_at_zero=enabled_zero,actual_emission_at_zero=actual_zero,
        all_ten_exact_writer_times_present=slots_ok,slot_checks=checks,writer_record_count=len(times),
        last_writer_time_s=float(times[-1]['physical_sim_time_s']),
        result_time_map_sha256=sha(run/'RESULT_TIME_MAP.tsv'),release_metadata_sha256=sha(run/'RELEASE_TIME_METADATA.tsv'),
        concentration_values_read=False,concentration_extraction_executed=False,
        nearest_metadata_not_used_as_observations=True,run_directory=str(run))
    (R/'TIMEBASE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2),flush=True)
    if not passed:raise SystemExit(10)

if __name__=='__main__':main()
