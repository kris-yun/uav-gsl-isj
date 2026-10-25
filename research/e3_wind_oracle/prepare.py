"""Freeze one horizontal-wind oracle diagnostic before forward results."""
from pathlib import Path
import datetime,hashlib,json,shutil

B=Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024')
P=B/'outputs/E3_CAUSAL_PAIR_20261025'
H=B/'outputs/E3_HISTORY_SUPPORT_20261025'
O=B/'outputs/E3_HORIZONTAL_WIND_ORACLE_20261025'

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not O.exists(),'NEVER_OVERWRITE_FIRST_RESULTS'
    O.mkdir();(O/'inputs').mkdir()
    plan=load(H/'PREREGISTERED_HISTORY_CONTRACT.json')
    contract=dict(identity='E3_FIXED220_HORIZONTAL_ORACLE_ONLY_20261025',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit='d6295dc942a32e39711204a4d2c9ad07ae686fa6',baseline_commit='631145657461c41840f6844f118de57d1e747ea4',
        hypothesis='Whether replacing only local GMRF horizontal wind by the archived physical-world reference slice rescues the locked source pair under identical fixed220warmup/2D transport',
        diagnostic_oracle_not_deployable=True,new_physical_worlds=0,new_ROS=0,neural_training=0,
        wind=dict(source='original E3 single loaded native wind_iteration_0',sha256='135690ce4679f43bb02d7d40fe39b338a250f2aa94cf3e71d0f2dbf8bbe4705a',
            projection='At each of all44x48 native PMFS coarse-cell centers, call the actual GADEN Environment coordsToIndices at the fixed common candidate height0.7m and sample native WindSequence; use u,v only. No averaging, filling, smoothing, scaling, source-specific editing, or new height search.',
            height_m=.7,vertical_component='audited but never supplied to2D predictor',
            geometry='both native2D occupancy and3D PID readout occupancy unchanged; source/query cells must be physically free; other coarse/3D center state mismatches reported, never repaired'),
        constants=dict(history_s=220,warmup_dt=.2,record_dt=.1,record_steps=200,noise=.5,D=.2,PID_threshold_ppm=.1),sources=plan['E3_sources'],prediction_streams=plan['prediction_streams'],
        shared_randomness='reuse exactly existing cache/uniform initial states; changed wind changes later survival/draw consumption, not claimed identical physical trajectories',
        qualification='native parser and independent raw float32 decoder agree at all coarse centers; coords/index/unit/source-height checks; exact GMRF control map andRNG replay before oracle',
        limits=dict(total_execution_wall_s=900,child_CPU_s=120,new_scientific_output_bytes=134217728,sequential=True),
        calls=dict(existing_GMRF_long220_exact_replays=4,new_oracle_point_forwards=4),
        endpoints=['true-source response at frozen8to13stations','source-pair signed compatibility and ranks on all4existing real worlds','native full-observation-map point-candidate score ratios','all source/prediction contrasts and costs'],
        full_map_scope='no new1132cell posterior or closed-loop localization claim',
        stop='Stop after this wind-only contrast. Do not auto-start3D armC, tune slice, alter history or noise, or add seeds.')
    put(O/'PREREGISTERED_WIND_CONTRACT.json',contract)
    for name in ['E3_scene.json','E3_CONSTANTS.json','E3_UNIQUE_POINTS.csv','pred_r0.cache.f32','pred_r1.cache.f32']:
        shutil.copy2(H/'inputs'/name,O/'inputs'/name)
    wind=P/'original_E3_decomposition/saved_world/wind/wind_iteration_0';assert sha(wind)==contract['wind']['sha256'];shutil.copy2(wind,O/'inputs/wind_iteration_0')
    shutil.copy2(P/'native_runtime/OccupancyGrid3D.csv',O/'inputs/OccupancyGrid3D.csv')
    for source in ['true','rival']:
        for pred in plan['prediction_streams']:
            for ext in ['spec.json','json','f32']:
                name=f'E3_{source}_{pred["id"]}_long220.{ext}';shutil.copy2(H/'runs'/name,O/'inputs'/('control_'+name))
    put(O/'INPUT_SHA256.json',[dict(path=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((O/'inputs').iterdir())])
    print('PREREGISTERED_WIND_ORACLE',flush=True)

if __name__=='__main__':main()
