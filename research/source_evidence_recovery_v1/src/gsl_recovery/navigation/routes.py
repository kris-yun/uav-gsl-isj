"""Bounded 2D geometric action proposals; native Nav2 collision checks remain required."""
from dataclasses import dataclass
import numpy as np
from ..types import Action

@dataclass
class RectWorld:
    bounds: tuple[float,float,float,float]=(-3.,3.,-3.,3.)
    obstacles: tuple=()
    clearance: float=.1

    def legal_point(self,xy):
        x,y=xy;x0,x1,y0,y1=self.bounds;r=self.clearance
        return x0+r<=x<=x1-r and y0+r<=y<=y1-r and not any(a-r<=x<=b+r and c-r<=y<=d+r for a,b,c,d in self.obstacles)

    def legal_segment(self,a,b):
        if not self.legal_point(a) or not self.legal_point(b):return False
        # Exact slab intersection with expanded axis-aligned rectangles.
        a=np.asarray(a,float);delta=np.asarray(b,float)-a;r=self.clearance
        for x0,x1,y0,y1 in self.obstacles:
            lo=np.array([x0-r,y0-r]);hi=np.array([x1+r,y1+r]);t0,t1=0.,1.
            for k in (0,1):
                if abs(delta[k])<1e-14:
                    if a[k]<lo[k] or a[k]>hi[k]:t0,t1=1.,0.;break
                else:
                    q=sorted(((lo[k]-a[k])/delta[k],(hi[k]-a[k])/delta[k]));t0=max(t0,q[0]);t1=min(t1,q[1])
            if t0<=t1:return False
        return True

def route_cost(actions,start=(0.,0.),speed=1.):
    if speed<=0:raise ValueError('speed must be positive')
    old=np.asarray(start,float);cost=0.
    for a in actions:
        new=np.array([a.x,a.y]);cost+=float(np.linalg.norm(new-old))/speed+a.dwell;old=new
    return cost

def action_blocks(current,now,world=None,length=5,budget=4,speed=1.,dwell=1.):
    if length<1 or length>8:raise ValueError('block length limit 1..8')
    world=world or RectWorld();x0,x1,y0,y1=world.bounds;r=world.clearance+.2
    targets=[(x0+r,y0+r),(x1-r,y0+r),(x1-r,y1-r),(x0+r,y1-r),((x0+x1)/2,y0+r),((x0+x1)/2,y1-r)]
    blocks=[]
    for target in targets:
        if not world.legal_segment(current,target):continue
        points=np.linspace(np.asarray(current,float),target,length+1)[1:]
        old=np.asarray(current,float);t=float(now);block=[]
        for xy in points:
            if not world.legal_segment(old,xy):block=[];break
            t+=float(np.linalg.norm(xy-old))/speed+dwell;block.append(Action(float(xy[0]),float(xy[1]),1.,t,dwell));old=xy
        if block:blocks.append(block)
        if len(blocks)>=budget:break
    if not blocks:raise RuntimeError('NO_LEGAL_ACTION_BLOCK')
    return blocks
