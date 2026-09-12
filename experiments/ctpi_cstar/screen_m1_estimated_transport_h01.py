"""Existing-data integration diagnostic, not utility or calibrated C2 evidence.

Two pre-existing oracle-supported candidates; no full-map localization claim.
No measured gas is supplied to forward dynamics. dt=.1 matches producer.
"""
import hashlib
import json
import math
import argparse
from pathlib import Path
from m1_causal.occupancy3d import Occupancy3D
from m1_causal.filament_geometry import FilamentGeometry
from m1_causal.estimated_wind_history import EstimatedWindHistory
from m1_causal.filament_transport import FixedSourceMember,TransportConfig
from m1_causal.filament_observation import concentration_ppm
from m1_causal.counterfactual_likelihood import FopdtConfig,fopdt_response

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--horizon',type=int,choices=(60,240),default=240)
    parser.add_argument('--candidate',choices=('both','SA','SB'),default='both')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    suffix='' if args.candidate=='both' else f'_{args.candidate}_trace_v3'
    out=root/f'evidence/cstar_m1_estimated_transport_h01_screen_{args.horizon}s{suffix}_20260910.json'
    if out.exists(): raise FileExistsError(out)
    grid=Occupancy3D.read(root/'evidence/cstar_m1_maps3d_20260910/H01.csv')
    geometry=FilamentGeometry(grid)
    wind=EstimatedWindHistory.read(root/'evidence/cstar_m1_gmrf_aligned_valid_20260910/H01_SA_fast.txt',
        origin_xy=grid.minimum[:2],cell_size=grid.cell_size,expected_end_s=240)
    path=root/'evidence/cstar_current_runtime_assets240_20260907/realizations/H01_SA_fast/measured_history.jsonl'
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    rows=[r for r in rows if r['t_sim_s']<=args.horizon]
    density=1/(82.057338*298)
    mass=10/1e6*density*(2*math.pi)**1.5*10**3
    config=TransportConfig(.1,7,mass,10,15,.01,density,2.0061)
    result={'verdict':'INTEGRATION_DIAGNOSTIC_NOT_UTILITY','map_sha256':grid.sha256,
       'wind_sha256':wind.sha256,'history_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'closure':'planar_extrusion_zero_vertical','initial_wind':[0,0,0],
       'emission':'deterministic 7/s point; differs from variable-rate producer',
       'candidates':[]}
    result['code_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__),*sorted((Path(__file__).parent/'m1_causal').glob('*.py'))]}
    for name,source in [('SA',(-.6,1.95,.4)),('SB',(-.4,-2.9,-.3))]:
        if args.candidate!='both' and name!=args.candidate: continue
        item={'candidate':name,'source_m':source,'times':[],'concentration_ppm':[]}
        model=FixedSourceMember(candidate_id=name,member_id='shared0',source_m=source,config=config,
           seed=1234,is_free=grid.is_free,step_boundary=geometry.step_boundary)
        try:
            for row in rows:
                # Intermediate sensor pose does not affect plume evolution;
                # concentrations are queried only at the recorded .2 s poses.
                pose=(*row['pose_xy'],.3)
                for _ in range(2):
                    snapshot=wind.snapshot_at(model.time_s,vertical_model=result['closure'],initial_velocity_m_s=(0,0,0))
                    frame=model.advance(wind=snapshot,sensor_pose_m=pose)
                item['times'].append(frame.stamp_s)
                item['concentration_ppm'].append(concentration_ppm(frame.filaments,pose,
                    air_moles_per_cm3=density,visible=geometry.visible))
            item['status']='PREFIX_COMPLETE'
            item['sensor_ppm']=fopdt_response(item['times'],item['concentration_ppm'],FopdtConfig(1.2,.4))
        except ValueError as e:
            item['status']='MODEL_INPUT_FAILURE';item['error']=str(e);item['failed_at_s']=model.time_s
        result['candidates'].append(item)
        print(name,item['status'],item.get('failed_at_s',args.horizon),flush=True)
    with out.open('x') as f: json.dump(result,f,indent=2)
    print(out)
if __name__=='__main__': main()
