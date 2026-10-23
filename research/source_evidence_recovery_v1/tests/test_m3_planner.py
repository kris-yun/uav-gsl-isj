import numpy as np
import pytest
import json
from pathlib import Path
from gsl_recovery.types import Action,Observation,Mechanism
from gsl_recovery.m3_codebook import (CorruptionChannel,SoftCodebook,JointCodebookBuilder,
                                       binary_words,encode_word)
from gsl_recovery.m3_planner import (solve_robust_test,RiskLedger,RecoveryList,
                                     RobustCounterEvidencePlanner,joint_eig,ClusteredASHTReference,
                                     minimax_channel_eig)


def delta(word):
    p=np.zeros(2**len(word));p[encode_word(word)]=1
    return p


def actions(length):
    return tuple(Action(i,0,time=i+1) for i in range(length))


def test_one_flip_tolerant_counterevidence_and_impossibility():
    null=delta([0,0,0,0,0])
    alternatives=np.array([delta([1,1,1,0,0]),delta([1,0,0,1,1])])
    test=solve_robust_test(null,alternatives,CorruptionChannel(max_flips=1),.05)
    assert test.null_risk_bound<=.05+1e-8
    assert test.alternative_power_bound>.999999
    blocked=solve_robust_test(null,np.array([null,alternatives[0]]),CorruptionChannel(max_flips=1),.05)
    assert blocked.alternative_power_bound<=.05+1e-7


def test_tv_uncertainty_cannot_fake_extra_power():
    p=delta([0,0,0]);q=delta([1,1,1])
    test=solve_robust_test(p,q,CorruptionChannel(),.03,null_radius=1,alternative_radius=1)
    assert test.null_risk_bound<=.03+1e-7
    assert test.alternative_power_bound<=.03+1e-7


def test_correlated_burst_and_erasures_neighborhoods():
    alphabet,neighbors=CorruptionChannel(max_flips=0,max_erasures=1,max_burst=2).neighborhoods(3)
    possible={tuple(alphabet[i]) for i in neighbors[0]}
    assert (1,1,0) in possible
    assert (-1,0,1) in possible
    assert (1,0,1) not in possible
    assert (-1,-1,0) not in possible


def test_anytime_risk_budget_and_list_restoration():
    risk=RiskLedger(.05)
    for _ in range(200):risk.reserve(0,"v1")
    assert risk.spent<.05
    book=SoftCodebook(actions(3),np.array([[delta([0,0,0])],[delta([1,1,1])]]),exact=True)
    recovery=RecoveryList(2,eta=.05)
    assert recovery.update(book,[1,1,1],CorruptionChannel(max_flips=1))==[1]
    assert recovery.invalidate("v2")
    assert recovery.active=={0,1}


class CorrelatedFuture:
    def sample_future(self,history,actions,source,mechanism,rng):
        bit=float(rng.random()<.5)
        return [Observation(f"future-{i}",a,(float(rng.normal()),0.),bit) for i,a in enumerate(actions)]


def test_codebook_samples_joint_dependence_instead_of_product_marginals():
    books=JointCodebookBuilder(CorrelatedFuture()).build([], [actions(3)],[[0,0]], [Mechanism()],
                                                          draws=200,rng=np.random.default_rng(1))
    p=books[0].probabilities[0,0]
    assert np.count_nonzero(p)==2
    assert p[0]+p[7]==1
    assert np.all(books[0].tv_radius>0)


def test_planning_variants_and_committed_block_execution():
    book=SoftCodebook(actions(3),np.array([[delta([0,0,0])],[delta([1,1,1])]]),exact=True)
    for variant in ["A","Aprime","B","Bprime","min_hamming","robust_eig"]:
        planner=RobustCounterEvidencePlanner(2,CorruptionChannel(max_flips=1),seed=2)
        plan=planner.plan([book],[.99,.01],variant=variant)
        observed=[Observation(f"o{i}",a,(1.,0.),1.) for i,a in enumerate(plan.actions)]
        with pytest.raises(ValueError,match="whole"):
            planner.observe(plan,observed[:1])
        report=planner.observe(plan,observed)
        assert report["status"]=="executed"
        if variant=="Bprime":
            assert report["rejected"]
        with pytest.raises(ValueError,match="second"):
            planner.observe(plan,observed)
    assert joint_eig(book,[.5,.5])>joint_eig(book,[.99,.01])


def test_round_robin_challenges_include_low_posterior_candidates():
    p=np.repeat(np.array([delta([0,0,0])])[None,:,:],5,axis=0)
    book=SoftCodebook(actions(3),p,exact=True)
    planner=RobustCounterEvidencePlanner(5,challenge_size=1)
    checked=set()
    for _ in range(5):checked.update(planner.plan([book],[.99,.004,.003,.002,.001]).challenge_indices)
    assert {1,2,3,4}.issubset(checked)


def test_mother_asht_really_executes_two_sequential_cluster_stages():
    # First action identifies {0,1}/{2,3}; second identifies {0,2}/{1,3}.
    laws=np.array([[[1,0],[1,0],[0,1],[0,1]],[[1,0],[0,1],[1,0],[0,1]]],float)
    reference=ClusteredASHTReference(laws,alpha=.05)
    true_source=3
    for _ in range(3):
        stage=reference.start_stage()
        if stage is None:break
        symbol=int(np.argmax(laws[stage.action_index,true_source]))
        outcome=reference.observe(symbol)
        if outcome["identified"]:break
    assert reference.active==[3]
    assert len(reference.stages)==2


