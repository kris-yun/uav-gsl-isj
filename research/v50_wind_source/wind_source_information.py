"""Wind/source qualification utilities, not a new physical forward solver.
All linear-Gaussian results are conditional on the stated linearization,
noise covariance and model support. No source truth is accepted at runtime.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


def matrix(value, name: str) -> np.ndarray:
    x = np.asarray(value, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError(f'{name} must be a finite matrix')
    return x


def efficient_source_information(A, B_wind, C_other, D_wind, *, rtol=1e-10):
    """Whiten inputs first. dy=A ds+B_wind db+C_other dn, dz=D_wind db.
    Gives min_{db,dn} ||A ds+B db+C dn||^2+||D db||^2 via SVD.
    B and D must refer to the SAME wind coefficients across the whole history.
    No artificial independent-wind or calibration certificate is implied.
    """
    A=matrix(A,'A');B=matrix(B_wind,'B_wind');C=matrix(C_other,'C_other');D=matrix(D_wind,'D_wind')
    if A.shape[0]!=B.shape[0] or A.shape[0]!=C.shape[0] or D.shape[1]!=B.shape[1]:
        raise ValueError('Incompatible shared source/wind/nuisance Jacobians')
    if not np.isfinite(rtol) or rtol<=0:raise ValueError('rtol must be positive')
    Js=np.vstack([A,np.zeros((D.shape[0],A.shape[1]))])
    Jn=np.block([[B,C],[D,np.zeros((D.shape[0],C.shape[1]))]])
    U,s,_=np.linalg.svd(Jn,full_matrices=False)
    tol=rtol*(s[0] if s.size else 1.)
    rank=int(np.sum(s>tol));Q=U[:,:rank]
    E=Js-Q@(Q.T@Js);info=E.T@E
    return {'information':(info+info.T)/2,'residual_design':E,'nuisance_rank':rank,
            'effective_source_rank':int(np.linalg.matrix_rank(E,tol=rtol*max(1.,np.linalg.norm(Js,2))))}


@dataclass
class GaussianWindFilter:
    """Exact finite-dimensional Gaussian conditioning with explicit dynamics.
    The native GMRF mesh must supply a validated basis and measurement matrix.
    This class does not turn point interpolation into a valid global wind field.
    """
    mean: np.ndarray
    covariance: np.ndarray

    def __post_init__(self):
        self.mean=np.asarray(self.mean,float).copy();self.covariance=matrix(self.covariance,'covariance').copy()
        n=self.mean.size
        if self.mean.shape!=(n,) or not np.isfinite(self.mean).all() or self.covariance.shape!=(n,n):raise ValueError('Invalid wind state')
        self._check_psd(self.covariance)

    @staticmethod
    def _check_psd(P):
        if not np.allclose(P,P.T,atol=1e-10,rtol=1e-10) or np.linalg.eigvalsh(P).min() < -1e-10:raise ValueError('Covariance must be symmetric PSD')

    def predict(self,F,Q):
        F=matrix(F,'F');Q=matrix(Q,'Q');n=self.mean.size
        if F.shape!=(n,n) or Q.shape!=(n,n):raise ValueError('Prediction shape mismatch')
        self._check_psd(Q);self.mean=F@self.mean;self.covariance=F@self.covariance@F.T+Q
        self.covariance=(self.covariance+self.covariance.T)/2

    def update(self,H,y,R):
        H=matrix(H,'H');R=matrix(R,'R');y=np.asarray(y,float);n=self.mean.size;m=H.shape[0]
        if H.shape[1]!=n or y.shape!=(m,) or not np.isfinite(y).all() or R.shape!=(m,m):raise ValueError('Observation shape mismatch')
        self._check_psd(R)
        S=H@self.covariance@H.T+R
        np.linalg.cholesky(S) # do not hide singular or unqualified observation models
        K=np.linalg.solve(S,H@self.covariance).T
        self.mean=self.mean+K@(y-H@self.mean)
        I=np.eye(n)-K@H
        self.covariance=I@self.covariance@I.T+K@R@K.T
        self.covariance=(self.covariance+self.covariance.T)/2
        return self.mean.copy(),self.covariance.copy()


def source_variance_reduction(P,source_dim,H_wind,R):
    """Local Gaussian POSTERIOR variance reduction, not frequentist Fisher.
    P is the CURRENT JOINT covariance [source, wind], including correlation.
    A directly source-independent wind observation can still reduce source
    uncertainty through correlation established by preceding gas measurements.
    """
    P=matrix(P,'P');H=matrix(H_wind,'H_wind');R=matrix(R,'R')
    if P.shape[0]!=P.shape[1] or not 0<source_dim<P.shape[0]:raise ValueError('Invalid source dimension')
    GaussianWindFilter._check_psd(P);GaussianWindFilter._check_psd(R)
    if H.shape[1]!=P.shape[0]-source_dim or R.shape!=(H.shape[0],H.shape[0]):raise ValueError('Wind measurement mismatch')
    Psw=P[:source_dim,source_dim:];Pww=P[source_dim:,source_dim:]
    V=H@Pww@H.T+R;np.linalg.cholesky(V)
    C=Psw@H.T;gain=C@np.linalg.solve(V,C.T)
    return (gain+gain.T)/2
