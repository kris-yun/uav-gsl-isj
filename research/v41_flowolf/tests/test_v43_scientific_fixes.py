"""Tests for V43 mathematical/code bugs; not claims of real S2 performance."""
import numpy as np
from v41_flowolf.types import Reading
from v41_flowolf.encoder import encode
from v41_flowolf.control import all_actions,shortlisted_actions,_bipolar_motor_score,Controller
from v41_flowolf.types import Configuration
from v41_flowolf.physics import GaussianAdvectionDemo


def read(t, pos, gas, wind=(1.,0.,0.)):
    p=np.asarray(pos,float)
    return Reading(float(t),p.copy(),np.asarray(gas,float),
                   np.tile(np.asarray(wind,float),(len(p),1)),
                   np.ones(len(p),bool))


def test_polarity_is_not_erased_when_radial_axis_flips():
    pos=np.array([[0.,-5.,10.],[0.,5.,10.]])
    h=[read(t,pos,[.2,.2],wind=(0.,1.,0.)) for t in range(5)]
    z=encode(h)
    assert np.allclose(z.radial_flow,[-1.,1.])
    assert z.inward_flow[0]>0 and z.outward_flow[0]==0
    assert z.outward_flow[1]>0 and z.inward_flow[1]==0
    assert np.allclose(z.signed_flow[0],z.signed_flow[1])  # documented old projection issue
    assert np.sign(z.outward_flow[0]-z.inward_flow[0])==-1
    assert np.sign(z.outward_flow[1]-z.inward_flow[1])==+1


def test_physical_triangle_is_permutation_equivariant():
    pos=np.array([[0.,-5.,10.],[4.,1.,10.],[-3.,6.,10.]])
    h=[read(t,pos,[.20,.20,.20]) for t in range(5)]
    action={x.name:x.velocity for x in all_actions(h[-1],encode(h),4)}
    permutation=np.array([2,0,1])
    hp=[read(t,pos[permutation],[.20,.20,.20]) for t in range(5)]
    ap={x.name:x.velocity for x in all_actions(hp[-1],encode(hp),4)}
    for name in action:
        assert np.allclose(ap[name],action[name][permutation]),name


def test_reject_nonstationary_profile_with_all_positive_sensors():
    pos=np.array([[5.,-8.,10.],[5.,0.,10.],[5.,8.,10.]])
    arr=np.array([[.07,.46,.08],[.35,.065,.90],
                  [.95,.07,.12],[.061,.75,.065]])
    h=[read(t,pos,arr[t]) for t in range(4)]
    z=encode(h)
    assert z.time_cert and not z.profile_stable and not z.shape_cert
    assert z.stage=='contact_uncertain'
    assert z.profile_statistic > 10.


def test_common_amplitude_changes_do_not_fail_shape_screen():
    pos=np.array([[5.,-8.,10.],[5.,0.,10.],[5.,8.,10.]])
    y=np.array([.2,.42,.3]);h=[read(t,pos,y*f) for t,f in enumerate([1.,1.4,2.,1.5])]
    sig=encode(h)
    assert sig.profile_stable and sig.shape_cert


def test_identity_ablation_has_identical_action_geometry_and_response_budget():
    p=np.array([[10.,-7.,10.],[10.,0.,10.],[10.,7.,10.]])
    h=[read(t,p,[.32,.09,.12],wind=(0.,1.,0.)) for t in range(5)]
    sig=encode(h)
    a=all_actions(h[-1],sig,4)
    full=shortlisted_actions(a,sig,'bio')
    noid=shortlisted_actions(a,sig,'bio_noidentity')
    assert [x.name for x in full]==[x.name for x in noid]
    for x,y in zip(full,noid): assert np.array_equal(x.velocity,y.velocity)
    # At least one candidate must have a nonzero identity-conditioned score.
    assert max(abs(_bipolar_motor_score(sig,x)) for x in full)>1e-8


def test_equal_precontact_for_full_and_noidentity():
    p=np.array([[10.,-7.,10.],[10.,0.,10.],[10.,7.,10.]])
    s=np.array([[x,y,10.] for x in [-6.,0.,6.] for y in [-6.,0.,6.]])
    cm=[]
    for mode in ['bio','bio_noidentity']:
        c=Controller(s,GaussianAdvectionDemo(),Configuration(mode=mode))
        o=read(0,p,[0.,0.,0.]);d=c.step(o)
        cm.append((d.action.name,d.action.velocity))
    assert cm[0][0]==cm[1][0]
    assert np.allclose(cm[0][1],cm[1][1])