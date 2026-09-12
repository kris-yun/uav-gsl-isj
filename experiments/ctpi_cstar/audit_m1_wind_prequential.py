"""Source-blind next-observation wind check, no parameter fitting or tuning.

Evaluate each field strictly BEFORE the observation timestamp so its own
measurement cannot already have been inserted. Local checks do not validate
unvisited-source transport or unknown vertical flow.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from m1_causal.occupancy3d import Occupancy3D
from m1_causal.estimated_wind_history import EstimatedWindHistory

def main():
    root=Path(__file__).resolve().parents[2]
    output=root/'evidence/cstar_m1_wind_prequential_20260911.json'
    if output.exists(): raise FileExistsError(output)
    result={'verdict':'DIAGNOSTIC_NOT_SOURCE_ACCURACY','cases':[]}
    for house in ('H01','H02','H03'):
        grid=Occupancy3D.read(root/f'evidence/cstar_m1_maps3d_20260910/{house}.csv')
        for regime in ('fast','slow'):
            name=f'{house}_SA_{regime}'
            h=EstimatedWindHistory.read(root/f'evidence/cstar_m1_gmrf_aligned_complete_20260910/{name}.txt',origin_xy=grid.minimum[:2],cell_size=grid.cell_size,expected_end_s=240)
            path=root/f'evidence/cstar_current_runtime_assets240_20260907/realizations/{name}/measured_history.jsonl'
            rows=[json.loads(s) for s in path.read_text().splitlines()]
            predictions=[];observed=[];last=[];failed=[];prev=None
            for row in rows:
                now=float(row['t_sim_s']); uv=np.asarray(row['wind_uv'])
                if prev is not None:
                    field=h.snapshot_at(np.nextafter(now,-np.inf),vertical_model='planar_extrusion_zero_vertical',initial_velocity_m_s=(0,0,0))
                    assert field.available_s<now
                    try:
                        pred=field.velocity_m_s((*row['pose_xy'],.3))[:2]
                        predictions.append(pred);observed.append(uv);last.append(prev)
                    except ValueError as e: failed.append({'t':now,'error':str(e)})
                prev=uv
            a,y,b=map(np.asarray,(predictions,observed,last))
            item={'case':name,'scored':len(y),'failures':failed,'wind_sha256':h.sha256,
                'history_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'gmrf_component_rmse':float(np.sqrt(np.mean((a-y)**2))),
                'last_local_observation_rmse':float(np.sqrt(np.mean((b-y)**2))),
                'zero_prior_rmse':float(np.sqrt(np.mean(y*y))),
                'error_norm_p95':float(np.quantile(np.linalg.norm(a-y,axis=1),.95)),
                'limitation':'same-route local wind diagnostic; no independent off-route or 3D coverage'}
            result['cases'].append(item); print(name,item['gmrf_component_rmse'],item['last_local_observation_rmse'],flush=True)
    with output.open('x') as f: json.dump(result,f,indent=2)
if __name__=='__main__': main()
