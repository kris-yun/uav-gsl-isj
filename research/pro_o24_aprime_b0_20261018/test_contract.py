#!/usr/bin/env python3
"""Executable synthetic unit tests. These are NOT empirical UAV results."""
import dataclasses
import numpy as np
from mechanism_probe import pilot_report
from identifiability import pairwise_identifiability
from response_contract import (ResponseProvenance,ObservationContract,
    ResponseBank,QualificationError,posterior_ppm_gaussian,check_physical_contract)


def expect_raises(fn, message):
    try:fn()
    except QualificationError:return
    raise AssertionError('Contract failed to reject: '+message)


def fixture():
    identity=ResponseProvenance('toy_scene','measured_or_estimated','analytic_toy_forward',
        'mg/s','calibrated_linear_ppm','s_from_release','toy_sensor_v1',
        'toy_config','toy_wind')
    obs=ObservationContract(('w0','w1','w2'),np.array([0.,1.,2.]),
        np.array([[0.,0.,.5],[1.,0.,.5],[2.,0.,.5]]),
        np.array([2.,0.5,0.]),np.array([.1,.1,.1]),identity)
    bank=ResponseBank(('w0','w1','w2'),
        np.array([[2.,0.],[.5,1.],[0.,2.]]),
        np.array([[1.,0.],[2.,0.]]),np.array([1.,1.]),identity,('source0','source1'))
    return obs,bank


def main():
    obs,bank=fixture();known=posterior_ppm_gaussian(obs,bank,source_release=1.)
    assert known.probability[0]>.9999 and np.isclose(known.probability.sum(),1.)
    prof=posterior_ppm_gaussian(obs,bank)
    assert prof.probability[0]>.9999 and np.isclose(prof.estimated_release[0],1.)
    expect_raises(lambda:posterior_ppm_gaussian(obs,dataclasses.replace(bank,response_kind='native_2d_hit_frequency')),'hit-to-ppm swapping')
    expect_raises(lambda:posterior_ppm_gaussian(obs,dataclasses.replace(bank,window_ids=('w1','w0','w2'))),'clock/window mismatch')
    expect_raises(lambda:posterior_ppm_gaussian(obs,dataclasses.replace(bank,provenance=dataclasses.replace(bank.provenance,wind_input='truth_offline_oracle'))),'different physical wind')
    o=dataclasses.replace(obs,provenance=dataclasses.replace(obs.provenance,wind_input='truth_offline_oracle'))
    b=dataclasses.replace(bank,provenance=o.provenance)
    expect_raises(lambda:posterior_ppm_gaussian(o,b),'test truth not allowed online')
    assert posterior_ppm_gaussian(o,b,deployment=False).probability[0]>.9999
    expect_raises(lambda:posterior_ppm_gaussian(obs,dataclasses.replace(bank,source_ids=('x','x'))),'fake second source')
    expect_raises(lambda:posterior_ppm_gaussian(obs,dataclasses.replace(bank,response_ppm_per_unit_release=-bank.response_ppm_per_unit_release)),'negative unphysical response')
    expect_raises(lambda:posterior_ppm_gaussian(obs,dataclasses.replace(bank,response_ppm_per_unit_release=bank.response_ppm_per_unit_release[:2,:])),'dimension mismatch')
    pairs=pairwise_identifiability(obs,bank);assert len(pairs)==1 and pairs[0]['unknown_amplitude_ray_sine']>.1
    same_bank=dataclasses.replace(bank,response_ppm_per_unit_release=np.column_stack([bank.response_ppm_per_unit_release[:,0],2*bank.response_ppm_per_unit_release[:,0]]))
    same_pairs=pairwise_identifiability(obs,same_bank)
    assert same_pairs[0]['structural_non_identifiable'] and same_pairs[0]['known_amplitude_whitened_separation']>0
    p=pilot_report(); assert p['ordinary_comparators']['raw_POD_rank1']['contrast_retained_fraction']<.02
    assert np.isclose(p['ordinary_comparators']['centered_POD_rank1']['contrast_retained_fraction'],1.)
    print('PASS: 10 synthetic contract + nuisance positive-profile + strong-POD checks, not empirical source localization')

if __name__=='__main__':main()
