"""Source-blind causal local residual baseline, not a causal-innovation claim.

Train-only linear shrinkage asks whether route geometry adds predictive value
to measured gas history. No absolute coordinates, House identity, source
truth or future wind are features. Outputs are marginal log-ppm means only;
this baseline is not a normalized first-passage law or a full CPO provider.
"""
import math
import numpy as np


def features(prefix,route_xy,dt=.2,include_route=True):
    if not prefix or not route_xy: raise ValueError('CSTAR_LOCAL_EMPTY_INPUT')
    gas=np.array([math.log1p(float(r['gas_ppm'])) for r in prefix])
    if not np.isfinite(gas).all(): raise ValueError('CSTAR_LOCAL_INVALID_GAS')
    current=float(gas[-1]); window=gas[-min(len(gas),10):]
    slope=(float(window[-1])-float(window[0]))/max(dt,(len(window)-1)*dt)
    mean=float(window.mean()); std=float(window.std())
    wind=np.array(prefix[-1]['wind_uv'],dtype=float)
    speed=float(np.linalg.norm(wind)); direction=wind/max(speed,1e-8)
    displacement=np.array(route_xy,dtype=float)-np.array(prefix[-1]['pose_xy'])
    t=np.arange(1,len(route_xy)+1)*dt
    # Common part: local persistence, temporal drift, short-memory variability.
    columns=[np.ones(len(t)),t,t*t,current*t,slope*t,slope*t*t,(mean-current)*t,std*t,speed*t]
    if include_route:
        along=displacement@direction
        cross=displacement[:,0]*direction[1]-displacement[:,1]*direction[0]
        distance=np.linalg.norm(displacement,axis=1)
        columns += [along,cross,distance,along*current,cross*current,distance*current,
                    along*slope,cross*slope,along*t,cross*t]
    return np.stack(columns,axis=1)


class LocalResidualRidge:
    """Fixed ridge=1 under mean-square feature scaling; fit train Houses only."""
    def fit(self,x,y):
        self.center=x.mean(axis=0); self.center[0]=0.
        self.scale=x.std(axis=0); self.scale[self.scale<1e-8]=1.
        z=(x-self.center)/self.scale
        penalty=np.eye(z.shape[1]); penalty[0,0]=0.
        self.weight=np.linalg.solve(z.T@z/len(z)+penalty,z.T@y/len(z))
        return self

    def predict(self,x,current):
        return current+(x-self.center)/self.scale@self.weight
