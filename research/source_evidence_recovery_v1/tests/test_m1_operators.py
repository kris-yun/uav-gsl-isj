import itertools
import tempfile
from pathlib import Path
import numpy as np
import pytest
from scipy.special import ndtr
from gsl_recovery.types import Action, Observation, Mechanism
from gsl_recovery.m1_teacher import (gaussian_lift, divergence_fd,
    gaussian_score_weight, sample_scalar_branch, ControlledPlumeBackend, make_training_episodes)
from gsl_recovery.m1_generator import (JointObservationGenerator, GeneratorConfig,
    source_features, objective_and_gradient, episodes_to_batch, teacher_records_to_batch)


def test_constrained_lift_preserves_wind_and_reports_infeasibility():
    result=gaussian_lift([[1.7,0.4]],[[1.,0.]],[[1.]])
    np.testing.assert_allclose(result.lift[:,0],[0.,2.5],atol=1e-10)
    assert result.feasible and result.wind_residual<1e-10
    impossible=gaussian_lift([[1.,0.]],[[1.,0.]],[[1.]])
    assert not impossible.feasible
    assert impossible.response_residual>0.9


def test_divergence_includes_noise_dependence():
    # v=(xi_0^2,3*xi_1): delta(v)=xi.v-(2*xi_0+3).
    xi=np.array([0.3,-0.8])
    fn=lambda z:np.array([[z[0]**2],[3*z[1]]])
    np.testing.assert_allclose(divergence_fd(fn,xi),[3.6],rtol=1e-8)
    np.testing.assert_allclose(gaussian_score_weight(fn,xi),[xi[0]**3+3*xi[1]**2-3.6],rtol=1e-8)


def test_branch_snap_coarea_has_correct_sign_and_density():
    # P(xi>b(s)) has derivative -phi(b)*b'.
    b=0.35;db=np.array([0.5,0.2])
    boundary=sample_scalar_branch(lambda z:z-b,-db,lambda z:1.,lambda z:1.,lambda z:0.)
    expected=-np.exp(-b*b/2)/np.sqrt(2*np.pi)*db
    np.testing.assert_allclose(boundary.coefficient,expected,rtol=1e-12)
    assert boundary.derivative_residual<1e-12


def test_feature_and_joint_source_derivatives_match_finite_differences():
    model=JointObservationGenerator();model.weights=np.random.default_rng(3).normal(0,0.2,len(model.weights))
    backend=ControlledPlumeBackend();s=np.array([1.2,2.1])
    actions=[Action(x=0.5,y=1.0),Action(x=2.2,y=0.5),Action(x=1.5,y=2.3)]
    obs=backend.simulate_episode(s,actions,rng=np.random.default_rng(4))
    f,d,_=source_features(s,obs[:1],actions[1],obs[1].wind)
    for j in range(2):
        delta=np.eye(2)[j]*1e-5
        plus=source_features(s+delta,obs[:1],actions[1],obs[1].wind)[0]
        minus=source_features(s-delta,obs[:1],actions[1],obs[1].wind)[0]
        np.testing.assert_allclose(d[j],(plus-minus)/2e-5,atol=1e-8)
        numerical=(model.log_prob(obs,s+delta)-model.log_prob(obs,s-delta))/2e-5
        assert abs(model.source_score(obs,s)[j]-numerical)<1e-6
        physical=(backend.log_prob(obs,s+delta)-backend.log_prob(obs,s-delta))/2e-5
        assert abs(backend.source_score(obs,s)[j]-physical)<1e-5


