"""Tests for real algorithm code, deliberately excluding source-label metrics."""
from __future__ import annotations
from dataclasses import replace
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v41_flowolf import (Reading,Configuration,GaussianAdvectionDemo,Controller,
                           encode,joint_posterior,LegacyV34MultiUAV)
from v41_flowolf.control import _project_source_information,_safe_velocity,OpenGeometry,all_actions
from v41_flowolf.native import check_root


def obs(t=0,gas=(.1,.1,.1),wind=(1.,0.,0.),pos=None):
    p=np.array([[10.,-5.,10.],[10.,0.,10.],[10.,5.,10.]]) if pos is None else np.asarray(pos,float)
    return Reading(float(t),p,np.array(gas,float),np.tile(np.array(wind,float),(len(p),1)),np.ones(len(p),bool))


def setup_controller(mode='bio',bound=None,strict=False):
    s=np.array([[x,y,10.] for x in [-6.,0.,6.] for y in [-6.,0.,6.]])
    c=Configuration(mode=mode,forecast_error_bound=bound,strict_model_gate=strict)
    return Controller(s,GaussianAdvectionDemo(),c)


def test_invalid_reading_rejected():
    with pytest.raises(ValueError):Reading(0,np.zeros((3,3)),np.ones(3),np.zeros((3,3)),np.ones(3))
    with pytest.raises(ValueError):obs(gas=(np.nan,0,0))


def test_wind_reversal_spatial_code_not_collapsed():
    a=encode([obs(gas=(.4,.4,.4))])
    b=encode([obs(gas=(.4,.4,.4),wind=(-1.,0.,0.))])
    assert np.allclose(a.signed_flow,-b.signed_flow)
    assert a.contact_count==b.contact_count==3


def test_true_response_does_not_consume_measured_gas():
    f=GaussianAdvectionDemo()
    s=np.array([[0.,0.,10.],[8.,0.,10.]])
    h=[obs(t=0,gas=(2,3,4)),obs(t=1,gas=(20,30,40))]
    h0=[obs(t=0,gas=(0,0,0)),obs(t=1,gas=(0,0,0))]
    assert np.array_equal(f.response(s,h),f.response(s,h0))


def test_source_posterior_mass_and_q_joint():
    c=setup_controller();r=[obs(0),obs(1),obs(2)]
    p=joint_posterior(r,c.sources,c.model,c.cfg)
    assert np.isclose(p.mass.sum(),1.)
    assert np.isclose(p.joint_source_q.sum(),1.)
    assert np.all(np.linalg.eigvalsh(p.xy_covariance)>-1e-10)
    xy,pm=p.source_xy_probability()
    assert np.isclose(pm.sum(),1.) and len(xy)==len(c.sources)


def test_invalid_sensor_excluded_from_actual_likelihood():
    c=setup_controller();o=obs()
    p=joint_posterior([o],c.sources,c.model,c.cfg)
    o2=Reading(0,o.pos,np.array([1000.,1000.,1000.]),o.wind,np.zeros(3,dtype=bool))
    p2=joint_posterior([o2],c.sources,c.model,c.cfg)
    assert np.allclose(p2.mass,np.ones(len(c.sources))/len(c.sources))
    assert np.isclose(p.mass.sum(),1.)


def test_precontact_does_not_ask_for_shape_certificate():
    c=setup_controller()
    decision=c.step(obs(0,gas=(0,0,0)))
    assert decision.stage=='precontact'
    assert decision.action.name in ('reconfigure_gap_indexed','reconfigure_cross','translate_cross+','translate_cross-',
                                     'translate_z+')
    assert not decision.qualified


def test_common_fisher_schur_and_rank():
    f=np.array([[3.,2.,0.],[-3.,2.,0.],[0.,2.,1.],[0.,2.,-1.]])
    p=np.array([[.5,.2],[.5,-.2],[.2,.4],[-.2,-.4]])
    response0=f[:,0].reshape(2,2)
    # The source derivatives span two independent directions after nuisance projection.
    J=np.array([[2.,0.],[0.,2.],[-2.,0.],[0.,-2.]])
    delta=1.0
    pert=np.stack([f[:,0]+delta*J[:,0],f[:,0]-delta*J[:,0],
                   f[:,0]+delta*J[:,1],f[:,0]-delta*J[:,1]]).reshape(4,2,2)
    lam,rank=_project_source_information(response0,pert,1.,1.,delta)
    assert rank==2 and lam>0


def test_collinear_derivative_orthogonalized_to_amplitude():
    response=np.array([[.1,.2,.3],[.3,.2,.1]])
    d=response.copy().ravel()
    f=np.array([d+1.*d,d-1.*d,d+2.*d,d-2.*d]).reshape(4,2,3)
    lam,rank=_project_source_information(response,f,1.,1.,1.)
    assert rank==0 and lam<1e-8


def test_no_model_certificate_is_not_reported_as_certified():
    c=setup_controller(bound=None)
    d=c.step(obs(0))
    assert d.model_bound is None and not d.qualified


