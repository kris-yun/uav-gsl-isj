#!/usr/bin/env python3
"""Known-age point-source Green-kernel certificate and necessary counterexamples."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'m1'))
from m1_decoders import encode,decode

def main():
    delta1=np.array([[-4.,-2.],[5.,-1.],[-1.,3.]])
    relwind=np.array([[1.3,.2],[.8,-.1],[1.1,.4]])
    R=decode(encode(delta1,relwind,[.4,.35,.25]))['relative']
    kappa=.8;a1=100.;dt=2.;a2=a1+dt;alpha=1.
    Q1=np.eye(2)/(2*kappa*a1);Q2=np.eye(2)/(2*kappa*a2)
    delta2=delta1+dt*alpha*R
    E=delta2@Q2-delta1@Q1
    mainterm=dt*alpha*R@Q2;perturb=delta1@(Q2-Q1)
    lower=np.linalg.svd(mainterm,compute_uv=False)[-1]-np.linalg.norm(perturb,2)
    H=np.eye(3)-np.ones((3,3))/3
    s=np.array([2.,-3.]);U=np.array([.7,.2]);q=150.;gain=np.log([1.1,.8,1.2])
    X1=np.array([40.,20.]);X2=np.array([42.,19.]);p1=X1+delta1;p2=X2+delta2
    def corrected_log(p,a,Q):
        r=p-U*a
        logc=np.log(q)-np.log(4*np.pi*kappa*a)-.5*np.sum((r-s)*((r-s)@Q),axis=1)+gain
        return logc+.5*np.sum(r*(r@Q),axis=1)
    z=H@(corrected_log(p2,a2,Q2)-corrected_log(p1,a1,Q1))
    err=float(np.linalg.norm(z-E@s))
    assert err<1e-12 and lower>0 and np.linalg.matrix_rank(E)==2
    # Nonempty rank is not enough: a formation expansion exactly cancels
    # the inverse-age precision change in a temporal contrast.
    cancel_delta2=(a2/a1)*delta1
    cancelR=(cancel_delta2-delta1)/dt
    cancelE=cancel_delta2@Q2-delta1@Q1
    assert np.linalg.matrix_rank(cancelR)==2 and np.linalg.norm(cancelE)<1e-14
    # Finite release basis q(t)=b*1 makes distinct kernels observationally
    # equivalent, without pointwise proportionality.
    t=np.linspace(0,1,1001);k1=np.ones_like(t);k2=2*t
    means=[float(np.trapezoid(k1,t)),float(np.trapezoid(k2,t))]
    assert np.allclose(means,[1,1]) and not np.allclose(k1,k2)
    # Vertical terms are noncommon in a multilevel array and must be removed
    # explicitly when source height is known.
    h=11.;z1=np.array([10.,12.,14.]);z2=np.array([11.,12.5,13.5])
    vertical_bias=H@(-((z2-h)**2)/(4*kappa*a2)+((z1-h)**2)/(4*kappa*a1))
    assert np.linalg.norm(vertical_bias)>1e-3
    report={'scope':'R3 analytical/implementation review only; not a plume performance experiment.',
        'green_positive_certificate':{'corrected_log_identity_error':err,
            'weyl_lower_bound':float(lower),'actual_min_singular_E':float(np.linalg.svd(E,compute_uv=False)[-1]),
            'E':E.tolist(),'relative_rank':int(np.linalg.matrix_rank(R))},
        'green_age_cancellation_counterexample':{'relative_rank':int(np.linalg.matrix_rank(cancelR)),
            'E_norm':float(np.linalg.norm(cancelE)),
            'condition':'delta2=(a2/a1)*delta1; nonzero full-rank motion alone does not establish source contrast'},
        'finite_release_basis_counterexample':{'integral_k1':means[0],'integral_k2':means[1],
            'kernels_pointwise_equal':False,'resolution':'Pointwise kernel proportionality requires all nonnegative release histories, not a fixed finite span.'},
        'multilevel_vertical_bias':{'norm':float(np.linalg.norm(vertical_bias)),
            'resolution':'Common altitude per epoch or explicit known vertical-term correction is required.'}}
    (HERE/'green_support_review_results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
