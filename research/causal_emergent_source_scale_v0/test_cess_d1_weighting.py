#!/usr/bin/env python3
"""Regression tests for the frozen CESS D1 intervention weighting contract."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location(
    "cess_d1_analyzer", HERE/"analyze_cess_d1.py"
)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_uniform_macro_weighting():
    # Unequal macro sizes: macro 0 has three microcells, macro 1 has one.
    labels=np.array([0,0,0,1],dtype=int)
    n_rep=2
    src_log=np.log(np.array([0.2,0.2,0.2,0.9],dtype=float))
    logtp=np.repeat(src_log,n_rep)

    ce,ei,recovered=mod.macro_uniform_ei_from_logtp(logtp,labels,n_rep)
    expected=np.log(2.0)+0.5*(np.log(0.2)+np.log(0.9))
    wrong_uniform_micro=np.log(2.0)+(3*np.log(0.2)+np.log(0.9))/4.0

    assert np.allclose(recovered,src_log)
    assert np.isclose(ei,expected,rtol=0,atol=1e-12)
    assert np.isclose(ce,-0.5*(np.log(0.2)+np.log(0.9)),rtol=0,atol=1e-12)
    assert not np.isclose(ei,wrong_uniform_micro,rtol=0,atol=1e-6)

def test_delta_decomposition():
    labels=np.array([0,0,0,1],dtype=int)
    n_sources=4
    n_rep=2
    true_source=np.repeat(np.arange(n_sources),n_rep)

    # Valid micro posterior matrix with unequal confusion patterns.
    rows=[]
    for s in true_source:
        p=np.full(n_sources,0.08,dtype=float)
        p[s]=0.76
        p[(s+1)%n_sources]+=0.02
        p/=p.sum()
        rows.append(p)
    post=np.stack(rows)
    micro_log=np.log(post[np.arange(len(post)),true_source])

    out=mod.evaluate_macro(post,true_source,labels,micro_log)
    assert out["M"]==2
    assert out["delta_source_contrib"].shape==(4,)
    assert np.isclose(
        out["delta_source_contrib"].mean(),
        out["delta_EI_nats"],
        rtol=0,atol=1e-12
    )

    # Independently recover macro-uniform EI from per-source held-out means.
    mpost,_=mod.macro_posterior_from_micro(post,labels)
    tm=labels[true_source]
    l=np.log(mpost[np.arange(len(mpost)),tm]).reshape(n_sources,n_rep).mean(axis=1)
    expected_macro_ei=np.log(2.0)+0.5*(l[labels==0].mean()+l[labels==1].mean())
    assert np.isclose(out["EI_lower_nats"],expected_macro_ei,rtol=0,atol=1e-12)

if __name__=="__main__":
    test_uniform_macro_weighting()
    test_delta_decomposition()
    print("CESS D1 weighting self-test: PASS")
