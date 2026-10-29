"""Minimal executable regression for the repository's static reference.
Run: cd research/v52_goal_wind && python test_seq.py
Not a native gas source localization test.
"""
import numpy as np
from sequential_goalwind import StaticGoalWindHistory

def main():
    model=StaticGoalWindHistory(np.array([0.]),np.array([[1.]]),np.array([[.6,0.]]))
    H=np.array([[1.,1.]])
    R=np.array([[.01]])
    before=model.candidate(np.array([[0.,1.]]),R)["source_trace_reduction"]
    model.append(H,R,np.array([0.]),"obs-1")
    after=model.candidate(np.array([[0.,1.]]),R)["source_trace_reduction"]
    assert abs(before)<1e-13 and abs(after-.1738709616658)<1e-11
    # Current covariance must be updated; repeated independent noisy readings
    # cannot claim a second copy of the same prior source covariance reduction.
    second=model.candidate(H,R)["source_covariance_after"][0,0]
    assert abs(second-.8204488778054863)<1e-11
    try:
        model.append(H,R,np.array([0.]),"obs-1")
        raise AssertionError("duplicate raw record should be rejected")
    except ValueError:
        pass
    print("V52 static sequential numerical tests PASS")

if __name__=="__main__":main()
