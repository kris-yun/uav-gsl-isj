import numpy as np
import pytest
from gsl_recovery.types import Action,Observation,Mechanism
from gsl_recovery.m2_replay import EvidenceLedger,ReplayEngine,defensive_importance
from gsl_recovery.m2_diagnosis import DifferentialDiagnoser,history_descriptor


class MemoryModel:
    def log_prob(self,history,source,mechanism):
        state=0.;total=0.
        for t,o in enumerate(history):
            state=.7*state+(mechanism.magnitude if mechanism.active(t) else 0.)
            mean=float(source[0])+state
            total-=.5*((o.gas-mean)/.3)**2+np.log(.3*np.sqrt(2*np.pi))
        return total


def history():
    return [Observation(str(i),Action(i,0,time=i),(1.,0.),float(i>1)) for i in range(6)]


def test_ledger_ids_and_atomic_block():
    ledger=EvidenceLedger(history()[:2])
    with pytest.raises(ValueError,match="Duplicate"):
        ledger.append(history()[0])
    with pytest.raises(ValueError):
        ledger.extend([history()[2],history()[1]])
    assert len(ledger)==2
    ledger.extend(history()[2:])
    assert len(ledger)==6


def test_suffix_replacement_is_full_likelihood_including_memory_tail():
    modes=[Mechanism(),Mechanism("sensor_offset",onset=2,duration=1,magnitude=.8)]
    sources=np.array([[0.,0.],[1.,0.]])
    model=MemoryModel()
    engine=ReplayEngine(model,sources,modes,mechanism_prior=[.8,.2])
    result=engine.infer(history(),"Bprime")
    direct=np.array([[model.log_prob(history(),s,e) for e in modes] for s in sources])
    assert np.allclose(result.log_likelihood,direct)
    assert all(abs(r["full_recompute_error"])<1e-10 for r in result.records)
    assert np.isclose(result.joint_posterior.sum(),1)
    assert np.all(result.source_posterior>0)
    latest_only=engine.infer(history(),"B")
    assert not np.allclose(result.log_likelihood,latest_only.log_likelihood)
    # Repeated replays rebuild from fixed prior, not squared old evidence.
    assert np.allclose(engine.infer(history()).joint_posterior,result.joint_posterior)


def test_prior_only_mechanism_at_structure_baseline():
    modes=[Mechanism(),Mechanism("sensor_offset",2,None,.8)]
    result=ReplayEngine(MemoryModel(),[[0,0],[1,0]],modes,mechanism_prior=[.9,.1]).infer(history(),"Aprime")
    assert np.allclose(result.mechanism_posterior,[.9,.1])


def test_source_pair_margin_identity():
    engine=ReplayEngine(MemoryModel(),[[0,0],[1,0]],
                        [Mechanism(),Mechanism("sensor_offset",1,None,.3)])
    r=engine.infer(history())
    old=r.nominal_log_likelihood[0]-r.nominal_log_likelihood[1]
    logk=r.source_log_evidence-r.nominal_log_likelihood
    assert np.isclose(np.log(r.source_posterior[0]/r.source_posterior[1]),old+logk[0]-logk[1])


def test_shared_mechanism_replay_can_reverse_wrong_high_confidence():
    class PatternModel:
        def log_prob(self,history,source,mechanism):
            total=0.
            for t,o in enumerate(history):
                mean=source[0]+(mechanism.magnitude*o.action.x if mechanism.active(t) else 0.)
                total-=.5*(o.gas-mean)**2/.25
            return total
    h=[Observation(str(i),Action(1. if i<20 else -1.,0.,time=i),(1.,0.),1. if i<20 else -1.)
       for i in range(21)]
    engine=ReplayEngine(PatternModel(),[[0,0],[1,0]],
                        [Mechanism(),Mechanism("sensor_offset",0,None,1.)],mechanism_prior=[.9,.1])
    nominal=engine.infer(h,"Aprime")
    repaired=engine.infer(h,"Bprime")
    assert nominal.source_posterior[1]>1-1e-12
    assert repaired.source_posterior[0]>.99
    # Controlled mechanism example, not a PMFS/GADEN experiment.


