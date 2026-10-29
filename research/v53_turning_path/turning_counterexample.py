#!/usr/bin/env python3
"""V53 analytic source–wind ambiguity certificate; not GADEN or a gas likelihood."""
import math, json, numpy as np

def certificate(U=1., L=4., kappa=.1, wind_sigma=.1):
    assert U>0 and L>0 and wind_sigma>0
    t=L/U
    x=np.linspace(0,L,40001)
    yA=float(np.trapezoid(kappa*x/U,x))
    yB=-kappa*L*L/(2*U)+kappa*L*t
    local=np.array([U,kappa*L])
    wrong=yA-kappa*L*t
    kl=lambda xi:(kappa*(xi-L))**2/(2*wind_sigma**2)
    bayes_error=lambda xi:0.5*math.erfc(abs(kappa*(xi-L))/(2*wind_sigma*math.sqrt(2)))
    assert abs(yA-yB)<1e-9 and abs(yA-kappa*L*L/(2*U))<1e-9
    assert abs(wrong+kappa*L*L/(2*U))<1e-9
    assert abs(kl(L))<1e-9
    return dict(endpoint=[L,yA],source_A=[0.,0.],source_B=[0.,wrong],
                local_wind=local.tolist(),backtrace_source=[0.,wrong],
                backtrace_bias=abs(wrong),KL_current=kl(L),KL_upstream=kl(0.),
                Bayes_error_current=bayes_error(L),Bayes_error_upstream=bayes_error(0.),
                assumptions="single particle endpoint and local wind, two known static divergence-free wind alternatives; no concentration distribution")

if __name__=="__main__":
    z=certificate()
    assert abs(z["backtrace_bias"]-.8)<1e-9
    assert abs(z["KL_upstream"]-8.)<1e-9
    print(json.dumps(z,ensure_ascii=False,indent=2))
