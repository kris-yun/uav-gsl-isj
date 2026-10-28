"""Exact two-step adaptive Gaussian certificate; not localization performance.

y1 = s+q+e1, a=sign(y1), y2=a*s+q+e2, independent N(0,1) innovations.
The policy is parameter-free GIVEN y1.  Holding observed history fixed gives
the correct conditional Jacobian (a,1), not a total derivative through y1.
"""
from pathlib import Path
import json
import math
import numpy as np


def schur_s(I):
    return float(I[0,0]-I[0,1]*I[1,0]/I[1,1])


def main():
    I_plus=np.array([[2.,2.],[2.,2.]])
    I_minus=np.array([[2.,0.],[0.,2.]])
    rows=[]
    for mean_y1 in [-2.,-1.,0.,1.,2.]:
        p=.5*(1+math.erf(mean_y1/math.sqrt(2)))
        joint=p*I_plus+(1-p)*I_minus
        full_eff=schur_s(joint)
        mean_design_eff=p*schur_s(I_plus)+(1-p)*schur_s(I_minus)
        exact_gap=2*p*(1-p)
        assert abs(full_eff-(2-2*p*p))<1e-14
        assert abs(full_eff-mean_design_eff-exact_gap)<1e-14
        assert full_eff>=mean_design_eff
        rows.append({"s_plus_q":mean_y1,"P_action_plus":p,
                     "adaptive_full_efficient_information":full_eff,
                     "expected_realized_design_schur":mean_design_eff,
                     "strict_gap":full_eff-mean_design_eff})

    # Numerical integration independently verifies the half-normal moments.
    # Interval [0,9] has omitted normal mass below 1.2e-19, far below tolerance.
    nodes,weights=np.polynomial.legendre.leggauss(128)
    x=(nodes+1)*4.5; w=weights*4.5
    density=np.exp(-x*x/2)/math.sqrt(2*math.pi)
    mass=float(w@density)
    mean_pos=float(w@(x*density)/mass)
    variance_pos=float(w@(x*x*density)/mass-mean_pos**2)
    expected_mean=math.sqrt(2/math.pi)
    assert abs(mass-.5)<1e-13
    assert abs(mean_pos-expected_mean)<1e-12
    assert abs(variance_pos-(1-2/math.pi))<1e-12
    # At s=q=0, E=a-1; z=E*s+(e2-e1). Conditioning on a also conditions on e1.
    contrast_noise_mean_given_plus=-mean_pos
    contrast_noise_variance_given_plus=1+variance_pos
    assert abs(contrast_noise_mean_given_plus)>0.7
    assert abs(contrast_noise_variance_given_plus-2)>0.6
    report={
      "scope":"EXACT_ADAPTIVE_GAUSSIAN_IDENTITY_AND_COUNTEREXAMPLE; no performance or calibrated field probability claim",
      "model":"y1=s+q+e1; a=+1 if y1>=0 else -1; y2=a*s+q+e2; ei iid N(0,1)",
      "conditional_policy_parameter_free":True,
      "realized_information_is_not_unconditional_fisher":True,
      "rows":rows,
      "quadrature_positive_half_mass":mass,
      "contrast_noise_mean_given_action_plus_at_s_q_zero":contrast_noise_mean_given_plus,
      "contrast_noise_variance_given_action_plus_at_s_q_zero":contrast_noise_variance_given_plus,
      "naive_fixed_design_contrast_mean":0.,
      "naive_fixed_design_contrast_variance":2.,
      "covariance_action_coefficient_and_contrast_noise":-expected_mean,
      "closed_loop_fisher_at_zero":1.5,
      "mean_pointwise_schur_at_zero":1.,
      "status":"PASS",
    }
    Path(__file__).with_name("ADAPTIVE_INFORMATION_AUDIT_RESULTS.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
