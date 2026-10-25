"""Freeze bounded same-kernel causal isolation after the oracle-only result."""
from pathlib import Path
import datetime,hashlib,json,shutil

B=Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024')
P=B/'outputs/E3_CAUSAL_PAIR_20261025';W=B/'outputs/E3_HORIZONTAL_WIND_ORACLE_20261025'
O=B/'outputs/E3_TRANSPORT_CAUSE_20261025'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not O.exists(),'Do not overwrite first evidence'
    O.mkdir();(O/'inputs').mkdir()
    prior=load(P/'PREREGISTERED_CAUSAL_CONTRACT.json');plan=dict(identity='E3_SAME_GADEN_KERNEL_TRANSPORT_CAUSE_20261025',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit='02ba595f07e03b46c3f63a7e6702c7f8f19d21c9',
        authority='User: continue until the cause is found; preserve frozen O24 and prior evidence',
        scope='bounded offline source-pair causal diagnostics, not ROS, a new dataset, or main-innovation validation',
        discovered_boundary_issue='Original coordsToIndices truncates negative fractional coordinates toward0. Slightly out-of-domain centers can pass native index-bounds tests. Native fidelity is not physical validity.',
        control='First exactly reproduce original true_r0 all604archived queries under the unchanged original-index mode',
        stage1_arms=['original_bounds_full3d','strict_bounds_full3d','strict_bounds_plane'],
        stage1_interventions=dict(original_bounds_full3d='untouched original GADEN transport, native RNG initialization adapted exactly as prior',strict_bounds_full3d='only coordsToIndices uses floor; existing native OutOfBounds collision response otherwise unchanged',strict_bounds_plane='same strict kernel, force newPosition.z to source0.7m after drawing all3noise components; horizontal advection,3D fine collision map,release,mass,growth,clock andPID readout unchanged'),
        physical_parameters=dict(source_height_m=.7,gas_type=10,gas='butane',dt_s=.1,release_filaments_per_s=10,sigma_initial_cm=10,gamma_cm2_per_s=15,noise_input=.015,noise_effective=.15,temperature_K=298,pressure_atm=1,duration_s=240),
        wind='same original full fine3D wind file for every matched-kernel arm; oracle-only diagnostic privilege, not deployment input',
        prediction_streams=prior['prediction_streams'],
        RNG='Use already preregistered prediction cache_seed_words for Gaussian MT seed_seq and uniform_seed as its one-word MT seed_seq. No target-world seeds enter candidate predictions. Same initial engines within each paired source/stream; consume xyznoise even in plane. After survival differs, later per-particle noise assignment need not stay matched.',
        sources=dict(true=[-4.,-1.9,.7],rival=[-2.375,-4.875,.7]),
        target='existing4actual paired physical worlds and untouched original E3; source labels are evaluation only',
        endpoints=['source pair rankings on untouched observed65windows','per-window ppm and0.1ppm event recovery at critical8to13','exact boundary-plane intervention, state bounds, gas heights and source-evidence differences','all normal/negative contrasts andcost'],
        adaptive_stage2=dict(if_full3d_has_more_positive_late_windows_than_plane_in_both_prediction_streams=['strict_bounds_no_vertical_wind','strict_bounds_no_buoyancy'],otherwise=['strict_bounds_plane_coarse_wind','strict_bounds_plane_native_noise'],purpose='isolate vertical mechanism, or fine-horizontal wind/noise discrepancy. No position, source, threshold, duration or seed search'),
        max_initial_candidate_calls=12,max_additional_candidate_calls=8,engineering_original_exact_replays=1,
        limits=dict(total_execution_wall_s=900,child_CPU_s=120,new_output_bytes=134217728,sequential=True),
        output='query-only independent candidate forward computations; save at most13anchor states per call, no full world archive',
        no_overwrite=True,no_ROS=True,no_new_neural_module=True,stop='Stop after the preregistered finite stage; do not claim a unique cause if effects are mixed or unqualified.')
    put(O/'PREREGISTERED_CAUSAL_CONTRACT.json',plan)
    for name in ['QUERIES.csv','UNIQUE_POINTS.csv']:shutil.copy2(P/'schedule'/name,O/'inputs'/name)
    for origin,name in [(P/'native_runtime/OccupancyGrid3D.csv','OccupancyGrid3D.csv'),(P/'original_E3_decomposition/saved_world/wind/wind_iteration_0','wind_iteration_0'),(P/'PHYSICAL_WINDOWS.csv','TARGET_PHYSICAL_WINDOWS.csv'),(P/'worlds/true_r0/TASK.json','ORIGINAL_REPLAY_TASK.json'),(P/'worlds/true_r0/RESPONSES.csv','ORIGINAL_REPLAY_EXPECTED.csv')]:shutil.copy2(origin,O/'inputs'/name)
    put(O/'INPUT_SHA256.json',[dict(path=p.relative_to(O).as_posix(),sha256=sha(p)) for p in sorted((O/'inputs').iterdir())])
    print('PREREGISTERED_SAME_KERNEL_CAUSE',flush=True)

if __name__=='__main__':main()
