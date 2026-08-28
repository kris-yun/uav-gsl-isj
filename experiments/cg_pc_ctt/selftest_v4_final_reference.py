#!/usr/bin/env python3
import numpy as np
import v4_final_reference as v4
from v4_final_reference import *

rng=np.random.default_rng(20260828)

# Physical-stop contract.
S=4; M=8; J=3; B=8
base=rng.uniform(.05,.95,size=(S,M,J)); p=np.repeat(base,B,axis=2)
sid=np.repeat(np.arange(J),B); y_stop=np.array([0.,1.,0.5]); y=np.repeat(y_stop,B)
bank=collapse_blocks_to_stops(p,y,sid)
assert bank.p.shape==(S,M,J) and np.allclose(bank.p,base)
assert np.allclose(bank.r,y_stop) and np.all(bank.block_count==B)
assert np.isclose(frequency_floor(200),.5/201)
assert not np.isclose(frequency_floor(100),frequency_floor(200))

# Component builder: finite precision in zero-transport-variance directions.
rect=np.array([[0,0,1,1],[1,0,1,1],[3,0,1,1],[4,0,1,1]])
flat=np.full((4,8,3),.5)
build=build_components(flat,rect,200)
assert np.min(build.c_eff_eigenvalues)>0 and np.all(np.isfinite(build.precision))

# Exact coordinate aliases cannot be separated by prediction noise.
alias_rect=np.array([[0,0,1,1],[0,0,1,1],[2,0,1,1],[3,0,1,1]])
aliasp=rng.uniform(.05,.95,size=(4,8,3))
ab=build_components(aliasp,alias_rect,200)
assert ab.labels[0]==ab.labels[1]

# Synthetic resolved components using calibration-member coherent differences.
rect2=np.array([[0,0,1,1],[1,0,1,1],[2,0,1,1],[3,0,1,1]])
sp=np.zeros((4,8,3))
calA=np.array([[.85,.90,.80],[.84,.89,.79],[.86,.91,.81],[.83,.88,.78]])
calB=np.array([[.15,.10,.20],[.14,.09,.19],[.16,.11,.21],[.13,.08,.18]])
sp[0,:4,:]=calA; sp[1,:4,:]=calA; sp[2,:4,:]=calB; sp[3,:4,:]=calB
sp[0:2,4:8,:]=.95; sp[2:4,4:8,:]=.05
labels=build_components(sp,rect2,200).labels
assert len(np.unique(labels))==2 and labels[0]==labels[1] and labels[2]==labels[3] and labels[0]!=labels[2]
q0=np.ones(4)/4; sr=np.ones(3)
d=strict_loso_m2(sp,sr,labels,q0,200)
assert d.accepted and d.informative_heldout>=2 and np.all(d.heldout_absolute_gain>0)
assert np.all(d.selected_mask[:2]) and not np.any(d.selected_mask[2:])

# Contradictory held-out stop must abstain.
sp2=sp.copy(); sp2[0:2,4:8,2]=.02; sp2[2:4,4:8,2]=.98
d2=strict_loso_m2(sp2,sr,labels,q0,200)
assert not d2.accepted

# Equal/shared source prediction must abstain.
eq=np.full((4,8,3),.5)
d3=strict_loso_m2(eq,np.array([0.,1.,0.]),labels,q0,200)
assert not d3.accepted

# Blocking counterexample 1: universally wrong family must lose to absolute Jeffreys-Beta null.
bad=np.full((4,8,3),.005); bad[:2,:,:]=.01
dbad=strict_loso_m2(bad,np.ones(3),np.array([0,0,1,1]),q0,200)
assert not dbad.accepted and dbad.reason=="HELDOUT_ABSOLUTE_NULL_FAIL"

# Coherent member contract vs naive stopwise member switching. Also locks NumPy axis semantics.
a=np.zeros((1,2,2)); a[0,0]=[0,-100]; a[0,1]=[-100,0]
coh=coherent_source_score(a,[0,1])[0]
naive=v4._logmeanexp(a[0,:,0])+v4._logmeanexp(a[0,:,1])
assert coh < naive-10

