import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import unittest
import numpy as np
import torch
from training_contract import *

class ContractTests(unittest.TestCase):
    def windows(self):
        return [Window(0,0.,2.,0.,0.,10), Window(1,2.,4.,0.,0.,10), Window(2,8.,10.,3.,0.,10)]
    def test_online_offline_equal(self):
        batch = encode_timing(self.windows(),0.,(0.,0.))
        online = TimingEncoder(0.,(0.,0.))
        np.testing.assert_array_equal(batch,np.stack([online.push(w) for w in self.windows()]))
    def test_same_location_new_event_is_valid(self):
        x=encode_timing(self.windows(),0.,(0.,0.))
        self.assertEqual(x[0,2],0.);self.assertEqual(x[1,2],0.)
    def test_clock_gap_changes_feature(self):
        a=encode_timing([Window(0,0.,2.,0.,0.,10)],0.,(0.,0.))
        b=encode_timing([Window(0,4.,6.,0.,0.,10)],0.,(0.,0.))
        self.assertNotEqual(a[0,0],b[0,0]);self.assertEqual(a[0,1],b[0,1])
    def test_no_overlap(self):
        e=TimingEncoder(0.,(0.,0.));e.push(self.windows()[0])
        with self.assertRaises(ValueError):e.push(Window(1,1.,3.,0.,0.,10))
    def test_no_duplicate(self):
        e=TimingEncoder(0.,(0.,0.));e.push(self.windows()[0])
        with self.assertRaises(ValueError):e.push(self.windows()[0])
    def test_no_future_budget(self):
        with self.assertRaises(ValueError):encode_timing([Window(0,299.,301.,0.,0.,10)],0.,(0.,0.))
    def test_append_preserves_original(self):
        old=np.array([[1,2,3],[4,5,6],[7,8,9]],dtype=np.float32)
        new=append_timing(old,encode_timing(self.windows(),0.,(0.,0.)))
        np.testing.assert_array_equal(new[:,:3],old);self.assertEqual(new.shape,(3,6))
    def test_invalid_truth_not_remapped(self):
        with self.assertRaises(ValueError):prefix_nll(torch.zeros(2,3),3)
    def test_candidate_permutation(self):
        z=torch.tensor([[1.,3.,2.],[.4,.7,.1]],dtype=torch.float64)
        torch.testing.assert_close(prefix_nll(z,1),prefix_nll(z[:,[2,0,1]],2))
    def test_episode_length_not_double_weighted(self):
        z=torch.tensor([[1.,3.,2.]],dtype=torch.float64)
        torch.testing.assert_close(prefix_nll(z,1),prefix_nll(z.repeat(100,1),1))
    def test_routes_not_independent_source_weight(self):
        f=lambda v:torch.tensor(float(v))
        a=source_plume_balanced_reduce([f(1),f(3)],['s1','s2'],['p1','p2'])
        b=source_plume_balanced_reduce([f(1),f(1),f(3)],['s1','s1','s2'],['p1','p1','p2'])
        torch.testing.assert_close(a,b)
    def test_mask_valid(self):
        z=torch.tensor([[1.,0.],[0.,1.]],dtype=torch.float64)
        torch.testing.assert_close(prefix_nll(z,0,torch.tensor([1,0])),prefix_nll(z[:1],0))
    def test_source_split_order_invariant(self):
        keys=[f'H02/pair{i}' for i in range(12)]
        self.assertEqual(deterministic_source_split(keys,'fixed',2,2),deterministic_source_split(keys[::-1],'fixed',2,2))
    def test_leakage_rejected(self):
        row=dict(house='House02',split='train',source_group='a',plume_group='p',same_sensor_pipeline=True)
        with self.assertRaises(ValueError):validate_rows([row,{**row,'split':'dev','plume_group':'p2'}])
    def test_h03_not_training_source(self):
        with self.assertRaises(ValueError):validate_rows([dict(house='House03',split='train',source_group='a',plume_group='p',same_sensor_pipeline=True)])
    def test_var_zero_does_not_establish_truth(self):
        xy=np.array([[0.,0.],[10.,0.]])
        q=np.array([1.,0.]);mean=q@xy;variance=np.sum(q*np.sum((xy-mean)**2,axis=1))
        self.assertEqual(variance,0.);self.assertEqual(np.linalg.norm(mean-xy[1]),10.)
    def test_temperature_cannot_change_uniform_prior_argmax(self):
        z=torch.tensor([-2.,1.,.5])
        self.assertEqual(int((z/.3).argmax()),int((z/4.).argmax()))

if __name__=='__main__':unittest.main(verbosity=2)
