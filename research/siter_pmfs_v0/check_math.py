"""Checks independent of experimental truth or terminal outcomes."""
import json
import numpy as np
from fit_loho import loss_gradient, solve, transform
from prepare_features import features


def run():
    rng=np.random.default_rng(20261001)
    d=rng.normal(size=(21,4));o=rng.normal(size=21);w=np.ones(21)/21;a=np.array([.1,.2,.3,.4])
    loss,gradient=loss_gradient(a,o,d,w)
    finite=np.array([(loss_gradient(a+np.eye(4)[i]*1e-6,o,d,w)[0]-loss_gradient(a-np.eye(4)[i]*1e-6,o,d,w)[0])/2e-6 for i in range(4)])
    assert np.max(abs(finite-gradient))<1e-8
    optimum,value,_=solve(o,d,w)
    assert value<=loss+1e-10 and abs(optimum.sum()-1)<1e-8 and optimum.min()>=-1e-10
    x=rng.normal(size=(30,4));lo=x.min(0);hi=x.max(0)
    c=transform(x,lo,hi);energy=c@optimum
    assert energy.min()>=-1e-10 and energy.max()<=1+1e-10
    # Zero confidence cannot manufacture residual or flow evidence.
    p=rng.random(5);hit=rng.random((3,5));wind=rng.normal(size=(5,2));xy=rng.normal(size=(5,2));source=rng.normal(size=(3,2));owner=np.array([0,0,1,2,2])
    f=features(np.array([1,2,3]),p,np.zeros(5),hit,wind,xy,source,owner,.1)
    evidence_columns=[1,2,3,4,5,6,8,9,10,11,12]
    assert np.all(f[:,evidence_columns]==0)
    # Geometry enters only through displacement: common translation leaves descriptors unchanged.
    f1=features(np.array([1,2,3]),p,np.ones(5),hit,wind,xy,source,owner,.1)
    f2=features(np.array([1,2,3]),p,np.ones(5),hit,wind,xy+7,source+7,owner,.1)
    assert np.max(abs(f1-f2))<1e-12
    # Missing training variance is explicitly zero, not inferred from test data.
    assert np.all(transform(np.ones((3,4))*10,np.ones(4),np.ones(4))==0)
    return {"pass":True,"analytic_gradient_max_abs":float(np.max(abs(finite-gradient))),"checks":["pairwise_gradient","simplex_optimizer","bounded_one_sided_energy","zero_confidence_no_evidence","common_translation_no_absolute_coordinate_feature","training_constant_scaling"]}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
