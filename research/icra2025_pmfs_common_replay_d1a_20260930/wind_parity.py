"""Vector-angle/raster parity from explicit downwind/upwind conventions; no model inference."""
import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'comparison_work/vgr_adapter'))
from official_three_channel import official_functions
def device_clockwise_degree(flow_world_xy,quaternion_xyzw):
    flow=np.array([*flow_world_xy,0.],float)
    if np.linalg.norm(flow[:2])==0:return None
    # Native calls its map-frame angle downWind_direction. Paper Eq3 labels +dot upwind.
    # Thus the official sensor vector must point opposite the transport velocity.
    upwind_robot=Rotation.from_quat(quaternion_xyzw).inv().apply(-flow)
    return -math.degrees(math.atan2(upwind_robot[1],upwind_robot[0]))
def main():
    f=official_functions();results=[]
    for deg in [0,180,90,-90,45,135,-135,-45]:
        vector=np.array([math.cos(math.radians(deg)),math.sin(math.radians(deg))])
        for robot_yaw in [0,45,90,-90]:
            q=Rotation.from_euler('z',robot_yaw,degrees=True).as_quat()
            clockwise=device_clockwise_degree(vector,q)
            # Upstream int() truncation needs floating-point boundary handling explicitly.
            # Values within1e-10 of an integer are canonicalized, not rounded arbitrary angles.
            if abs(clockwise-round(clockwise))<1e-10:clockwise=float(round(clockwise))
            yaw=f['sensor_direction_in_world'](*q,-math.radians(int(clockwise)))
            raster=np.zeros((279,279));raster[139,139]=1
            image=f['mark_wind_direction'](raster,yaw)
            yy,xx=np.indices(image.shape);dot=(xx-139)*(-vector[0])+(yy-139)*(-vector[1])
            safe=np.abs(dot)>1e-8
            assert np.array_equal(image[safe],np.where(dot[safe]>=0,1.,-1.))
            rebuilt=np.array([math.cos(yaw),math.sin(yaw)])
            assert np.dot(rebuilt,-vector)>1-1e-12
            results.append(dict(flow_world_degree=deg,robot_yaw_degree=robot_yaw,
                quaternion_xyzw=q.tolist(),device_clockwise_degree=clockwise,
                reconstructed_world_upwind_degree=math.degrees(yaw),raster_nonboundary_parity=True))
    assert device_clockwise_degree([0,0],[0,0,0,1]) is None
    out=ROOT/'freeze';out.mkdir(exist_ok=True)
    obj=dict(decision='D1A_WIND_CONVENTION_PASS',vector_quaternion_cases=len(results),
        authoritative_native='Algorithm::windCallback names map-frame vector downWind_direction; VGR publishes atan2(v,u)',
        authoritative_official='paper Eq3 and text: positive halfplane is upwind; code rotates device vector and assigns +1 for positive dot',
        mapping='device clockwise = -atan2(R(q)^-1(-flow_world)) in degrees',
        quantization='preserve upstream int-degrees; only canonicalize numerical representations of exact integers',
        no_wind='zero velocity -> sentinel None -> zero contribution',cases=results)
    (out/'WIND_VECTOR_ANGLE_PARITY.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    print(obj['decision'],len(results),'vector/quaternion cases')
if __name__=='__main__':main()
