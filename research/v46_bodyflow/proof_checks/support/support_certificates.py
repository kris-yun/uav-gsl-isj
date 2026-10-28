"""Small exact-model certificates. These are not localization benchmarks."""
from pathlib import Path
import json
import numpy as np


def effective_info(js, jn, covariance=None):
    js = np.atleast_2d(js)
    jn = np.atleast_2d(jn)
    if covariance is None:
        covariance = np.eye(js.shape[0])
    l = np.linalg.cholesky(covariance)
    a = np.linalg.solve(l, js)
    b = np.linalg.solve(l, jn)
    r = a - b @ np.linalg.pinv(b) @ a
    return r.T @ r


def main():
    rng = np.random.default_rng(20261028)
    report = {}
    report['shared_nuisance'] = {
        'individual_information': [float(effective_info([[1]], [[1]])[0, 0]),
                                   float(effective_info([[1]], [[-1]])[0, 0])],
        'joint_information': float(effective_info([[1], [1]], [[1], [-1]])[0, 0])}
    assert np.isclose(report['shared_nuisance']['joint_information'], 2, rtol=0, atol=1e-14)

    b = np.array([1., 2., 4., 3.])[:, None]
    js = b @ np.array([[0.7, -1.4]])
    report['separable_effective_info_max'] = float(np.abs(effective_info(js, b)).max())
    assert report['separable_effective_info_max'] < 1e-27

    # Positive known-shape Gaussian patch, arbitrary per-time amplitude and per-sensor gain.
    n, t = 3, 3
    p = rng.normal(size=(n, t, 2))
    s = np.array([0.9, -0.4])
    qmat = np.array([[1.7, 0.2], [0.2, 0.8]])
    alpha = rng.normal(size=t)
    gamma = rng.normal(size=n)
    diff = p - s
    ell = alpha[None, :] + gamma[:, None] - .5 * np.einsum('nti,ij,ntj->nt', diff, qmat, diff)
    corrected = ell + .5 * np.einsum('nti,ij,ntj->nt', p, qmat, p)
    hn, ht = np.eye(n)-np.ones((n,n))/n, np.eye(t)-np.ones((t,t))/t
    exact = hn @ np.einsum('nti,i->nt', p, qmat@s) @ ht
    residual = hn @ corrected @ ht
    report['gaussian_patch_identity_error'] = float(np.max(np.abs(residual-exact)))
    assert report['gaussian_patch_identity_error'] < 1e-14
    report['interaction_dimensions'] = {'N3_T2': (3-1)*(2-1), 'N3_T3': (3-1)*(3-1)}

    # Geometric rank is two, but source sensitivity only has one direction.
    d = np.array([[1.,0.],[0.,1.],[-1.,-1.]])
    bs = np.array([[1.,0.],[0.,0.]])
    report['geometry_not_source_rank'] = {'rank_D': int(np.linalg.matrix_rank(d)),
                                        'rank_information': int(np.linalg.matrix_rank(bs.T@d.T@d@bs))}
    assert report['geometry_not_source_rank']['rank_information'] == 1

    # Global alias despite full-rank local Jacobian.
    source = np.array([.3, .7]); alias = source + np.array([2*np.pi, 0.])
    response = lambda x: np.array([np.cos(x[0]),np.sin(x[0]),np.cos(x[1]),np.sin(x[1])])
    jac = np.array([[-np.sin(source[0]),0.],[np.cos(source[0]),0.],
                    [0.,-np.sin(source[1])],[0.,np.cos(source[1])]])
    report['local_global_alias'] = {'local_rank': int(np.linalg.matrix_rank(jac)),
                                   'alias_response_distance': float(np.linalg.norm(response(source)-response(alias)))}
    assert report['local_global_alias']['alias_response_distance'] < 1e-14

    # Different puff ages create a nonzero double difference in a spatially constant field.
    y1=np.array([1.,0.,0.]);y2=np.array([0.,1.,0.])
    report['noncommon_age_false_difference'] = (hn@(y2-y1)).tolist()

    # Marginal likelihood can depend on source through a q prior even when data profile cannot.
    # q~N(0,1) here is only an analytic counterexample; a bounded positive prior has the same principle.
    y=1.; noise_var=.2
    marginal=[]
    for a in [1.,2.]:
        var=a*a+noise_var
        marginal.append(float(-.5*np.log(2*np.pi*var)-.5*y*y/var))
    report['prior_induced_marginal_difference'] = marginal[1]-marginal[0]

    path=Path(__file__).with_name('support_certificates.json')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
