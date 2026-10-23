from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PairedAction:
    name:str
    center:tuple[float,float]
    angle_rad:float
    separation_m:float
    dwell_s:float
    cost_s:float

    @property
    def points(self):
        u=np.array([np.cos(self.angle_rad),np.sin(self.angle_rad)])
        return np.array(self.center)[None,:]+np.array([[1.],[-1.]])*self.separation_m/2*u


def legal_pair(points,bounds,obstacle_rectangles=(),minimum_separation=0.5):
    p=np.asarray(points,dtype=float)
    if p.shape!=(2,2) or not np.isfinite(p).all():return False
    lo,hi=np.asarray(bounds,dtype=float)
    if np.any(p<lo) or np.any(p>hi) or np.linalg.norm(p[0]-p[1])<minimum_separation:return False
    for x0,y0,x1,y1 in obstacle_rectangles:
        if np.any((p[:,0]>=x0)&(p[:,0]<=x1)&(p[:,1]>=y0)&(p[:,1]<=y1)):return False
    return True


def segment_clear(start,end,bounds,obstacle_rectangles=(),step=0.05):
    x=np.asarray(start,dtype=float);y=np.asarray(end,dtype=float)
    if step<=0 or x.shape!=(2,) or y.shape!=(2,) or not np.isfinite([x,y]).all():return False
    lo,hi=np.asarray(bounds,dtype=float)
    if np.any(x<lo) or np.any(x>hi) or np.any(y<lo) or np.any(y>hi):return False
    # Exact slab intersection; step retained for API compatibility, not a
    # discretization that could miss a thin obstacle.
    d=y-x
    for xmin,ymin,xmax,ymax in obstacle_rectangles:
        t0,t1=0.,1.
        for k,(mn,mx) in enumerate(((xmin,xmax),(ymin,ymax))):
            if abs(d[k])<1e-15:
                if not mn<=x[k]<=mx:t0,t1=1.,0.;break
            else:
                a,b=(mn-x[k])/d[k],(mx-x[k])/d[k]
                t0=max(t0,min(a,b));t1=min(t1,max(a,b))
        if t0<=t1:return False
    return True


def make_actions(centers,separations=(1.,),angles=(0.,np.pi/2),anchor=(0.,0.),speed=1.,dwell=2.,bounds=((-5.,-5.),(8.,8.))):
    out=[];anchor=np.asarray(anchor)
    for ci,c in enumerate(centers):
        for d in separations:
            for ai,theta in enumerate(angles):
                center=np.asarray(c)
                u=np.array([np.cos(theta),np.sin(theta)])
                points=center+np.array([[1.],[-1.]])*d/2*u
                if not legal_pair(points,bounds,minimum_separation=.5):continue
                # Both aircraft return to their declared anchor formation.
                # Unit cost is wall time; UAV seconds are recorded separately.
                homes=anchor+np.array([[.4,0],[-.4,0]])
                flight=2*np.ceil(np.max(np.linalg.norm(points-homes,axis=1))/speed/.1)*.1
                out.append(PairedAction(f"c{ci}_d{d:g}_a{ai}",tuple(center),float(theta),float(d),float(dwell),float(flight+dwell)))
    return out


def simultaneous_paths_clear(starts,ends,bounds,obstacles=(),minimum_separation=.5):
    starts=np.asarray(starts,dtype=float);ends=np.asarray(ends,dtype=float)
    if starts.shape!=(2,2) or ends.shape!=(2,2):return False
    if not all(segment_clear(starts[i],ends[i],bounds,obstacles) for i in range(2)):return False
    separation=starts[0]-starts[1]
    change=(ends[0]-ends[1])-separation
    denom=float(change@change)
    u=0. if denom==0 else float(np.clip(-(separation@change)/denom,0,1))
    return bool(np.linalg.norm(separation+u*change)>=minimum_separation-1e-12)

