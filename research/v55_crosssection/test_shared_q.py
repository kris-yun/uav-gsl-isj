"""V55 fixed two-hypothesis Gaussian-section certificate; not a GADEN solver."""
import numpy as np
U,L,k,x,w,sd=1.,4.,.1,2.,.25,.1
a=lambda xi:k*xi*xi/(2*U)
b=lambda xi:-k*L*L/(2*U)+k*L*xi/U
ya,yb=a(x),b(x)
probe=np.array([ya,yb])
fA=np.exp(-.5*((probe-ya)/w)**2)
fB=np.exp(-.5*((probe-yb)/w)**2)
def score(y,h):
    q=max(0,float(h@y/(h@h)))
    return float(np.linalg.norm(y-q*h)**2/sd**2)
assert abs(ya-yb-.2)<1e-12
assert score(fA[:1],fB[:1])<1e-12
assert abs(score(fA,fB)-14.630626646832548)<1e-9
assert np.linalg.norm(fA-(fA/fB)*fB)<1e-12
print(dict(center_A=ya,center_B=yb,one=score(fA[:1],fB[:1]),two=score(fA,fB),independent_amplitude=0.,native_validation=False))
