"""Metamorphic checks for causal local predictor feature invariants."""
import copy
import numpy as np
from m2_cpo.local_prediction import features, LocalResidualRidge


def main():
    prefix=[dict(gas_ppm=i*.01,pose_xy=[i*.1,.5],wind_uv=[.2,-.1]) for i in range(10)]
    route=[[1.+i*.1,.5+i*.02] for i in range(20)]
    x=features(prefix,route)
    shifted=copy.deepcopy(prefix)
    for r in shifted:
        r['pose_xy']=[r['pose_xy'][0]+123,r['pose_xy'][1]-45]
        r['source_xyz_m']=object();r['future_gas']=object();r['house']=object()
    moved=[[r[0]+123,r[1]-45] for r in route]
    assert np.allclose(x,features(shifted,moved),atol=1e-12)
    def rotate(p): return [-p[1],p[0]]
    rotated=copy.deepcopy(prefix)
    for r in rotated: r['pose_xy']=rotate(r['pose_xy']);r['wind_uv']=rotate(r['wind_uv'])
    assert np.allclose(x,features(rotated,[rotate(r) for r in route]),atol=1e-12)
    assert np.array_equal(features(prefix,route,include_route=False),features(prefix,moved,include_route=False))
    model=LocalResidualRidge().fit(x,np.zeros(len(x)))
    assert np.array_equal(model.predict(x,.4),np.full(len(x),.4))
    print('CSTAR_M2_LOCAL_FEATURE_INVARIANTS_PASS')


if __name__=='__main__': main()
