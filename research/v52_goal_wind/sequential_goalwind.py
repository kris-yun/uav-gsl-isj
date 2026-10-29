"""V52: exact sequential source-marginal wind scoring for ONE static Gaussian wind factor.
This is a numerical reference, NOT a 3-D meteorological or gas transport solver.
Inputs (Pss,C) must come from the SAME gas+wind-conditioned posterior.
Observation blocks are independent given static z; all dynamic or correlated-noise
cases require a different joint state-space model.
"""
import numpy as np

def arr(x,dim):
    a=np.asarray(x,dtype=float)
    if a.ndim!=dim or not np.all(np.isfinite(a)):raise ValueError("nonfinite/wrong shape")
    return a

def chol(a):
    a=arr(a,2)
    if a.shape[0]!=a.shape[1] or not np.allclose(a,a.T,atol=1e-10):raise ValueError("not symmetric")
    return np.linalg.cholesky(a)

class StaticGoalWindHistory:
    def __init__(self,source_mean,source_cov,source_wind_cross):
        self.s0=arr(source_mean,1);self.Pss=arr(source_cov,2);self.C=arr(source_wind_cross,2)
        self.r=self.C.shape[1];self.m=self.s0.size
        if self.Pss.shape!=(self.m,self.m) or self.C.shape[0]!=self.m:raise ValueError("joint dimensions")
        if np.linalg.eigvalsh(self.Pss-self.C@self.C.T).min() < -1e-9:raise ValueError("invalid joint covariance")
        self.W=np.zeros((0,self.r));self.y=np.zeros(0);self.ids=set();self.L=None

    def solve(self, rhs):
        if self.L is None:return np.asarray(rhs,float).copy()
        return np.linalg.solve(self.L.T,np.linalg.solve(self.L,rhs))

    def current(self):
        if not len(self.y):return self.s0.copy(),self.Pss.copy()
        B=self.C@self.W.T
        return (self.s0+B@self.solve(self.y),
                self.Pss-B@self.solve(B.T))

    def candidate(self,A,R):
        A=arr(A,2);chol(R);R=arr(R,2)
        if A.shape[1]!=self.r or R.shape!=(A.shape[0],A.shape[0]):raise ValueError("candidate dims")
        D=self.W@A.T
        cross=self.C@A.T-(self.C@self.W.T)@self.solve(D)
        S=R+A@A.T-D.T@self.solve(D)
        L=chol((S+S.T)/2)
        U=np.linalg.solve(L,cross.T)
        gain=U.T@U
        _,P=self.current()
        Pnew=(P-gain+P.T-gain.T)/2
        return {"cross":cross,"innovation_covariance":S,"source_trace_reduction":float(np.trace(gain)),
                "source_covariance_after":Pnew}

    def append(self,A,R,y,record_id):
        if record_id in self.ids:raise ValueError("duplicate raw observation ID")
        A=arr(A,2);y=arr(y,1);L=chol(R)
        if A.shape[1]!=self.r or A.shape[0]!=len(y):raise ValueError("observation dimensions")
        wb=np.linalg.solve(L,A);yb=np.linalg.solve(L,y)
        Wnew=np.vstack([self.W,wb]);ynew=np.hstack([self.y,yb])
        Lnew=chol(np.eye(len(ynew))+Wnew@Wnew.T)
        self.W,self.y,self.L=Wnew,ynew,Lnew;self.ids.add(record_id)
        return self.current()
