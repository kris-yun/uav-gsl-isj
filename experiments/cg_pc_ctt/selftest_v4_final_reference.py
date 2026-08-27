#!/usr/bin/env python3
import numpy as np
import v4_final_reference as v4
from v4_final_reference import *

rng = np.random.default_rng(20260828)

S=4; M=8; J=3; B=8
base=rng.uniform(.05,.95,size=(S,M,J)); p=np.repeat(base,B,axis=2); sid=np.repeat(np.arange(J),B)
y_stop=np.array([0.,1.,0.5]); y=np.repeat(y_stop,B)
bank=collapse_blocks_to_stops(p,y,sid)
assert bank.p.shape==(S,M,J) and np.allclose(bank.p,base) and np.allclose(bank.r,y_stop) and np.all(bank.block_count==B)

assert np.isclose(frequency_floor(200),.5/201)
assert not np.isclose(frequency_floor(100),frequency_floor(200))

labels=np.array([0,0,1,1]); q0=np.ones(4)/4
sp=np.zeros((4,8,3)); sp[0:2,:,:]=.85; sp[2:4,:,:]=.15; sr=np.array([1.,1.,1.])
d=strict_loso_m2(sp,sr,labels,q0,200)
assert d.accepted and d.informative_heldout>=2 and np.all(d.selected_mask[:2])

sp2=sp.copy(); sp2[0:2,:,2]=.05; sp2[2:4,:,2]=.95
d2=strict_loso_m2(sp2,sr,labels,q0,200)
assert not d2.accepted

eq=np.full((4,8,3),.4)
d3=strict_loso_m2(eq,np.array([0.,1.,0.]),labels,q0,200)
assert not d3.accepted

a=np.zeros((1,2,2)); a[0,0]=[0,-100]; a[0,1]=[-100,0]
coh=coherent_source_score(a,[0,1])[0]
naive=v4._logmeanexp(a[0,:,0])+v4._logmeanexp(a[0,:,1])
assert coh < naive-10

for _ in range(10000):
    n=rng.integers(4,40); qn=rng.dirichlet(np.ones(n)); mask=rng.random(n)<.4
    if not mask.any() or mask.all(): continue
    beta=qn[mask].sum(); alpha=max(0.,beta-rng.random()*beta)
    out,active,_=information_projection(qn,mask,alpha,np.ones(n)/n)
    assert not active and np.array_equal(out,qn)
    alpha=beta+(1-beta)*rng.uniform(.01,.99)
    out,active,_=information_projection(qn,mask,alpha,np.ones(n)/n)
    assert active and abs(out[mask].sum()-alpha)<1e-12
    if mask.sum()>1:
        ix=np.flatnonzero(mask); assert np.max(abs(qn[ix]/qn[ix].sum()-out[ix]/out[ix].sum()))<1e-12
    if (~mask).sum()>1:
        ix=np.flatnonzero(~mask); assert np.max(abs(qn[ix]/qn[ix].sum()-out[ix]/out[ix].sum()))<1e-12

st=initialize_state(q0)
out,st2,dec,active,alpha,beta=apply_window(eq,np.array([0.,1.,0.]),labels,q0,np.array([.1,.2,.3,.4]),200,st,"w0")
assert np.array_equal(out,np.array([.1,.2,.3,.4])) and not dec.accepted and "w0" in st2.consumed
try:
    apply_window(eq,np.array([0.,1.,0.]),labels,q0,out,200,st2,"w0")
    raise AssertionError("duplicate window accepted")
except ValueError:
    pass

st=initialize_state(q0); native=np.array([.4999,.4999,.0001,.0001])
out,st2,dec,active,alpha,beta=apply_window(sp,sr,labels,q0,native,200,st,"w1")
assert dec.accepted and beta>=alpha-1e-12 and np.array_equal(out,native)

st=initialize_state(q0); native=np.array([.01,.01,.49,.49])
out,st2,dec,active,alpha,beta=apply_window(sp,sr,labels,q0,native,200,st,"w2")
assert dec.accepted and active and out[:2].sum()>=alpha-1e-12 and out[:2].sum()>native[:2].sum()

perm=np.array([2,0,3,1]); inv=np.argsort(perm)
dp=strict_loso_m2(sp[perm],sr,labels[perm],q0[perm],200)
assert dp.accepted and np.array_equal(dp.selected_mask[inv],d.selected_mask)

spm=sp.copy(); spm[:,4:8,:]=sp[:,[6,4,7,5],:]
dm=strict_loso_m2(spm,sr,labels,q0,200)
assert dm.accepted and np.array_equal(dm.selected_mask,d.selected_mask)

print("V4_FINAL_REFERENCE_SELFTEST PASS")
