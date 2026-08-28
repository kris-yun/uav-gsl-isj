#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pf_dei_observation_contract import (
    reconstruct_completed_blocks, validate_forward_payload,
    reject_occupancy_as_main_observation,
)


def must_fail(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def main():
    t=np.arange(40,dtype=float)*0.2
    m=np.concatenate([
        np.linspace(0.0,0.9,10),
        np.linspace(1.1,2.0,10),
        np.linspace(0.1,0.5,10),
        np.linspace(2.0,3.0,10),
    ])
    idx=[range(0,10),range(10,20),range(20,30),range(30,40)]
    th=1.0
    hit=[False,True,False,True]
    blocks=reconstruct_completed_blocks(t,m,idx,th,hit,10)
    assert [b.hit for b in blocks]==hit
    must_fail(lambda: reconstruct_completed_blocks(t,m,idx,th,[True,True,False,True],10))
    must_fail(lambda: reconstruct_completed_blocks(t,m,[range(0,10),range(9,19)],th,[False,True],10))

    payload={
        'sample_time':np.arange(8,dtype=float)*0.2,
        'physical_concentration_ppm':np.ones((3,4,8),dtype=float),
        'simulated_measured_ppm':np.ones((3,4,8),dtype=float)*0.8,
        'source_xy':np.zeros((3,2),dtype=float),
        'transport_keys':['m0','m1','m2','m3'],
        'sensor_model_hash':'abc','sensor_parameter_hash':'def',
        'concentration_origin':'native_gaden_physical_concentration',
        'sensor_state_scope':'run_persistent','context_state_reset':False,
        'source_truth_used':False,
    }
    assert validate_forward_payload(payload)
    bad=dict(payload); bad['context_state_reset']=True
    must_fail(lambda: validate_forward_payload(bad))
    bad2=dict(payload); bad2['concentration_origin']='empirical_occupancy_mapping'
    must_fail(lambda: validate_forward_payload(bad2))
    must_fail(lambda: reject_occupancy_as_main_observation({'occupancy_words':np.ones(10)}))
    assert reject_occupancy_as_main_observation(payload)
    print('PF_DEI_OBSERVATION_OPERATOR_CONTRACT_SELFTEST PASS')


if __name__=='__main__':
    main()