def test_robust_eig_is_actual_channel_minimization():
    book=SoftCodebook(actions(2),np.array([[delta([0,0])],[delta([1,1])]]),exact=True)
    robust=minimax_channel_eig(book,[.5,.5],CorruptionChannel(max_flips=1))
    assert robust["value"]<1e-6  # Both words can be corrupted to 01.
    clean=minimax_channel_eig(book,[.5,.5],CorruptionChannel())
    assert np.isclose(clean["value"],joint_eig(book,[.5,.5]),atol=1e-8)


def test_recovery_list_changes_second_challenge_without_losing_global_coverage():
    posterior=np.array([.9,.05,.03,.02])
    a=RobustCounterEvidencePlanner(4,challenge_size=2)
    b=RobustCounterEvidencePlanner(4,challenge_size=2)
    a.recovery.active={0,2};b.recovery.active={0,3}
    assert a._challengers(posterior,0)==[1,2]
    assert b._challengers(posterior,0)==[1,3]
    # Even if absent from the list, source 1 was deliberately selected first.


def test_uninformative_fallback_abstains_without_spending_risk():
    p=np.array([[delta([0,0,0])],[delta([0,0,0])]])
    book=SoftCodebook(actions(3),p,exact=True)
    planner=RobustCounterEvidencePlanner(2)
    plan=planner.plan([book],[.99,.01],variant="Bprime")
    assert plan.test is None and plan.risk_index is None
    assert planner.risk.spent==0
    observations=[Observation(str(i),a,(1.,0.),0.) for i,a in enumerate(plan.actions)]
    event=planner.observe(plan,observations)
    assert not event["rejected"] and event["counterevidence_status"]=="abstained"


def test_plan_cannot_be_retested_with_relabelled_observation_ids():
    book=SoftCodebook(actions(3),np.array([[delta([0,0,0])],[delta([1,1,1])]]),exact=True)
    planner=RobustCounterEvidencePlanner(2)
    plan=planner.plan([book],[.99,.01])
    first=[Observation(f"a{i}",a,(1.,0.),1.) for i,a in enumerate(plan.actions)]
    second=[Observation(f"b{i}",a,(1.,0.),1.) for i,a in enumerate(plan.actions)]
    planner.observe(plan,first)
    with pytest.raises(ValueError,match="second"):
        planner.observe(plan,second)
    assert plan.consumed and len(planner.risk.tests)==1


def test_stale_plan_is_consumed_even_if_later_observations_get_new_ids():
    book=SoftCodebook(actions(3),np.array([[delta([0,0,0])],[delta([1,1,1])]]),exact=True)
    planner=RobustCounterEvidencePlanner(2)
    plan=planner.plan([book],[.99,.01])
    first=[Observation(f"a{i}",a,(1.,0.),1.) for i,a in enumerate(plan.actions)]
    assert planner.observe(plan,first,model_version="v2")["status"]=="stale_plan_invalidated"
    second=[Observation(f"b{i}",a,(1.,0.),1.) for i,a in enumerate(plan.actions)]
    with pytest.raises(ValueError,match="second"):
        planner.observe(plan,second,model_version="v1")


def test_new_version_restores_list_before_challenge_selection_and_mixed_versions_fail():
    p=np.repeat(np.array([delta([0,0,0])])[None,:,:],4,axis=0)
    old=SoftCodebook(actions(3),p,model_version="v1",exact=True)
    new=SoftCodebook(actions(3),p,model_version="v2",exact=True)
    planner=RobustCounterEvidencePlanner(4,challenge_size=2)
    planner.recovery.invalidate("v1")
    planner.recovery.active={0,3}
    with pytest.raises(ValueError,match="Mixed"):
        planner.plan([old,new],[.9,.05,.03,.02])
    assert planner.recovery.model_version=="v1"  # Failed batches do not mutate state.
    plan=planner.plan([new],[.9,.05,.03,.02])
    assert planner.recovery.active=={0,1,2,3}
    assert plan.challenge_indices==[1,2]  # Restored source 2 enters slot two.


def test_sparse_five_bit_robust_eig_regression_has_primal_dual_certificate():
    fixture=json.loads((Path(__file__).parent/"fixtures"/"robust_eig_sparse.json").read_text())
    probs=np.asarray(fixture["counts"],float)/fixture["draws"]
    pi=np.asarray(fixture["source_prior"])
    mechanisms=np.asarray(fixture["conditional_mechanisms"])
    book=SoftCodebook(actions(5),probs,exact=True)
    result=minimax_channel_eig(book,pi,CorruptionChannel(max_flips=1),mechanisms)
    assert result["optimality_gap"]<=1e-5
    assert result["feasibility_error"]<1e-9
    transition=np.zeros((32,32))
    for weight,(c,y) in zip(result["channel_weights"],result["allowed_edges"]):
        transition[c,y]=weight
    assert np.all(transition>=0) and np.allclose(transition.sum(axis=1),1)
    p=np.sum(probs*mechanisms[:,:,None],axis=1)
    q=p@transition;mix=pi@q
    logratio=np.log(np.maximum(q,1e-300))-np.log(np.maximum(mix,1e-300))[None,:]
    value=float(np.sum(pi[:,None]*q*logratio))
    gradient=p.T@(pi[:,None]*logratio)
    allowed={c:[] for c in range(32)}
    for c,y in result["allowed_edges"]:allowed[c].append(y)
    gap=float(np.sum(gradient*transition)-sum(min(gradient[c,y] for y in ys) for c,ys in allowed.items()))
    assert abs(value-result["value"])<1e-10
    assert min(value,max(0,gap))<=1e-5+1e-10
    # A too-small optimization budget is rejected, never reported as success.
    with pytest.raises(RuntimeError,match="gap qualification"):
        minimax_channel_eig(book,pi,CorruptionChannel(max_flips=1),mechanisms,max_iterations=1)