def test_weak_objective_all_variants_have_correct_analytic_gradients():
    backend=ControlledPlumeBackend();s=np.array([0.8,1.7]);rng=np.random.default_rng(1)
    actions=[Action(x=1.2,y=1.5),Action(x=0.2,y=2.3)]
    mechanism=Mechanism(kind='detection_loss',magnitude=0.25)
    episodes=make_training_episodes(backend,[s],actions,n_episodes=4,seed=1,mechanisms=[mechanism])
    batch=episodes_to_batch(episodes)
    records=[]
    for ep in episodes:
        for j,o in enumerate(ep['observations']):
            records.append(backend.teacher_record(ep['source'],ep['observations'][:j],o.action,mechanism,rng))
    weak=teacher_records_to_batch(records)
    w=rng.normal(0,0.1,batch['features'].shape[1])
    for variant in ('Aprime','B','Bprime','Bprime_no_boundary','Bprime_no_wind_constraint'):
        _,gradient=objective_and_gradient(w,batch,weak,variant=variant)
        numerical=[]
        for j in range(len(w)):
            delta=np.eye(len(w))[j]*1e-6
            plus=objective_and_gradient(w+delta,batch,weak,variant=variant)[0]
            minus=objective_and_gradient(w-delta,batch,weak,variant=variant)[0]
            numerical.append((plus-minus)/2e-6)
        np.testing.assert_allclose(gradient,numerical,atol=2e-6,rtol=2e-5)


def test_joint_binary_distribution_is_normalized_and_memory_changes_response():
    model=JointObservationGenerator();model.weights[0]=-1.;model.weights[14]=2.
    actions=[Action(x=1.,y=1.,time=float(i)) for i in range(4)]
    winds=[(0.6,0.1)]*4;s=np.array([1.,1.])
    probabilities=[model.gas_word_probability([],actions,winds,word,s)
                   for word in itertools.product((0,1),repeat=4)]
    assert abs(sum(probabilities)-1)<1e-12
    one=[Observation(uid='prior',action=actions[0],wind=winds[0],gas=1.)]
    zero=[Observation(uid='prior',action=actions[0],wind=winds[0],gas=0.)]
    assert model.next_probability(one,actions[1],winds[1],s)>model.next_probability(zero,actions[1],winds[1],s)
    future=model.sample_future([],actions,s,rng=np.random.default_rng(5))
    assert len(future)==4 and all(o.gas in (0.,1.) for o in future)


def test_mechanism_cannot_change_pre_onset_likelihood():
    backend=ControlledPlumeBackend();s=np.array([1.,1.])
    actions=[Action(x=1.,y=1.,time=float(i)) for i in range(3)]
    obs=backend.simulate_episode(s,actions,rng=np.random.default_rng(5))
    mechanism=Mechanism(kind='sensor_offset',onset=5,magnitude=-1.)
    for model in (backend,JointObservationGenerator()):
        assert model.log_prob(obs,s,mechanism)==model.log_prob(obs,s,Mechanism())


def test_training_checkpoint_and_frozen_split_rejection(tmp_path):
    backend=ControlledPlumeBackend()
    actions=[Action(x=x,y=y) for x,y in [(0.,0.),(1.,1.),(2.,2.),(3.,0.)]]
    episodes=make_training_episodes(backend,[[0.5,0.5],[2.5,1.5]],actions,n_episodes=20,seed=9)
    model=JointObservationGenerator(GeneratorConfig(max_teacher_records=64,maxiter=80))
    receipt=model.fit(episodes,'Bprime',teacher_backend=backend,seed=10)
    assert receipt['final_objective']<receipt['initial_objective']
    assert receipt['final_nll']<receipt['initial_nll']
    assert receipt['maximum_wind_residual']<1e-9
    path=model.save(tmp_path/'model.npz');loaded=JointObservationGenerator.load(path)
    assert loaded.version==model.version
    np.testing.assert_allclose(loaded.weights,model.weights)
    bad=dict(episodes[0]);bad['split']='test'
    with pytest.raises(ValueError,match='non-training'):
        model.fit([bad])
    with pytest.raises(ValueError,match='BLOCKED'):
        JointObservationGenerator().fit(episodes,'Bprime')


