import unittest
import numpy as np
from source_map_tools import *
class Tests(unittest.TestCase):
 def test_native(self):
  s=native_log_score([1,0],[1,1],[[1,0],[0,1]],[1,1]);np.testing.assert_allclose(s,[0,2*np.log(.6)])
 def test_event_equivalence(self):
  x=np.ones((2,2,50));s=event_composite_log_score(x,np.ones(50));np.testing.assert_array_equal(s[:1],s[1:])
  np.testing.assert_allclose(normalized_source_weights(s,[.5,.5]),[.5,.5])
 def test_prior_and_raster(self):
  ids=np.array([0,0,0,1,1,-1]);m=np.array([1,1,1,1,1,0],bool)
  w=normalized_source_weights([0,0],[.6,.4]);r=rasterize_source_mass(w,ids,m);np.testing.assert_allclose(r[:5],.2)
 def test_missing_cell_rejected(self):
  with self.assertRaises(ValueError):rasterize_source_mass([.5,.5],[0,-1],[1,1])
 def test_prob_range(self):
  with self.assertRaises(ValueError):native_log_score([1],[1],[[1.1]],[1])
 def test_order_equivariance(self):
  s=np.array([2.,0.,-1.]);p=np.array([.2,.4,.4]);o=[2,0,1]
  np.testing.assert_allclose(normalized_source_weights(s,p)[o],normalized_source_weights(s[o],p[o]))
 def test_constant_shift(self):
  q=score_perturbation([1,3,2],[8,10,9]);self.assertEqual(q['range_delta'],0)
 def test_no_contract_drift(self):
  a={'threshold':.1,'model':{'readout':'O0'}};b={'threshold':.1,'model':{'readout':'O1'}}
  self.assertEqual(contract_diff(a,b,['model.readout']),['model.readout'])
  b['threshold']=.2
  with self.assertRaises(ValueError):contract_diff(a,b,['model.readout'])
if __name__=='__main__':unittest.main()