def test_legality_group_collision_and_budget():
    c=setup_controller();v=np.zeros((3,3))
    v[0,1]=8.;v[1,1]=0.
    r,ok=_safe_velocity(v,obs().pos,np.zeros(3),OpenGeometry(),c.cfg)
    assert ok and np.linalg.norm(r[0,:2])<=c.cfg.speed_xy_max+1e-8
    assert np.min([np.linalg.norm((obs().pos+r)[i]-(obs().pos+r)[j])
                   for i,j in [(0,1),(0,2),(1,2)]])>=c.cfg.min_separation-1e-8
    r,ok=_safe_velocity(np.ones((3,3)),obs().pos,np.array([54.,54.,54.]),OpenGeometry(),c.cfg)
    assert ok and np.linalg.norm(r)<1e-8


def test_no_future_clock_or_skip():
    c=setup_controller();c.step(obs(0))
    with pytest.raises(ValueError):c.step(obs(2))


def test_ordinary_and_bio_share_posterior_from_same_prefix():
    a=setup_controller('bio');b=setup_controller('ordinary_eig')
    h=[obs(0),obs(1),obs(2)]
    for o in h:
        a.observe(o);b.observe(o)
    assert np.array_equal(a.posterior.mass,b.posterior.mass)
    assert np.array_equal(a.posterior.map_source,b.posterior.map_source)


def test_legacy_v34_adapter_is_real_source_conditioned():
    f=LegacyV34MultiUAV()
    a=[obs(0),obs(1),obs(2)]
    s=np.array([[0.,0.,10.],[9.,2.,10.]])
    p=f.response(s,a)
    assert p.shape==(2,3,3) and np.isfinite(p).all() and (p>=0).all()
    assert np.allclose(p[:,0,:],0.)


def test_static_s2_refused_by_native_bridge():
    static=Path('/mnt/data/v41_development/mimic_static')
    static.mkdir(exist_ok=True)
    (static/'dataset.json').write_text('{"version":"DATA_ONLY_V1_20261026","worlds":5,"total_native_frames":3005}')
    with pytest.raises(FileNotFoundError):check_root(static)


def test_end_to_end_comparison_runs_not_claiming_s2():
    from demo_v41 import run
    b=run('bio',steps=8,seed=42)
    g=run('ordinary_eig',steps=8,seed=42)
    for z in (b,g):
        assert np.isfinite(z['map_error_m_eval_only'])
        assert z['forward_model'].startswith('GaussianAdvectionDemo')
        assert len(z['action_names'])==8
        assert max(z['distance_per_uav_m'])<=54.
        assert not z['independently_validated_error_certificate']
    assert b['action_names']!=g['action_names']


def test_no_double_evidence_when_recomputing_history():
    c=setup_controller();h=[obs(t) for t in range(4)]
    for o in h:c.observe(o)
    direct=joint_posterior(h,c.sources,c.model,c.cfg)
    assert np.allclose(c.posterior.mass,direct.mass,atol=1e-14)


def test_indexed_signal_changes_per_agent_action_without_relabeling_sources():
    from v41_flowolf.control import all_actions
    base=np.array([[10.,-5.,10.],[10.,0.,10.],[10.,5.,10.]])
    h0=[obs(0,gas=(0.3,0.08,0.01),pos=base)]
    h1=[obs(0,gas=(0.01,0.08,0.3),pos=base)]
    v0={a.name:a.velocity for a in all_actions(h0[-1],encode(h0),0)}
    v1={a.name:a.velocity for a in all_actions(h1[-1],encode(h1),0)}
    assert not np.allclose(v0['reconfigure_gap_indexed'],v1['reconfigure_gap_indexed'])
    assert np.allclose(v0['reconfigure_cross'],v1['reconfigure_cross'])
    assert np.allclose(v0['reconfigure_gap_indexed'].mean(axis=0),0,atol=1e-12)


def test_gap_axis_uses_history_and_permutation_preserves_physical_actions():
    from v41_flowolf.control import all_actions
    base=np.array([[10.,-5.,10.],[10.,0.,10.],[10.,5.,10.]])
    observations=[]
    for t in range(5):
        motion=np.array([[-t*.5,0,0],[0,0,0],[t*.5,0,0]])
        observations.append(obs(t,gas=(.15,.08,.02),pos=base+motion))
    sig=encode(observations)
    assert sig.motion_rank==1
    assert abs(sig.missing_axis[1])>.99  # x-relative motion seen; target y
    v={a.name:a.velocity for a in all_actions(observations[-1],sig,4)}['reconfigure_gap_indexed']
    perm=np.array([2,0,1])
    rerouted=[Reading(h.t,h.pos[perm],h.gas_ppm[perm],h.wind[perm],h.valid[perm]) for h in observations]
    sig2=encode(rerouted)
    v2={a.name:a.velocity for a in all_actions(rerouted[-1],sig2,4)}['reconfigure_gap_indexed']
    assert np.allclose(v[perm],v2)


