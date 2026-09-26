"""Conformance to original SLSQP objective and structural identities."""
import json,sys,time
from pathlib import Path
import numpy as np
from solver import fit,kl_oracle

root=Path(__file__).resolve().parents[2];e=root/'evidence/pmfs_shared_field_v0';e.mkdir(exist_ok=True)
up=Path(__file__).parent/'upstream/code';sys.path.insert(0,str(up))
from shared_channel import fit_shared,worst_kl_expectation
text=(up/'test_shared_channel.py').read_text()
exec(compile(text,str(up/'test_shared_channel.py'),'exec'),{'__file__':str(e/'upstream_test_runner.py'),'__name__':'__main__'})

started=time.perf_counter();checks={};x=np.array([[[0,0],[0,1],[1,0],[2,1]],[[1,2],[1,2],[2,1],[0,2]],[[3,3],[3,3],[3,2],[2,3]]])
p=np.array([.2,.3,.5]);v=np.array([.4,.6]);A=np.full((3,4,2,4),.05);s,r,m=np.indices(x.shape);A[s,r,m,x]+=.8
ref=fit_shared(A,p,v,.2,tol=1e-12);f=fit(x,4,.2,prior=p,nu=v)
checks['same_SLSQP_entropy']=abs(f.entropy-ref.least_favorable_entropy)<2e-6
checks['same_SLSQP_probability_map']=np.max(abs(f.posterior-ref.posterior))<2e-4
checks['dual_risk_certificate']=f.gap<2e-6 and f.constraint_violation<2e-8
checks['normalized_source_probability']=np.allclose(f.posterior.sum(0),1)
nom=fit(x,4,0,prior=p,nu=v);rf=fit_shared(A,p,v,0)
checks['zero_radius_exact_nominal']=np.allclose(nom.posterior,rf.posterior,atol=1e-14)
perm=np.array([2,0,3,1]);fp=fit(x[:,perm],4,.2,prior=p,nu=v)
checks['synchronous_run_permutation']=np.max(abs(fp.posterior-f.posterior))<2e-6
fd=fit(np.repeat(x,2,axis=2),4,.2,prior=p,nu=np.repeat(v/2,2))
checks['duplicated_protocol_not_extra_evidence']=np.max(abs(fd.posterior[:,::2]-f.posterior))<2e-6
ind=fit(x,4,.2,independent=True,prior=p,nu=v)
indref=[fit_shared(A[:,:,m:m+1],p,np.ones(1),.2,tol=1e-12) for m in range(2)]
checks['independent_matches_separate_SLSQP']=abs(ind.entropy-sum(v[m]*indref[m].least_favorable_entropy for m in range(2)))<2e-6
checks['ambiguity_set_risk_order']=f.entropy<=ind.entropy+2e-6
loss=np.array([[1,2,4,7],[7,7,1,1]],dtype=float);w,upper=kl_oracle(loss,.2)
checks['independent_linear_oracle_matches_scalar']=all(abs(upper[j]-worst_kl_expectation(loss[j],.2))<2e-8 for j in range(2))
reordered=x.copy();reordered[:, :,1]=reordered[:,perm,1]
ir=fit(reordered,4,.2,independent=True,prior=p,nu=v)
checks['independent_identity_shuffle_invariant']=np.max(abs(ir.posterior-ind.posterior))<2e-6
checks['nominal_identity_shuffle_invariant']=np.array_equal(fit(reordered,4,0,prior=p,nu=v).posterior,nom.posterior)
assert all(checks.values()),checks
out={'status':'SCALABLE_SOLVER_CONFORMANCE_PASS','scope':'deterministic synthetic inputs only, no plume or bank scores',
     'checks':{k:bool(v) for k,v in checks.items()},'passed':len(checks),'seconds':time.perf_counter()-started,
     'solver_gap':f.gap,'max_probability_difference_to_SLSQP':float(np.max(abs(f.posterior-ref.posterior)))}
(e/'SOLVER_CONFORMANCE.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
print(out['status'])