def test_defensive_importance_preserves_support_and_evidence_target():
    rng=np.random.default_rng(7)
    prior=np.array([.85,.10,.05]);proposal=np.array([.001,.001,.998]);likelihood=np.array([.2,.6,1.7])
    result=defensive_importance(np.log(likelihood),prior,proposal,150000,rng,.2)
    assert np.all(result["proposal"]>0)
    assert result["max_importance_weight"]<=5+1e-12
    assert abs(np.exp(result["log_evidence"])-prior@likelihood)<.008


def test_trainable_shared_differential_diagnosis_and_persistence(tmp_path):
    rng=np.random.default_rng(12)
    y=np.tile([0,1],50)
    reference=rng.normal(0,.05,(100,21))
    actual=reference.copy();actual[:,0]+=y*1.5
    diagnosis=DifferentialDiagnoser(2,hidden=8)
    diagnosis.bind_catalog([Mechanism(),Mechanism("wind_bias",0,None,.5)])
    receipt=diagnosis.fit(actual,reference,y,max_iter=80)
    assert receipt["final_loss"]<receipt["initial_loss"]*.3
    assert (diagnosis.predict_proba(actual,reference).argmax(1)==y).mean()>.95
    path=tmp_path/"diagnosis.npz";diagnosis.save(path)
    loaded=DifferentialDiagnoser.load(path)
    assert np.allclose(loaded.predict_proba(actual,reference),diagnosis.predict_proba(actual,reference))
    assert history_descriptor(history()).shape==(21,)


def test_diagnosis_checkpoint_binds_exact_mechanism_identity(tmp_path):
    from gsl_recovery.m1_teacher import ControlledPlumeBackend
    modes=[Mechanism(),Mechanism("wind_bias",2,None,.5)]
    diagnosis=DifferentialDiagnoser(2).bind_catalog(modes)
    path=tmp_path/"d.npz";diagnosis.save(path)
    loaded=DifferentialDiagnoser.load(path)
    wrong=[Mechanism(),Mechanism("sensor_offset",2,None,.5)]
    with pytest.raises(ValueError,match="identity"):
        loaded.propose([],[[0,0]],ControlledPlumeBackend(),wrong,np.random.default_rng(1))
    with pytest.raises(ValueError,match="rebound"):
        loaded.bind_catalog(wrong)
    np.savez(tmp_path/"legacy.npz",W=diagnosis.W,b=diagnosis.b,V=diagnosis.V,c=diagnosis.c)
    with pytest.raises(ValueError,match="legacy"):
        DifferentialDiagnoser.load(tmp_path/"legacy.npz")


def test_extreme_low_probability_source_retains_conditional_mechanism_and_challenge():
    from gsl_recovery.m3_codebook import SoftCodebook
    from gsl_recovery.m3_planner import RobustCounterEvidencePlanner
    observations=[Observation(str(i),Action(0,0,time=i),(1.,0.),0.) for i in range(100)]
    sources=np.array([[0.,0.],[100.,0.]])
    modes=[Mechanism(),Mechanism("sensor_offset",50,None,.1)]
    result=ReplayEngine(MemoryModel(),sources,modes).infer(observations)
    assert result.source_posterior[1]==0.0  # Numerical underflow is not concealed by a floor.
    assert result.joint_posterior[1].sum()==0.0
    assert np.all(np.isfinite(result.source_log_posterior))
    assert np.allclose(result.conditional_mechanism_posterior.sum(axis=1),1.0)
    probabilities=np.zeros((2,2,8))
    probabilities[0,:,0]=1.;probabilities[1,:,7]=1.
    actions=tuple(Action(i,0,time=100+i) for i in range(3))
    book=SoftCodebook(actions,probabilities,exact=True)
    plan=RobustCounterEvidencePlanner(2).plan(
        [book],result.source_posterior,
        mechanism_posterior=result.conditional_mechanism_posterior)
    assert plan.challenge_indices==[1]
    assert plan.test is not None and plan.test.alternative_power_bound>.99
