#!/usr/bin/env python3
"""Already-open H01/H02 scoring regression, no forward or House03 gas access."""
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
R=Path('/home/zyc/aod_house03_f1_full624_20260927')
sys.path.insert(0,str(R/'amplitude_implementation'))
from amplitude_readout import AmplitudeTemplates, Arm, ranking
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    manifest=json.loads((R/'open_regression/SHA_INPUTS.json').read_text())
    for name,h in manifest.items():assert sha(R/'open_regression'/name)==h,name
    d0=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
    targets=np.load(d0/'protocol/JTD_E2_FRESH_TARGET_10x30.npy')
    original=pd.read_csv(R/'open_regression/posthoc_readout_factorial_candidates.csv')
    original_targets=pd.read_csv(R/'open_regression/posthoc_readout_factorial_targets.csv')
    max_sse=0.;max_gain=0.
    with np.load(R/'open_regression/amplitude_templates.npz') as arrays:
        for e in range(3):
            for arm in Arm:
                pred=arrays[f'env_{e}_{arm.value}']
                bank=AmplitudeTemplates(arm,pred[:,0,:],pred)
                for s in range(6):
                    for j in range(4):
                        sse,gain=bank.score(targets[e,s,j])
                        old=original[(original.env==e)&(original.source==s)&(original.target==j)&(original.arm==arm.value)].sort_values('candidate')
                        assert np.allclose(sse,old.sse.to_numpy(),rtol=1e-12,atol=1e-12)
                        assert np.allclose(gain,old.scale.to_numpy(),rtol=1e-12,atol=1e-12)
                        max_sse=max(max_sse,float(np.max(abs(sse-old.sse.to_numpy()))))
                        max_gain=max(max_gain,float(np.max(abs(gain-old.scale.to_numpy()))))
                        oldtarget=original_targets[(original_targets.env==e)&(original_targets.source==s)&(original_targets.target==j)&(original_targets.arm==arm.value)].iloc[0]
                        rank,unique=ranking(sse,s)
                        assert rank==oldtarget['rank'] and unique==oldtarget.unique_top1
    report=dict(passed=True,existing_open_environments=3,existing_open_targets=72,arms=4,
        max_absolute_sse_deviation=max_sse,max_absolute_gain_deviation=max_gain,
        all_ranks_and_unique_top1_equal=True,house03_gas_read=False,new_forward_runs=0,
        source_amplitude_module_sha256=sha(R/'amplitude_implementation/amplitude_readout.py'),
        archived_native_parity=json.loads((d0/'NATIVE_PARITY.json').read_text()))
    assert report['archived_native_parity']['pass']
    (R/'OPEN_IMPLEMENTATION_REGRESSION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
