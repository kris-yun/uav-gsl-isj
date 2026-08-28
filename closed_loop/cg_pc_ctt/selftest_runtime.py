#!/usr/bin/env python3
import numpy as np
from reversible_rank_posterior import normal_ranks, posterior

# All ties must be neutral; candidate index cannot break a tie.
assert np.allclose(normal_ranks([1,1,1,1]),0.0)

ids=["a","b","c","d"]
def ev(score,accepted=True): return {"candidate_id":ids,"score":np.asarray(score,float),"accepted":accepted}

# One accepted event cannot release a two-fold posterior.
q,m=posterior([ev([4,3,2,1])]); assert q is None and not m["released"]

# Two concordant accepted events release a posterior favoring candidate a.
q,m=posterior([ev([4,3,2,1]),ev([5,3,2,1])]); assert m["released"] and int(np.argmax(q))==0
q_ref=q.copy()

# A rejected event with arbitrarily extreme score is permanently excluded.
q2,m2=posterior([ev([4,3,2,1]),ev([1000,0,0,0],False),ev([5,3,2,1])]); assert np.allclose(q2,q_ref)

# Symmetric opposing accepted evidence must return to a uniform prior rather
# than break ties by candidate index.
q3,m3=posterior([ev([4,3,2,1]),ev([5,3,2,1]),ev([1,2,3,4]),ev([1,2,3,5])]); assert np.allclose(q3,np.ones(4)/4)
print("CG_PC_CTT_RUNTIME_SELFTEST PASS")