# Blocking counterexample 2: reproduce fixed old-reference trial 136 and forbid incoherent reversal.
rng2=np.random.default_rng(20260828)
trial_case=None
for trial in range(137):
    z=np.full((2,8,3),.5)
    z[:,4:8,:]=np.exp(rng2.uniform(np.log(.003),np.log(.95),size=(2,4,3)))
    if trial==136: trial_case=z
assert trial_case is not None
di=strict_loso_m2(trial_case,np.ones(3),np.array([0,1]),np.array([.5,.5]),200,min_informative=1)
aa=source_member_stop_logscore(trial_case,np.ones(3),200)
full=np.array([coherent_source_score(aa,[0,1,2])[s] for s in range(2)])
if di.accepted:
    b=int(di.selected_component)
    assert full[b] >= np.max(np.delete(full,b)) - 1e-12

# Calibration/scoring member order and candidate permutation invariance.
perm=np.array([2,0,3,1]); inv=np.argsort(perm)
rectp=rect2[perm]; spp=sp[perm]; q0p=q0[perm]
bp=build_components(spp,rectp,200)
dp=strict_loso_m2(spp,sr,bp.labels,q0p,200)
assert dp.accepted and np.array_equal(dp.selected_mask[inv],d.selected_mask)
spm=sp.copy(); spm[:,4:8,:]=sp[:,[6,4,7,5],:]
dm=strict_loso_m2(spm,sr,labels,q0,200)
assert dm.accepted and np.array_equal(dm.selected_mask,d.selected_mask)
spc=sp.copy(); spc[:,:4,:]=sp[:,[2,0,3,1],:]
bc=build_components(spc,rect2,200)
assert np.array_equal(bc.labels,labels)

# KL/I-projection stress.
rng3=np.random.default_rng(123)
for _ in range(10000):
    n=rng3.integers(4,40); qn=rng3.dirichlet(np.ones(n)); mask=rng3.random(n)<.4
    if not mask.any() or mask.all(): continue
    beta=qn[mask].sum(); alpha=max(0.,beta-rng3.random()*beta)
    out,active,_=information_projection(qn,mask,alpha,np.ones(n)/n)
    assert not active and np.array_equal(out,qn)
    alpha=beta+(1-beta)*rng3.uniform(.01,.99)
    out,active,_=information_projection(qn,mask,alpha,np.ones(n)/n)
    assert active and abs(out[mask].sum()-alpha)<1e-12

# apply_window builds labels internally, consumes once, exact native on abstain.
st=initialize_state(q0); native=np.array([.1,.2,.3,.4])
out,st2,dec,active,alpha,beta,bld=apply_window(eq,np.array([0.,1.,0.]),rect2,q0,native,200,st,"w0")
assert np.array_equal(out,native) and not dec.accepted and "w0" in st2.consumed
try:
    apply_window(eq,np.array([0.,1.,0.]),rect2,q0,native,200,st2,"w0")
    raise AssertionError("duplicate window accepted")
except ValueError:
    pass

# Accepted window: inactive projection preserves a stronger native state exactly.
st=initialize_state(q0); native=np.array([.49999,.49999,.00001,.00001])
out,st2,dec,active,alpha,beta,bld=apply_window(sp,sr,rect2,q0,native,200,st,"w1")
assert dec.accepted and beta>=alpha-1e-12 and np.array_equal(out,native)

# Accepted window: active projection raises only validated macro mass.
st=initialize_state(q0); native=np.array([.01,.01,.49,.49])
out,st2,dec,active,alpha,beta,bld=apply_window(sp,sr,rect2,q0,native,200,st,"w2")
assert dec.accepted and active and out[:2].sum()>=alpha-1e-12 and out[:2].sum()>native[:2].sum()

print("V4_FINAL_REFERENCE_SCIENCE_CONTRACT PASS")
