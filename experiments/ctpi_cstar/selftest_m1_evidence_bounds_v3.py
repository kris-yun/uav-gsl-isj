import math
import numpy as np
from m1_causal.evidence_bounds import pairwise_bound, matched_member_bounds


def main():
    rng=np.random.default_rng(20260910)
    for _ in range(10000):
        y,c,d,dc,dd=rng.normal(size=(5,6))
        ec,ed=np.linalg.norm(dc),np.linalg.norm(dd)
        b=pairwise_bound(y,c,d,ec,ed)
        exact=.5*(np.linalg.norm(y-d-dd)**2-np.linalg.norm(y-c-dc)**2)
        assert b['lower']-1e-10 <= exact <= b['upper']+1e-10
        swap=pairwise_bound(y,d,c,ed,ec)
        assert math.isclose(b['lower'],-swap['upper'],abs_tol=1e-10)
        wider=pairwise_bound(y,c,d,2*ec,2*ed)
        assert wider['lower']<=b['lower'] and wider['upper']>=b['upper']
        zero=pairwise_bound(y,c,d,0.,0.)
        assert zero['lower']==zero['upper']==zero['nominal']
    c={'k1':[-5.],'k2':[5.]}; d={'k1':[5.],'k2':[-5.]}; r={'k1':0.,'k2':0.}
    b=matched_member_bounds([-5.],c,d,r,r)
    assert b['conditional_separation_lower']==10.
    assert b['cross_member_separation_lower']==0.
    assert b['state']=='ABSTAIN'
    assert pairwise_bound([1.],[0.],[0.],0.,0.)['conditional_separation_lower']==0
    try:
        matched_member_bounds([0.],c,{'wrong':[5.]},r,r)
    except ValueError:
        pass
    else:
        raise AssertionError('mismatched keys accepted')
    print('M1_V3_BOUND_SELFTEST=PASS; 10000 perturbations; unknown-member counterexample preserved')


if __name__=='__main__':
    main()
