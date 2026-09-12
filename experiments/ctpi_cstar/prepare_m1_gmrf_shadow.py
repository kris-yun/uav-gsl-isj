"""Generate native shadow inputs from map + local wind only, never gas/source fields."""
import hashlib
import json
from pathlib import Path
from m1_causal.occupancy3d import Occupancy3D

def main():
    root=Path(__file__).resolve().parents[2]
    dest=root/'evidence/cstar_m1_gmrf_shadow_inputs_20260910'
    dest.mkdir(exist_ok=False)
    manifest={'scope':'DIAGNOSTIC_NOT_C2_OR_ROS_PARITY','cadence_s':2,
              'vertical_wind':'unavailable; not filled from truth','cases':[]}
    for house in ('H01','H02','H03'):
        path=root/f'evidence/cstar_m1_maps3d_20260910/{house}.csv'
        grid=Occupancy3D.read(path)
        z=grid.index((grid.minimum[0],grid.minimum[1],.3))[2]
        nx,ny,_=grid.dimensions
        plane=grid.cells[z]
        (dest/f'{house}.map').write_text(
            f'{nx} {ny} {grid.cell_size} {grid.minimum[0]} {grid.minimum[1]}\n'+
            ' '.join('0' if v==0 else '100' for v in plane.flat)+'\n')
        for source in ('SA','SB'):
            for wind in ('fast','slow'):
                case=f'{house}_{source}_{wind}'
                hist=root/f'evidence/cstar_current_runtime_assets240_20260907/realizations/{case}/measured_history.jsonl'
                rows=[json.loads(line) for line in hist.read_text().splitlines()]
                values=[(r['t_sim_s'],*r['pose_xy'],*r['wind_uv']) for r in rows]
                (dest/f'{case}.obs').write_text(''.join(' '.join(map(str,r))+'\n' for r in values))
                manifest['cases'].append({'case':case,'map_sha256':grid.sha256,
                    'history_sha256':hashlib.sha256(hist.read_bytes()).hexdigest(),'observations':len(values),
                    'allowed_columns':['t_sim_s','pose_xy','wind_uv']})
    manifest['input_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(dest)
if __name__=='__main__': main()
