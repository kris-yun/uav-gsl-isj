"""Validate transferred native estimated fields; not their prediction accuracy."""
import hashlib
import json
from pathlib import Path
from m1_causal.occupancy3d import Occupancy3D
from m1_causal.estimated_wind_history import EstimatedWindHistory

def main():
    root=Path(__file__).resolve().parents[2]
    folder=root/'evidence/cstar_m1_gmrf_aligned_complete_20260910'
    for line in (folder/'outputs.sha256').read_text().splitlines():
        digest,name=line.split(maxsplit=1)
        p=folder/Path(name).name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,p
    cases=[]
    for house in ('H01','H02','H03'):
        grid=Occupancy3D.read(root/f'evidence/cstar_m1_maps3d_20260910/{house}.csv')
        for wind in ('fast','slow'):
            name=f'{house}_SA_{wind}'
            h=EstimatedWindHistory.read(folder/f'{name}.txt',origin_xy=grid.minimum[:2],cell_size=grid.cell_size,expected_end_s=240)
            log=(folder/f'{name}.log').read_text()
            assert 'frames=120 accepted=1200 rejected=0 final_s=240' in log
            assert (folder/f'{name}.txt.rejected').stat().st_size==0
            assert all(grid.is_free((*xy,.3)) for xy in h.centres)
            cases.append({'case':name,'sha256':h.sha256,'frames':len(h.times),'cells':len(h.centres),
                'converged':log.count('MAP Converged at iteration'),'not_converged':log.count('did not converge'),
                'diverged':log.count('MAP Diverged')})
    result={'status':'TRANSFER_AND_INPUT_CONTRACT_PASS_NOT_ACCURACY_OR_CLOSED_LOOP','cases':cases}
    with (root/'evidence/cstar_m1_aligned_wind_complete_audit_20260910.json').open('x') as f:
        json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
