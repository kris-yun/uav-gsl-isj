"""Deterministic software/identity checks only. No plume/data/model training."""
import json
from pathlib import Path
import numpy as np
from shared_channel import fit_shared,posterior_and_entropy,worst_kl_expectation

# Hand specified response symbols for THREE synthetic sources, FOUR whole
# realizations, TWO alternative observation protocols, FOUR symbols.
# 0.04 here is an explicitly declared SYNTHETIC sensor confusion probability;
# it is not a proposed GADEN noise level, smoothing rule, or probability floor.
labels=np.array([[[0,0],[0,1],[1,0],[2,1]],
                 [[1,2],[1,2],[2,1],[0,2]],
                 [[3,3],[3,3],[3,2],[2,3]]])
A=np.full((3,4,2,4),.04)
for s in range(3):
 for r in range(4):
  for m in range(2):A[s,r,m,labels[s,r,m]]=.88
p=np.array([.2,.3,.5]);v=np.array([.4,.6])
nom=fit_shared(A,p,v,0.)
fit=fit_shared(A,p,v,.2)
checks={}
checks['fixed_prior_nominal_recovery']=bool(np.allclose(nom.posterior,posterior_and_entropy(A,p,v,np.ones((3,4))/4)[0]))
checks['probability_mass']=bool(np.allclose(fit.posterior.sum(0),1.))
checks['weights_mass']=bool(np.allclose(fit.weights.sum(1),1.))
checks['saddle_gap']=bool(fit.saddle_gap<2e-6)
checks['worst_risk_at_most_uniform_decision']=bool(fit.worst_case_risk<=-np.sum(p*np.log(p))+2e-6)
perm=np.array([2,0,3,1])
fp=fit_shared(A[:,perm],p,v,.2)
checks['consistent_run_permutation_invariance']=bool(np.allclose(fp.posterior,fit.posterior,atol=2e-5))
Ad=np.repeat(A,2,axis=2);vd=np.repeat(v/2,2)
fd=fit_shared(Ad,p,vd,.2)
checks['duplicating_protocol_is_not_extra_evidence']=bool(np.allclose(fd.posterior[:,::2],fit.posterior,atol=2e-5))
ind=[fit_shared(A[:,:,m:m+1],p,np.ones(1),.2) for m in range(2)]
ind_value=sum(v[m]*ind[m].least_favorable_entropy for m in range(2))
checks['shared_ambiguity_subset_order']=bool(fit.least_favorable_entropy<=ind_value+2e-6)
identical=np.repeat(A[:1],3,axis=0)
fi=fit_shared(identical,p,v,.2)
checks['indistinguishable_sources_preserve_prior']=bool(np.allclose(fi.posterior,p[:,None,None],atol=2e-5))
checks['KL_zero_mean_identity']=bool(abs(worst_kl_expectation([1,2,4,7],0)-3.5)<1e-12)
checks['KL_saturated_max_identity']=bool(abs(worst_kl_expectation([1,2,4,7],np.log(4))-7)<1e-12)
checks['no_automatic_smoothing']=False
try:fit_shared(np.zeros_like(A),p,v,.2)
except ValueError:checks['no_automatic_smoothing']=True
output={'scope':'synthetic deterministic numerical/identity checks; NOT source-localization evidence',
        'checks':checks,'passed':sum(checks.values()),'total':len(checks),
        'saddle_gap':fit.saddle_gap,'max_constraint_violation':fit.max_constraint_violation,
        'shared_entropy':fit.least_favorable_entropy,'independent_protocols_entropy':ind_value,
        'nominal_entropy':nom.least_favorable_entropy,
        'nominal_posterior':nom.posterior.tolist(),'robust_posterior':fit.posterior.tolist()}
assert all(checks.values()),output
Path(__file__).with_name('test_results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
print(json.dumps(output,ensure_ascii=False,indent=2))
