"""Online target-marginal kernel; not a physical forward solver.
See CODEX_START_HERE.md for joint-model and residual-covariance conditions.
"""
from dataclasses import dataclass
import numpy as np

def sym(M):return (M+M.T)/2

def cov_check(M,name):
    M=np.asarray(M,dtype=float)
    if M.ndim!=2 or M.shape[0]!=M.shape[1] or not np.isfinite(M).all():raise ValueError(name+' must be finite square')
    if not np.allclose(M,M.T,atol=1e-10,rtol=1e-10):raise ValueError(name+' must be symmetric')
    if np.linalg.eigvalsh(M).min() < -1e-9*max(1.,np.linalg.norm(M,2)):raise ValueError(name+' must be PSD')
    return M


@dataclass
class FactorGoalWind:
    """Online kernel in an ALREADY whitened, retained wind coefficient space.

    wind=L z, z~N(0,I_r), Cov(source,z)=C. Candidate A=H L is supplied by
    evaluation of the basis at proposed sensor points; this class never builds
    a full spatial covariance. Residual *within* this declared factor model is
    marginalized. Additional outside-basis uncertainty belongs in R/ensemble
    and cannot be certified by this class.
    """
    Pss: np.ndarray
    C: np.ndarray

    def __post_init__(self):
        self.Pss=cov_check(self.Pss,'Pss');self.C=np.asarray(self.C,float)
        if self.C.ndim!=2 or self.C.shape[0]!=len(self.Pss) or not np.isfinite(self.C).all():raise ValueError('C shape/value')
        cov_check(sym(self.Pss-self.C@self.C.T),'source residual')
        _,s,Vt=np.linalg.svd(self.C,full_matrices=False)
        tol=1e-12*(s[0] if len(s) and s[0]>0 else 1.)
        self.V=Vt[s>tol].T;self.Cz=self.C@self.V
        self.rank=self.V.shape[1]

    def update(self,A,R,innovation=None):
        A=np.asarray(A,float);R=cov_check(R,'R')
        if A.ndim!=2 or A.shape[1]!=self.C.shape[1] or not np.isfinite(A).all() or R.shape!=(len(A),len(A)):raise ValueError('A/R mismatch')
        Az=A@self.V
        Reff=sym(R+A@A.T-Az@Az.T)
        # S equals R+A A^T; no spatial D-by-D covariance is formed.
        S=sym(Reff+Az@Az.T);np.linalg.cholesky(S)
        cross=self.Cz@Az.T
        gain=sym(cross@np.linalg.solve(S,cross.T))
        ret={'posterior_source_covariance':sym(self.Pss-gain),
             'source_covariance_reduction':gain,'effective_noise':Reff,'target_rank':self.rank}
        if innovation is not None:
            e=np.asarray(innovation,float)
            if e.shape!=(len(A),) or not np.isfinite(e).all():raise ValueError('innovation shape/value')
            ret['source_mean_increment']=cross@np.linalg.solve(S,e)
        return ret
