"""Multi-UAV adaptation of the saved V34 *ordinary* CausalLocalPuffs model.

This preserves the historical V34 source-conditioned local-wind reconstruction;
its use is a shared ordinary baseline, never claimed a novel gas transport model
or validated full S2 native source-conditioned forward. Experimental errors
may make it unusable; run source-coverage audits before claiming localization.
"""
from __future__ import annotations
import numpy as np
from .legacy_v34.continuous_baseline import CompiledLocalPuffs
from .types import Reading


class LegacyV34MultiUAV:
    def __init__(self, q_reference_mol_s=1e-3,air_mol_m3=41.0,mode=0):
        self.physics={'Q_mol_s':q_reference_mol_s,'air_mol_m3':air_mol_m3}
        self.mode=int(mode)
        if self.mode not in (0,1):raise ValueError('unsupported V34 wind mode')
        if self.physics['air_mol_m3']<=0 or q_reference_mol_s<=0:raise ValueError('invalid physics')
        self.calls=0

    def response(self, sources, observations):
        sources=np.asarray(sources,float)
        n=len(observations[0].pos); t=len(observations)
        if t==1:return np.zeros((len(sources),1,n),float)
        times=np.asarray([o.t for o in observations])
        if not np.allclose(np.diff(times),1.0,atol=1e-7):
            raise ValueError('V34 kernel requires exactly 1 Hz causal prefix')
        out=np.zeros((len(sources),t,n),float)
        # No shared sensor state: compile each UAV's actual pose/wind history.
        for i in range(n):
            records=[{'tick':10*j,'position_ENU_m':o.pos[i].tolist(),
                      'local_wind_m_s':o.wind[i].tolist()} for j,o in enumerate(observations)]
            compiled=CompiledLocalPuffs(records,self.physics)
            for k,s in enumerate(sources):
                out[k,:,i]=compiled.prediction(s,self.mode,'lag2_tau1')
                self.calls+=1
        return np.maximum(out,0.)