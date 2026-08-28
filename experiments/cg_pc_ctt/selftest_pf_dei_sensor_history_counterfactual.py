#!/usr/bin/env python3
from __future__ import annotations

from pf_dei_sensor_history_counterfactual import analyze


def arm(sid, hid, measured):
    rows=[]
    for i,(c,m) in enumerate(zip([1.0,1.0,1.0,1.0],measured)):
        rows.append({
            'scenario_id':sid,'history_id':hid,'phase':'evaluation',
            'sim_time':str(10.0+0.2*i),'physical_concentration_ppm':str(c),
            'measured_gas_ppm':str(m),'threshold_gas':'0.5'
        })
    return rows


def main():
    same = arm('same','clean',[0.8,0.9,0.95,0.98]) + arm('same','high',[0.8,0.9,0.95,0.98])
    r0=analyze(same,1e-12)
    assert not r0['local_stop_observation_falsified']

    diff = arm('memory','clean',[0.2,0.3,0.4,0.45]) + arm('memory','high',[1.4,1.2,1.0,0.8])
    r1=analyze(diff,1e-12)
    assert r1['local_stop_observation_falsified']
    assert r1['history_effect_active_scenarios']==1
    print('PF_DEI_SENSOR_HISTORY_COUNTERFACTUAL_SELFTEST PASS')


if __name__=='__main__':
    main()
