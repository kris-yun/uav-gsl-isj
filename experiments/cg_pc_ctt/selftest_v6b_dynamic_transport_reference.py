#!/usr/bin/env python3
"""Deterministic selftests for CG-PC-CTT V6-B ordered dynamics."""
from __future__ import annotations
import numpy as np
import v6b_dynamic_transport_reference as v6


def assert_close(a,b,tol=1e-12):
    if not np.allclose(a,b,atol=tol,rtol=tol):
        raise AssertionError((a,b))


def persistent_trace(T=200):
    x=np.zeros(T,dtype=np.int8)
    x[T//2:]=1
    return x


def alternating_trace(T=200):
    return (np.arange(T)%2).astype(np.int8)


def test_order_is_not_frequency():
    tr=persistent_trace()
    entering=np.asarray([0,0,0,0,1,1,1,1],dtype=np.int8)
    leaving=np.asarray([1,1,1,1,0,0,0,0],dtype=np.int8)
    alternating=np.asarray([0,1,0,1,0,1,0,1],dtype=np.int8)
    # All three have hit fraction 1/2; ordered score must distinguish them.
    assert entering.mean()==leaving.mean()==alternating.mean()==0.5
    se=v6.tape_logscore(tr,entering,1)
    sl=v6.tape_logscore(tr,leaving,1)
    sa=v6.tape_logscore(tr,alternating,1)
    if not (se>sl and se>sa):
        raise AssertionError((se,sl,sa))


def test_cadence_is_explicit():
    tr=persistent_trace()
    y=np.asarray([0,0,0,1,1,1,1,1],dtype=np.int8)
    a=v6.tape_logscore(tr,y,1)
    b=v6.tape_logscore(tr,y,4)
    if abs(a-b)<1e-10:
        raise AssertionError("lag_steps is not live")
    for bad in (0,-1,1.5):
        try: v6.tape_logscore(tr,y,bad)
        except ValueError: pass
        else: raise AssertionError("unverified cadence accepted")


def synthetic_context(source=0, member_pattern=(4,5,6), J=3, T=200):
    S,M=2,8
    x=np.empty((S,M,J,T),dtype=np.int8)
    enter=persistent_trace(T)
    leave=1-enter
    alt=alternating_trace(T)
    for s in range(S):
        for m in range(M):
            for j in range(J):
                # Correct source has persistent entrance-like dynamics for scoring
                # members, wrong source is highly intermittent.
                x[s,m,j]=enter if s==source else alt
    y=np.tile(np.asarray([0,0,0,0,1,1,1,1],dtype=np.int8),(J,1))
    return x,y


def test_context_member_permutation():
    x,y=synthetic_context()
    e=v6.context_source_evidence(x,y,1)
    perm=np.asarray([0,1,2,3,6,4,7,5])
    ep=v6.context_source_evidence(x[:,perm],y,1)
    assert_close(e,ep)


def test_context_specific_member_identity():
    # Construct two contexts where different scoring members are informative.
    # Evidence is marginalized within each context, so swapping which member is
    # informative between contexts must not require a persistent global member id.
    x1,y=synthetic_context()
    x2,y2=synthetic_context()
    alt=alternating_trace()
    ent=persistent_trace()
    # context 1: only member 4 strongly supports source 0; other scoring members neutral-ish
    for m in (5,6,7):
        x1[0,m,:,:]=alt
    # context 2: only member 7 strongly supports source 0
    for m in (4,5,6):
        x2[0,m,:,:]=alt
    e1=v6.context_source_evidence(x1,y,1)
    e2=v6.context_source_evidence(x2,y2,1)
    q=v6.source_posterior(np.asarray([0.5,0.5]),np.stack([e1,e2]))
    if not q[0]>q[1]:
        raise AssertionError(q)


def test_static_ablation_discards_order():
    T=200; S,M,J=2,8,1
    x=np.empty((S,M,J,T),dtype=np.int8)
    x[0,:,:,:]=persistent_trace(T)
    x[1,:,:,:]=alternating_trace(T)
    entering=np.asarray([[0,0,0,0,1,1,1,1]],dtype=np.int8)
    leaving=np.asarray([[1,1,1,1,0,0,0,0]],dtype=np.int8)
    a=v6.frequency_source_evidence(x,entering,T)
    b=v6.frequency_source_evidence(x,leaving,T)
    assert_close(a,b)
    da=v6.context_source_evidence(x,entering,1)
    db=v6.context_source_evidence(x,leaving,1)
    if np.allclose(da,db):
        raise AssertionError("dynamic evidence collapsed to frequency")


def test_dynamic_null_is_source_independent():
    train=[np.asarray([0,0,0,1,1,1,1,1]),np.asarray([0,0,1,1,1,1,1,1])]
    held=[np.asarray([0,0,0,0,1,1,1,1])]
    a=v6.jeffreys_markov_null_predictive(train,held)
    b=v6.jeffreys_markov_null_predictive(list(reversed(train)),held)
    assert_close(a,b)


def test_loco_pass_on_consistent_dynamic_source():
    contexts=[]
    for c in range(4):
        x,y=synthetic_context(source=0)
        contexts.append({'id':f'c{c}','sim_occupancy':x,'observed_tape':y,'timesteps':200})
    d=v6.loco_dynamic_diagnostic(contexts,np.asarray([0.5,0.5]),1)
    if not d.transfer_pass:
        raise AssertionError(d)


def main():
    test_order_is_not_frequency()
    test_cadence_is_explicit()
    test_context_member_permutation()
    test_context_specific_member_identity()
    test_static_ablation_discards_order()
    test_dynamic_null_is_source_independent()
    test_loco_pass_on_consistent_dynamic_source()
    print('V6B_DYNAMIC_TRANSPORT_REFERENCE_SELFTEST PASS')

if __name__=='__main__': main()
