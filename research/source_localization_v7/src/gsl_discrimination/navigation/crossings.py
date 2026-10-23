"""A causal occupancy crossing detector, with no future run merging."""
from __future__ import annotations
from ..m2_boundary import BoundaryEvent


class CrossingDetector:
    def __init__(self,minimum_pre_s=.2,minimum_post_s=.2):
        if min(minimum_pre_s,minimum_post_s)<=0:raise ValueError("positive dwell thresholds required")
        self.pre=minimum_pre_s;self.post=minimum_post_s
        self.state=None;self.run_start=None;self.pending=None;self.last=None

    def update(self,time_s,detected):
        if self.last is not None and time_s<=self.last:raise ValueError("crossing clock must advance")
        self.last=float(time_s);detected=bool(detected)
        if self.state is None:
            self.state=detected;self.run_start=time_s;return None
        if detected!=self.state:
            previous=time_s-self.run_start
            self.pending=(time_s,previous,'entry' if detected else 'exit') if previous+1e-9>=self.pre else None
            self.state=detected;self.run_start=time_s
        if self.pending and time_s-self.pending[0]+1e-9>=self.post:
            t,pre,kind=self.pending;self.pending=None
            return BoundaryEvent(kind,t,pre,float(time_s-t))
        return None

