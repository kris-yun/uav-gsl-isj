"""Full TRAIN-only native queries. Never opens a DEV raw frame."""
import csv,json,sys,time,subprocess
from pathlib import Path
import numpy as np
from common import PROJECT,OUT,PROTOCOL,OCC,run_path,sha,write,probes,points_for_probes,NativeQuery,decode_frame

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'INPUT_FREEZE.json').exists():raise RuntimeError('new audit already started; retain first output')
    config=json.loads(PROTOCOL.read_text())
    old=PROJECT/'results/native_20261023'
    write('INPUT_FREEZE.json',{'protocol':config,'protocol_sha256':sha(PROTOCOL),
       'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
       'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
       'code_sha256':{str(p.relative_to(PROJECT)).replace('\\','/'):sha(p) for p in Path(__file__).parent.glob('*.py')},
       'previous_frozen_files':{str(p.relative_to(PROJECT)).replace('\\','/'):sha(p) for p in
         [old/'FINAL_DECISION.json',old/'MODEL_FREEZE.json',old/'R2_RESULT.json',old/'models/secondary/operator.json',
          PROJECT/'src/gsl_discrimination/m1_opponent/calibration.py']},
       'new_training_seeds_or_worlds':False,'DEV_frame_bytes_opened':False})
    query=NativeQuery(OCC,PROJECT/'native/native_query.dll')
    pp=probes();points=points_for_probes(pp)
    positions=np.array([[float(p['center_x_m']),float(p['center_y_m']),float(p['z_m'])] for p in pp])
    from recover_assets import geometry_receipt
    geom=geometry_receipt(points)
    assert all(x['legal_free'] for x in geom)
    source_xyz=np.array([[-.6,1.95,.4],[-.4,-2.9,-.3]])
    write('GEOMETRY_AND_DISTANCE.json',{'occupancy_sha256':sha(OCC),'pool_cells':geom,
       'probe_positions_m':positions.tolist(),'source_xyz_m':source_xyz.tolist(),
       'source_to_probe_distance_3D_m':np.linalg.norm(source_xyz[:,None,:]-positions[None,:,:],axis=2).tolist(),
       'fixed_probe_legality_not_UAV_flight_safety':True})
    start=time.perf_counter();worlds=[]
    for run in config['only_TRAIN_runs_before_selection_freeze']:
        p=run_path(run)
        with (p/'RECORD_TIMELINE.tsv').open(newline='') as f:timeline=list(csv.DictReader(f,delimiter='\t'))
        with (p/'OUTPUT_SHA256SUMS.tsv').open(newline='') as f:hashes={r['name']:r for r in csv.DictReader(f,delimiter='\t')}
        times=np.array([float(r['internal_simulation_time_s']) for r in timeline])
        values=np.empty((len(timeline),30));local_wind=np.empty((len(timeline),30,3),dtype=np.float32)
        # Cache only local probe vectors, not the full true wind field.
        wind_cache={i:query.local_wind(p/'wind'/('wind_iteration_'+str(i)),points).reshape(30,4,3).mean(1) for i in range(11)}
        counts=[]
        for k,r in enumerate(timeline):
            if time.perf_counter()-start>config['maximum_extraction_wall_s']:raise TimeoutError('bounded TRAIN extraction wall limit')
            frame_path=p/('iteration_'+r['record_index']);expected=hashes[frame_path.name]
            assert frame_path.stat().st_size==int(expected['size_bytes']) and sha(frame_path)==expected['sha256']
            frame=decode_frame(frame_path)
            assert frame['wind_index']==int(r['wind_index'])
            values[k]=query.query(frame,points).reshape(30,4).mean(1,dtype=np.float64)
            local_wind[k]=wind_cache[frame['wind_index']]
            counts.append(len(frame['filaments']))
            if k%300==0:print('TRAIN_FRAME',run,k,len(timeline),'elapsed',round(time.perf_counter()-start,2),flush=True)
        target=OUT/'train_arrays'/(run+'.npz');target.parent.mkdir(exist_ok=True)
        np.savez_compressed(target,values_ppm=values,times_s=times,local_wind_mps=local_wind,
               positions_m=positions,native_filament_count=np.array(counts),
               record_index=np.array([int(r['record_index']) for r in timeline]))
        worlds.append({'run_id':run,'file':str(target.relative_to(OUT)).replace('\\','/'),'sha256':sha(target),
            'frame_count':len(timeline),'manifest_sha256':sha(p/'RUN_MANIFEST.json'),
            'timeline_sha256':sha(p/'RECORD_TIMELINE.tsv'),'all_frame_sha_matched':True,
            'source':'B' if '_s2x_' in run else 'A','repeat':int(run[-2:])})
        print('TRAIN_WORLD_DONE',run,flush=True)
    write('TRAIN_EXTRACTION_RECEIPT.json',{'status':'PASS_TRAIN_ONLY_NATIVE_EXTRACTION','worlds':worlds,
         'frames':sum(w['frame_count'] for w in worlds),'wall_s':time.perf_counter()-start,
         'scalar_probe_readings':sum(w['frame_count'] for w in worlds)*30,
         'DEV_raw_frames_read':0,'new_propagation':0,'new_ROS':0,'units':'ppm','ideal_pooled_readout':True})

if __name__=='__main__':main()
