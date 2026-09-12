"""Independent local audit of native numerical/rejection diagnostics."""
import hashlib
import json
from pathlib import Path
import numpy as np
from m1_causal.occupancy3d import Occupancy3D

def main():
    root=Path(__file__).resolve().parents[2]
    old=root/'evidence/cstar_m1_gmrf_shadow_results_20260910'
    new=root/'evidence/cstar_m1_gmrf_numerical_20260910'
    result={'verdict':'INPUT_DIAGNOSTIC_NOT_M1_UTILITY','cases':[]}
    for path in sorted(new.glob('*.txt')):
        case=path.stem
        grid=Occupancy3D.read(root/f'evidence/cstar_m1_maps3d_20260910/{case[:3]}.csv')
        a=np.loadtxt(old/path.name); b=np.loadtxt(path)
        assert a.shape==b.shape and np.array_equal(a[:,:3],b[:,:3])
        assert np.isfinite(b).all()
        rejected=np.loadtxt(str(path)+'.rejected',ndmin=2)
        log=path.with_suffix('.log').read_text()
        states=[grid.state((x,y,.3)) for t,x,y in rejected]
        result['cases'].append({'case':case,'snapshots':len(np.unique(b[:,0])),
            'converged_messages':log.count('MAP Converged at iteration'),
            'not_converged_messages':log.count('did not converge'),
            'diverged_messages':log.count('MAP Diverged'),
            'rejections':len(rejected),'rejected_but_original_voxel_free':states.count(0),
            'rejected_original_states':{str(s):states.count(s) for s in set(states)},
            'component_rms_difference_20_vs_1':float(np.sqrt(np.mean((a[:,3:]-b[:,3:])**2))),
            'max_abs_difference_20_vs_1':float(np.max(np.abs(a[:,3:]-b[:,3:]))),
            'field_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'log_sha256':hashlib.sha256(path.with_suffix('.log').read_bytes()).hexdigest()})
    output=root/'evidence/cstar_m1_gmrf_numerical_audit_20260910.json'
    with output.open('x') as f: json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
