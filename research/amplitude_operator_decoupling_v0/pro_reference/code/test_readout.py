import unittest
import numpy as np
from readout import rectangular_average_matrix,scale_profile_sse,ranks_and_unique_top1
class Tests(unittest.TestCase):
    def setUp(self):
        self.meta=dict(width=2,height=2,resolution=1.,origin_x=0.,origin_y=0.)
    def test_cell_exact(self):
        w=rectangular_average_matrix(self.meta,np.array([[.5,.5]]),np.array([[1.,1.]]))
        np.testing.assert_allclose(w,[[1,0,0,0]])
    def test_four_cells(self):
        w=rectangular_average_matrix(self.meta,np.array([[1.,1.]]),np.array([[1.,1.]]))
        np.testing.assert_allclose(w,[[.25,.25,.25,.25]])
    def test_constant_field(self):
        w=rectangular_average_matrix(self.meta,np.array([[.8,1.]]),np.array([[.2,.7]]))
        np.testing.assert_allclose(w@np.ones(4),[1.])
    def test_outside_not_renormalized(self):
        w=rectangular_average_matrix(self.meta,np.array([[0.,.5]]),np.array([[1.,1.]]))
        self.assertAlmostEqual(w.sum(),.5)
    def test_scale_invariance(self):
        y=np.array([2.,4.,1.]);f=np.array([[1.,2.,.5],[2.,1.,1.]])
        a,_=scale_profile_sse(y,f);b,_=scale_profile_sse(y,3*f)
        np.testing.assert_allclose(a,b,atol=1e-14)
    def test_tie_not_unique(self):
        self.assertEqual(ranks_and_unique_top1(np.array([1.,1.]),0),(1,False))
    def test_sse_equals_angle_formula(self):
        y=np.array([2.,4.,1.]);f=np.array([[1.,2.,.5],[2.,1.,1.]])
        a,_=scale_profile_sse(y,f);b=y@y-np.maximum(f@y,0)**2/np.sum(f*f,axis=1)
        np.testing.assert_allclose(a,b,atol=1e-14)
    def test_mass_partition(self):
        centers=np.array([[.5,.5],[1.5,.5],[.5,1.5],[1.5,1.5]])
        w=rectangular_average_matrix(self.meta,centers,np.ones((4,2)))
        counts=np.array([1.,2.,3.,4.])
        self.assertAlmostEqual((w@counts).sum(),counts.sum())
if __name__=='__main__':unittest.main(verbosity=2)
