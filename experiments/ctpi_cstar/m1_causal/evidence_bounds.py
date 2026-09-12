"""V3 deterministic perturbation bounds in a caller-frozen whitened space.

No covariance fitting, epsilon calibration or deployment error-rate guarantee
is performed here. Bounds are conditional on all supplied error balls holding.
"""
import math
import numpy as np


def pairwise_bound(observed, candidate_c, candidate_d, epsilon_c, epsilon_d):
    y,c,d = (np.asarray(v,dtype=float) for v in (observed,candidate_c,candidate_d))
    if y.ndim!=1 or y.size==0 or c.shape!=y.shape or d.shape!=y.shape or not all(np.isfinite(v).all() for v in (y,c,d)):
        raise ValueError('M1_BOUND_VECTOR')
    if any(not math.isfinite(v) or v<0 for v in (epsilon_c,epsilon_d)):
        raise ValueError('M1_BOUND_RADIUS')
    rc,rd=float(np.linalg.norm(y-c)),float(np.linalg.norm(y-d))
    nominal=.5*(rd*rd-rc*rc)
    error=rc*epsilon_c+.5*epsilon_c**2+rd*epsilon_d+.5*epsilon_d**2
    separation=max(0.,float(np.linalg.norm(c-d))-epsilon_c-epsilon_d)
    if not all(math.isfinite(v) for v in (nominal,error,separation)):
        raise ValueError('M1_BOUND_OVERFLOW')
    return dict(nominal=nominal,error_bound=error,lower=nominal-error,upper=nominal+error,
                conditional_separation_lower=separation)


def matched_member_bounds(observed, predictions_c, predictions_d, radii_c, radii_d):
    keys=set(predictions_c)
    if not keys or any(set(mapping)!=keys for mapping in (predictions_d,radii_c,radii_d)):
        raise ValueError('M1_BOUND_MEMBER_KEYS')
    rows={k:pairwise_bound(observed,predictions_c[k],predictions_d[k],radii_c[k],radii_d[k]) for k in sorted(keys)}
    lower=min(v['lower'] for v in rows.values())
    upper=max(v['upper'] for v in rows.values())
    # Unknown-k ambiguity diagnostic. This is not a Bayes-error bound either.
    cross=min(max(0.,float(np.linalg.norm(np.asarray(predictions_c[k])-np.asarray(predictions_d[j])))
                  -radii_c[k]-radii_d[j]) for k in keys for j in keys)
    return dict(members=rows,lower=lower,upper=upper,
                state='C_OVER_D' if lower>0 else 'D_OVER_C' if upper<0 else 'ABSTAIN',
                conditional_separation_lower=min(v['conditional_separation_lower'] for v in rows.values()),
                cross_member_separation_lower=cross,
                guarantee='deterministic only if declared error balls all hold; no statistical coverage claimed')