def test_branch_compensation_recovers_source_derivative_of_joint_observable():
    # Gauss-Hermite expectation over source-blind local wind, h(Y,U)=Y*U_x.
    # Comparing to finite differences checks the boundary sign and shows why
    # a smooth-only teacher is insufficient for this controlled gate.
    from numpy.polynomial.hermite import hermgauss
    from gsl_recovery.m1_teacher.operators import standard_normal_pdf
    backend=ControlledPlumeBackend();source=np.array([1.1,1.4]);action=Action(x=2.1,y=1.7)
    nodes,weights=hermgauss(30)
    winds=[(np.array([0.6,0.1])+0.45*np.sqrt(2)*np.array([x,y]),wx*wy/np.pi)
           for x,wx in zip(nodes,weights) for y,wy in zip(nodes,weights)]
    def expectation(s):
        return sum(weight*wind[0]*backend.next_probability([],action,wind,s)
                   for wind,weight in winds)
    regular=np.zeros(2);boundary=np.zeros(2)
    for wind,weight in winds:
        mu,ds,_=backend.response(source,action,wind,0.,None,0)
        b=backend.gate(source);sig=backend.config.response_sigma;delta=backend.config.branch_jump
        regular+=weight*wind[0]*(ndtr(b)*standard_normal_pdf(mu/sig)+(1-ndtr(b))*standard_normal_pdf((mu+delta)/sig))/sig*ds
        boundary+=weight*wind[0]*standard_normal_pdf(b)*(ndtr(mu/sig)-ndtr((mu+delta)/sig))*backend.gate_gradient()
    numerical=np.array([(expectation(source+np.eye(2)[j]*1e-5)-expectation(source-np.eye(2)[j]*1e-5))/2e-5 for j in range(2)])
    np.testing.assert_allclose(regular+boundary,numerical,atol=1e-7)
    assert np.linalg.norm(boundary)>1e-3
    assert np.linalg.norm(regular-numerical)>1e-3


def test_wind_calibration_is_learned_only_from_training_and_not_controlled_default():
    model=JointObservationGenerator();rng=np.random.default_rng(33)
    observations=[]
    previous=np.array([2.0,-1.0])
    for i in range(300):
        wind=np.array([2.0,-1.0])+0.5*(previous-np.array([2.0,-1.0]))+0.2*rng.standard_normal(2)
        observations.append(Observation(uid=str(i),action=Action(x=0.,y=0.),wind=tuple(wind),gas=float(i%2)))
        previous=wind
    episode={'source':np.array([0.,0.]),'observations':observations,'split':'train','mechanism':Mechanism()}
    receipt=model.fit_wind([episode])
    np.testing.assert_allclose(model.config.wind_mean,[2.0,-1.0],atol=0.1)
    assert 0.35<model.config.wind_rho<0.65
    assert 0.15<model.config.wind_sigma<0.25
    assert receipt['training_transitions']==299
    with pytest.raises(ValueError,match='non-training'):
        model.fit_wind([{**episode,'split':'frozen_test'}])


def test_saturated_probability_source_derivative_matches_floored_log_prob():
    source=np.array([1.2,1.5]);action=Action(x=2.,y=2.)
    for intercept,y in ((-100.,1.),(100.,0.)):
        model=JointObservationGenerator();model.weights[0]=intercept;model.weights[1]=1.
        obs=[Observation(uid='extreme',action=action,wind=(.6,.1),gas=y)]
        for j in range(2):
            step=np.eye(2)[j]*1e-5
            fd=(model.log_prob(obs,source+step)-model.log_prob(obs,source-step))/2e-5
            assert abs(model.source_score(obs,source)[j]-fd)<1e-9
    backend=ControlledPlumeBackend();source=np.array([100.,100.])
    obs=[Observation(uid='far',action=action,wind=(.6,.1),gas=1.)]
    np.testing.assert_allclose(backend.source_score(obs,source),[0.,0.],atol=1e-12)
