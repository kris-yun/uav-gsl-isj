"""Synthetic-only pre-score parity, invoking unmodified public reference functions."""
import ast
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import torch
import signature_core as sc

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[2]/'evidence/ocb_r2/r2c_signature_path'


def extract(filename,names,scope):
    tree=ast.parse((HERE/'upstream_reference'/filename).read_text())
    selected=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]
    assert {node.name for node in selected}==set(names)
    exec(compile(ast.Module(body=selected,type_ignores=[]),filename,'exec'),scope)


def main():
    scope={'torch':torch,'np':np}
    extract('static_kernels.py',['RBFKernel'],scope)
    extract('sigkernel.py',['tile','SigKernel_naive'],scope)
    rng=np.random.default_rng(2026093200)
    xs=[sc.path(rng.integers(0,2,(10,30))) for _ in range(12)]
    tx=torch.tensor(np.stack(xs).tolist(),dtype=torch.float64)
    ty=torch.tensor(np.stack(xs[::-1]).tolist(),dtype=torch.float64)
    upstream=scope['SigKernel_naive'](tx,ty,scope['RBFKernel'](1),dyadic_order=1).tolist()
    fast=[sc.kernel(x,y) for x,y in zip(xs,xs[::-1])]
    error=float(np.max(np.abs(np.array(upstream)-fast)))
    assert np.allclose(upstream,fast,rtol=1e-10,atol=1e-10)
    gram=np.array([[sc.kernel(x,y) for y in xs] for x in xs])
    symmetry=float(np.max(np.abs(gram-gram.T)))
    minimum_eig=float(np.linalg.eigvalsh((gram+gram.T)/2).min())
    assert symmetry<1e-10 and (gram.diagonal()>=0).all() and minimum_eig>=-1e-10*max(1,np.linalg.norm(gram,2))
    assert np.array_equal(gram,np.array([[sc.kernel(x,y) for y in xs] for x in xs]))
    # Independently verify cached-static lookup against full generic paths.
    ref=rng.integers(0,2,(3,10,30));rp=np.stack([sc.path(r) for r in ref]).transpose(1,0,2)
    tab=np.exp(-np.square(rp[:,:,None,None,:]-rp[None,None,:,:,:]).sum(axis=-1))
    ca,cb=sc.choices(12,[0,0,1,1],0),sc.choices(12,[0,0,1,1],1)
    cached=sc.lookup_batch(tab,ca,cb)
    generic=[sc.kernel(rp[np.arange(11),a],rp[np.arange(11),b]) for a,b in zip(ca,cb)]
    lookup_error=float(np.max(np.abs(cached-generic)))
    assert lookup_error<1e-10
    # Exact-Q explicit level-three tensors: independently enumerate all 3^3 paths,
    # keeping last seven snapshots equal across realizations (only 27 unique Q paths).
    short=ref.copy();short[:,3:]=short[0,3:]
    eq=sc.q_expected_signature(short)
    enumerated=[[],[],[]]
    for idx in itertools.product(range(3),repeat=3):
        y=short[0].copy()
        for t,i in enumerate(idx): y[t]=short[i,t]
        s=sc.signature(sc.path(y))
        for l in range(3):enumerated[l].append(s[l])
    exact_error=max(float(np.max(np.abs(eq[l]-np.mean(enumerated[l],axis=0)))) for l in range(3))
    assert exact_error<1e-10
    # Straight-line signatures must match exp(v) through level three.
    v=rng.normal(size=4);sg=sc.signature(np.array([np.zeros(4),v]))
    assert np.allclose(sg[0],v) and np.allclose(sg[1],np.outer(v,v)/2)
    assert np.allclose(sg[2],np.einsum('i,j,k->ijk',v,v,v)/6)
    # Q choices select complete same-candidate/same-time snapshots, not scalar cells.
    sampled=rp[np.arange(11)[None,:],ca]
    assert all(np.array_equal(sampled[b,t],rp[t,ca[b,t]]) for b in range(12) for t in range(11))
    result=dict(decision='R2C_IMPLEMENTATION_PARITY_PASS',synthetic_pairs=12,
        upstream_repository='https://github.com/crispitagorico/sigkernel',upstream_commit='40a583155ea8d2194af0e90dddab37e2659cfcfd',
        reference_functions=['RBFKernel','SigKernel_naive','tile'],public_source_unmodified=True,
        float64_rtol=1e-10,float64_atol=1e-10,primary_max_absolute_error=error,
        lookup_max_absolute_error=lookup_error,symmetry_max_error=symmetry,minimum_gram_eigenvalue=minimum_eig,
        nonnegative_diagonal=True,deterministic_repeat=True,exact_Q_signature_enumeration_error=exact_error,
        q_snapshot_preservation_pass=True,
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'upstream_reference').iterdir() if p.is_file()},
        no_discovery_target_decoded=True)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'R2C_IMPLEMENTATION_PARITY.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=='__main__':main()
