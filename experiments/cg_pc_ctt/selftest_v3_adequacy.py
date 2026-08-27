#!/usr/bin/env python3
"""Synthetic regression for V3 observation adequacy."""
import numpy as np
from v3_adequacy import candidate_predictive_adequacy, family_predictive_adequacy

rng=np.random.default_rng(20260827)
M,E=8,12
base=rng.normal(size=E)
v=rng.normal(size=E); v/=np.linalg.norm(v)
coef=np.linspace(-1,1,M)
Z=base[None,:]+0.2*coef[:,None]*v[None,:]

# Observation generated inside the predictive family.
y_good=base+0.05*v
g=candidate_predictive_adequacy(Z,y_good)
assert g["residual_in_member_span_fraction"]>0.999
assert g["relative_center_distance"]<1.0

# Shared systematic wrong bias orthogonal to member variation.
w=rng.normal(size=E); w-=v*(v@w); w/=np.linalg.norm(w)
y_bad=base+2.0*w
b=candidate_predictive_adequacy(Z,y_bad)
assert b["residual_in_member_span_fraction"]<1e-8
assert b["relative_center_distance"]>100.0
assert b["nearest_member_relative_distance"]>10.0

# A family with one good candidate should beat a reproducibly wrong candidate.
P=np.stack([Z, Z+3*w[None,:]],axis=0)
rows,s=family_predictive_adequacy(P,y_good)
assert s["best_candidate_by_relative_center_distance"]==0

print("CG_PC_CTT_V3_ADEQUACY_SELFTEST PASS")
