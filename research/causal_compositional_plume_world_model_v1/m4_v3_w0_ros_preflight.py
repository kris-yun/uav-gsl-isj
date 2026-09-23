#!/usr/bin/env python3
"""ROS2 W0 preflight for a running GMRF-wind node.

Injects four canonical map-frame DOWNWIND observations through
AddWindObservation, then queries WindEstimation at the same source-blind free
cells. Run on a fresh GMRF instance with no prior wind observations.
"""
from __future__ import annotations

import argparse
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
from gmrf_msgs.srv import AddWindObservation, WindEstimation


def cosine(au,av,bu,bv):
    an=math.hypot(au,av); bn=math.hypot(bu,bv)
    return (au*bu+av*bv)/(an*bn) if an>0 and bn>0 else float("nan")


class W0(Node):
    def __init__(self,args):
        super().__init__("m4_v3_w0_preflight")
        self.args=args
        qos=QoSProfile(depth=1)
        qos.durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
        qos.reliability=QoSReliabilityPolicy.RELIABLE
        self.map_msg=None
        self.create_subscription(OccupancyGrid,args.map_topic,self._map_cb,qos)
        self.add_cli=self.create_client(AddWindObservation,args.add_service)
        self.est_cli=self.create_client(WindEstimation,args.est_service)

    def _map_cb(self,msg):
        if self.map_msg is None:
            self.map_msg=msg

    def wait_map(self):
        deadline=time.monotonic()+self.args.timeout
        while rclpy.ok() and self.map_msg is None and time.monotonic()<deadline:
            rclpy.spin_once(self,timeout_sec=0.1)
        if self.map_msg is None:
            raise RuntimeError("occupancy map timeout")
        return self.map_msg

    def choose_points(self,msg):
        info=msg.info
        free=[]
        # avoid outer 10% of the grid to reduce boundary effects
        x0=max(1,int(info.width*0.1)); x1=min(info.width-1,int(info.width*0.9))
        y0=max(1,int(info.height*0.1)); y1=min(info.height-1,int(info.height*0.9))
        for y in range(y0,y1):
            for x in range(x0,x1):
                if msg.data[y*info.width+x]==0:
                    wx=info.origin.position.x+(x+0.5)*info.resolution
                    wy=info.origin.position.y+(y+0.5)*info.resolution
                    free.append((wx,wy))
        if len(free)<4:
            raise RuntimeError("fewer than four interior free cells")
        # deterministic spread through the ordered free-cell set
        ids=[len(free)//8,3*len(free)//8,5*len(free)//8,7*len(free)//8]
        return [free[i] for i in ids]

    def call(self,client,request):
        if not client.wait_for_service(timeout_sec=self.args.timeout):
            raise RuntimeError(f"service unavailable: {client.srv_name}")
        fut=client.call_async(request)
        rclpy.spin_until_future_complete(self,fut,timeout_sec=self.args.timeout)
        if not fut.done() or fut.result() is None:
            raise RuntimeError(f"service call failed: {client.srv_name}")
        return fut.result()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--map-topic",default="/map")
    ap.add_argument("--add-service",default="/AddWindObservation")
    ap.add_argument("--est-service",default="/WindEstimation")
    ap.add_argument("--speed",type=float,default=0.5)
    ap.add_argument("--settle-sec",type=float,default=2.0)
    ap.add_argument("--timeout",type=float,default=10.0)
    ap.add_argument("--min-cosine",type=float,default=0.95)
    ap.add_argument("--min-ratio",type=float,default=0.5)
    ap.add_argument("--max-ratio",type=float,default=1.5)
    args=ap.parse_args()

    rclpy.init()
    node=W0(args)
    try:
        msg=node.wait_map()
        pts=node.choose_points(msg)
        directions=[0.0,math.pi/2,math.pi,-math.pi/2]
        req=AddWindObservation.Request()
        req.wind_speed=[args.speed]*4
        req.wind_direction=directions
        req.var_speed=[1e-4]*4
        req.var_direction=[1e-4]*4
        req.x_pos=[p[0] for p in pts]
        req.y_pos=[p[1] for p in pts]
        node.call(node.add_cli,req)

        deadline=time.monotonic()+args.settle_sec
        while rclpy.ok() and time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=min(0.1,max(0.0,deadline-time.monotonic())))

        q=WindEstimation.Request()
        q.x=req.x_pos; q.y=req.y_pos
        res=node.call(node.est_cli,q)

        rows=[]; passed=True
        labels=["+x","+y","-x","-y"]
        for i,(d,label) in enumerate(zip(directions,labels)):
            iu=args.speed*math.cos(d); iv=args.speed*math.sin(d)
            ou=float(res.u[i]); ov=float(res.v[i])
            c=cosine(iu,iv,ou,ov)
            ratio=math.hypot(ou,ov)/args.speed
            ok=(math.isfinite(c) and c>args.min_cosine and
                args.min_ratio<=ratio<=args.max_ratio)
            passed &= ok
            rows.append((label,pts[i],iu,iv,ou,ov,c,ratio,ok))

        print("case,x,y,in_u,in_v,out_u,out_v,cosine,magnitude_ratio,pass")
        for label,p,iu,iv,ou,ov,c,ratio,ok in rows:
            print(f"{label},{p[0]:.6f},{p[1]:.6f},{iu:.6f},{iv:.6f},"
                  f"{ou:.6f},{ov:.6f},{c:.6f},{ratio:.6f},{str(ok).lower()}")
        print("M4_V3_W0_ROS_PREFLIGHT_"+("PASS" if passed else "FAIL"))
        raise SystemExit(0 if passed else 2)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__=="__main__":
    main()
