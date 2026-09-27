import unittest,json,tempfile,sys
from pathlib import Path
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pmfs_brg.model import *
from pmfs_brg.features import *
from pmfs_brg.bank import TemplateBank
from pmfs_brg.runtime import InferenceSession

class Tests(unittest.TestCase):
 def setUp(self):
  torch.set_num_threads(1);torch.manual_seed(17)
  self.model=CandidateBRG(ModelConfig(hidden=12));self.model.eval()
  self.o=torch.rand(2,5,3);self.c=torch.rand(2,5,6,6)
 def bank(self):
  meta=dict(width=3,height=2,resolution=1.,origin_x=0.,origin_y=0.,height_m=.2,footprint_x_m=.2,footprint_y_m=.2)
  return TemplateBank(meta,['a','b'],[[.5,.5],[2.5,1.5]],[0,5],[[.8,.4,.1,0,0,0],[0,0,.2,.3,.4,.9]],[[4,2,1,0,0,0],[0,0,1,2,3,5]])
 def session(self):
  m=CandidateBRG(ModelConfig(hidden=12));meta={'feature_config':asdict(FeatureConfig()),'deployment_status':'OPEN_WARMSTART_NOT_VALIDATED_CLOSED_LOOP','max_tested_history':10}
  ss=InferenceSession(m,meta,self.bank(),True);ss.reset('run',ss.bank.fingerprint);return ss
 def event(self,eid=0,t=1):return dict(run_id='run',event_id=eid,time_s=t,x=.5,y=.5,z=.2,concentration_ppm=.2)
 def test_01_probability_mass(self):
  q=log_posterior(self.model(self.o,self.c)).exp();self.assertTrue(torch.allclose(q.sum(-1),torch.ones(2,5)))
 def test_02_stream_batch(self):
  z=self.model(self.o,self.c);h=self.model.initial(2,6);out=[]
  for t in range(5):v,h=self.model.step(self.o[:,t],self.c[:,t],h);out.append(v)
  torch.testing.assert_close(z,torch.stack(out,1),rtol=0,atol=0)
 def test_03_no_future(self):
  x=self.o.clone();x[:,3:]+=9
  torch.testing.assert_close(self.model(x,self.c)[:,:3],self.model(self.o,self.c)[:,:3],rtol=0,atol=0)
 def test_04_permutation(self):
  perm=torch.tensor([3,0,5,4,2,1]);z=self.model(self.o,self.c)
  torch.testing.assert_close(self.model(self.o,self.c[:,:,perm]),z[:,:,perm],rtol=1e-5,atol=1e-6)
 def test_05_support_counts(self):
  for n in [6,168,624]:self.assertEqual(self.model(torch.zeros(1,1,3),torch.zeros(1,1,n,6)).shape,(1,1,n))
 def test_06_bounded_gates(self):
  a=1+.5*torch.tanh(self.model.feedback(torch.randn(20,24)*100));self.assertTrue((a>=.5).all() and (a<=1.5).all())
 def test_07_nonfinite_reject(self):
  self.o[0,0,0]=float('nan')
  with self.assertRaises(ValueError):self.model(self.o,self.c)
 def test_08_mask(self):
  valid=torch.tensor([[1,1,0,0,0],[1,1,0,0,0]],dtype=torch.bool);z=self.model(self.o,self.c,valid)
  torch.testing.assert_close(z[:,2:],z[:,1:2].expand(-1,3,-1))
 def test_09_extreme_features(self):
  o,c=encode([0,1e30],[[0,0],[1,1]],[[0,1],[1,0]],np.ones((2,2))*.5,np.array([[0,1e30],[1e20,1]]))
  self.assertTrue(np.isfinite(o).all() and np.isfinite(c).all());self.assertEqual(c[0,0,1],0)
 def test_10_prior_once(self):
  p=torch.tensor([.1,.2,.3,.4]);q=log_posterior(torch.zeros(4),p).exp();torch.testing.assert_close(q,p)
 def test_11_projection(self):
  b=self.bank();p,u=b.project([[.5,.5]]);self.assertAlmostEqual(p[0,0],.8);self.assertAlmostEqual(u[0,1],0)
 def test_12_footprint_reject(self):
  with self.assertRaises(ValueError):self.bank().project([[-.1,0]])
 def test_13_planner_cache(self):
  b=self.bank();q=np.array([.1,.9]);src,v=b.planner_maps(q);expected=q[0]*q[1]*(b.p[0]-b.p[1])**2
  np.testing.assert_allclose(v,expected,atol=1e-15);self.assertAlmostEqual(src.sum(),1)
 def test_14_bank_save(self):
  b=self.bank()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bank.npz';b.save(p);self.assertEqual(b.fingerprint,TemplateBank.load(p).fingerprint)
 def test_15_duplicate_event(self):
  s=self.session();a=s.observe(self.event());b=s.observe(self.event());self.assertEqual(a,b);self.assertEqual(s.count,1)
 def test_16_duplicate_corrupt(self):
  s=self.session();s.observe(self.event());e=self.event();e['concentration_ppm']=.3
  with self.assertRaises(ValueError):s.observe(e)
 def test_17_no_truth_context(self):
  s=self.session();e=self.event();e['true_source']='a'
  with self.assertRaises(ValueError):s.observe(e)
 def test_18_order(self):
  s=self.session();s.observe(self.event());s.observe(self.event(1,2))
  with self.assertRaises(ValueError):s.observe(self.event())
 def test_19_bank_id(self):
  s=self.session()
  with self.assertRaises(ValueError):s.reset('run','wrongbank')
 def test_20_checkpoint(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'m.pt';save_checkpoint(p,self.model,{});m,_=load_checkpoint(p);torch.testing.assert_close(m(self.o,self.c),self.model(self.o,self.c))
 def test_21_warmstart_explicit(self):
  with self.assertRaises(ValueError):InferenceSession(self.model,{'feature_config':asdict(FeatureConfig())},self.bank())
 def test_22_no_batchnorm(self):self.assertFalse(any(isinstance(m,torch.nn.modules.batchnorm._BatchNorm) for m in self.model.modules()))
 def test_23_candidate_common_cue(self):
  c=self.c[:,:,0:1].expand(-1,-1,6,-1);z=self.model(self.o,c)
  torch.testing.assert_close(z,z[:,:,0:1].expand_as(z),rtol=0,atol=0)
 def test_24_duplicate_source_reject(self):
  b=self.bank()
  with self.assertRaises(ValueError):TemplateBank(b.meta,['a','a'],b.xy,b.cells,b.p,b.u)
 def test_25_height(self):
  s=self.session();e=self.event();e['z']=1
  with self.assertRaises(ValueError):s.observe(e)
 def test_26_shared_parameter_gradients(self):
  self.model.train();loss=torch.nn.functional.cross_entropy(self.model(self.o,self.c)[:,-1],torch.tensor([0,1]));loss.backward()
  self.assertGreater(float(self.model.feedback.weight.grad.abs().sum()),0)
 def test_27_constant_presence_footprint_physical_bounds(self):
  b=self.bank();b.p[:]=1.;b.u[:]=7.
  p,u=b.project([[.5,.5],[1.7,.8]],(.2,.2))
  self.assertTrue((p<=1).all() and (p>=0).all())
  np.testing.assert_allclose(p,np.ones_like(p),atol=1e-14,rtol=0)
  np.testing.assert_allclose(u,np.full_like(u,7.),atol=1e-13,rtol=0)
  encode([0,1],[[.5,.5],[1.7,.8]],b.xy,p,u)
if __name__=='__main__':unittest.main(verbosity=2)
