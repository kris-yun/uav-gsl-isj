"""Actual JSONL fixed-probe native archive component, deliberately not UAV control.

Use --run from the exact eight-world allowlist. describe does not claim the
full gsl-action-bridge-1 safety/dynamics contract. execute returns observations
only after the requested frozen interval was consumed; duplicate use is refused.
"""
import argparse,csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from reader import NativeQuery,NativeWorldExecutor
from recover_assets import ROOT,OUT,OCC,PROTO,run_path
from gsl_discrimination.data import SynchronousBlock

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();root=run_path(args.run)
    with (root/'RECORD_TIMELINE.tsv').open(newline='') as f:timeline=list(csv.DictReader(f,delimiter='\t'))
    query=NativeQuery(OCC,ROOT/'native/native_query.dll')
    backend=NativeWorldExecutor(root,query,timeline)
    prototype=SynchronousBlock.load_npz(OUT/'blocks'/(args.run+'.npz'))
    import numpy as np
    geometry=json.loads((OUT/'GEOMETRY_QUALIFICATION.json').read_text())
    points=np.array([r['point_m'] for r in geometry['receivers']],dtype=np.float32)
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    for line in sys.stdin:
        request=json.loads(line)
        try:
            if request['method']=='describe':
                result={'schema':'gsl-native-fixed-probe-component-1','scope':'IDEAL_NATIVE_ARCHIVE_QUERY_ONLY',
                  'source_label_exposed':False,'future_truth_available_to_policy':False,
                  'fixed_geometry':prototype.positions_m.tolist(),'motion_controller_qualified':False,
                  'original_fast_filter_qualified':False,'available_action_count':1}
            elif request['method']=='execute':
                if request.get('action')!=0:raise ValueError('only preregistered fixed paired-probe action 0 is available')
                ids=[i for i,r in enumerate(timeline) if 50<=float(r['internal_simulation_time_s'])<=70]
                sampled=backend.observe(ids,points)
                opaque=hashlib.sha256(args.run.encode()).hexdigest()[:16]
                block=SynchronousBlock(sampled['values'].reshape(len(ids),2,4).mean(2,dtype=np.float64),
                    sampled['times_s'],prototype.positions_m,prototype.sensor_ids,prototype.qualification,
                    opaque+':executed50_70',opaque,'ppm',
                    sampled['local_wind_mps'].reshape(len(ids),2,4,3).mean(2,dtype=np.float64),
                    metadata={'hardware_sensor':False,'active_motion':False,'truth_included':False})
                path=output/(opaque+'.npz');block.save_npz(path)
                result={'schema':'gsl-native-fixed-probe-execution-1','block_path':str(path.resolve()),
                   'actual_interval_s':[float(sampled['times_s'][0]),float(sampled['times_s'][-1])],
                   'scalar_readings':len(ids)*2,'scope':'fixed simultaneous probes, not active UAV flight'}
            else:raise ValueError('unknown method')
            reply={'id':request['id'],'result':result}
        except Exception as exc:reply={'id':request.get('id'),'error':str(exc)}
        print(json.dumps(reply),flush=True)

if __name__=='__main__':main()