def test_causal_footprint_uses_past_pose_and_no_future():
    hist=[obs(t,pos=np.array([[10+2*t,-5,10],[10+2*t,0,10],[10+2*t,5,10]])) for t in range(7)]
    sig=encode(hist)
    assert sig.footprint_available
    expected=hist[-1].pos.copy();expected[:,0]-=2*(2+1/(np.e-1))
    assert np.allclose(sig.effective_positions,expected,atol=1e-9)
    assert not encode(hist[:2]).footprint_available


def test_source_height_is_projected_out_not_reused_as_xy():
    base=np.array([[.1,.2],[.3,.4],[.6,.1]])
    f0=base
    dheight=np.array([[1.,-1.],[1.,-1.],[0.,0.]])
    Jx=dheight.ravel();Jy=np.array([2.,0.,-1.,0.,0.,3.])
    # XY derivative 1 is aligned with the (unknown) h derivative.
    near=np.stack([f0.ravel()+Jx,f0.ravel()-Jx,
                   f0.ravel()+Jy,f0.ravel()-Jy]).reshape(4,3,2)
    lam,rank=_project_source_information(f0,near,1.,.02,1.,
                                         height_sensitivity=dheight)
    assert rank==1 and lam<1e-10
    noheight=_project_source_information(f0,near,1.,.02,1.)
    assert noheight[1]==2 and noheight[0]>0


def test_strict_missing_certificate_never_uses_forecast_and_must_scout():
    class PoisonModel:
        def response(self,*args,**kwargs):
            # Bayesian past observation cannot be skipped, but test ensures that
            # unqualified future forecasting is absent: return a valid zero mean.
            return np.zeros((len(args[0]),len(args[1]),len(args[1][0].pos)))
    c=Configuration(strict_model_gate=True,mode='bio')
    s=setup_controller().sources
    ctrl=Controller(s,PoisonModel(),c)
    res=ctrl.step(obs(0,gas=(.4,.05,.01)))
    assert not res.qualified and res.forward_calls==0
    assert res.reason=='MODEL_UNCALIBRATED_PHYSICAL_COVERAGE_FALLBACK'
    assert res.action.name in ('reconfigure_gap_reverse','recenter_on_contact','translate_cross+')


def test_model_error_gate_rejects_unverified_flag_only():
    with pytest.raises(ValueError):Configuration(model_error_calibrated=True,
                                                  forecast_error_bound=.2)
    c=Configuration(model_error_calibrated=True,forecast_error_bound=.2,
                    model_error_certificate_id='external-calibration-locked')
    assert c.model_error_calibrated


def test_source_blind_native_adapter_no_world_reference_and_schema():
    from v41_flowolf.native import reading_from_sessions, OBSERVATION_KEYS
    class MockAgent:
        def __init__(self,i):self.i=i
        def observe(self):
            return {'tick':0,'time_s':0.,'position_ENU_m':[i+10 for i in (self.i,0,50)],
                    'local_wind_m_s':[1,0,0],'CH4_total_ppm':1.93457+.1*self.i,
                    'sensor_valid':True,'instrument':{},'sensor_delay_s':2.,
                    'sensor_tau_s':1.,'hit':False}
    md={'sensor':{'background_ppm':1.93457,'delay_s':2.,'tau_s':1.}}
    r=reading_from_sessions([MockAgent(i) for i in range(3)],md,expected_tick=0)
    assert r.gas_ppm.tolist()==pytest.approx([0,.1,.2])
    assert r.sensor_ids==('uav_0','uav_1','uav_2')
    assert len(OBSERVATION_KEYS)==10


def test_trajectory_planning_checks_whole_horizon_not_only_first_second():
    class Domain:
        def segment_legal(self,a,b):return bool(max(a[0],b[0])<=1.0+1e-10)
    p=np.array([[0,0,0],[0,5,0],[0,10,0]],float)
    c=Configuration(horizon_steps=3)
    v=np.tile([1.,0,0],(3,1))
    out,okay=_safe_velocity(v,p,np.zeros(3),Domain(),c)
    assert okay
    assert out[0,0]*3<=1.+1e-8
    assert out[0,0]>0


def test_native_adapter_rejects_static_subset_even_if_json_has_metadata():
    from v41_flowolf.native import check_root
    with pytest.raises(FileNotFoundError):check_root(Path('/mnt/data/research_v37/prior'))


def test_explicit_unknown_mode_and_identity_guard():
    with pytest.raises(ValueError):Configuration(mode='oracle_eig')
    ctrl=setup_controller();a=obs(t=0)
    first=Reading(0.,a.pos,a.gas_ppm,a.wind,a.valid,sensor_ids=('a','b','c'))
    ctrl.observe(first)
    second=Reading(1.,a.pos,a.gas_ppm,a.wind,a.valid,sensor_ids=('b','a','c'))
    with pytest.raises(ValueError,match='identity'):ctrl.observe(second)