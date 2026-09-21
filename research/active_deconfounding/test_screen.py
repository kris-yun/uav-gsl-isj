import itertools,unittest
import numpy as np
from screen import information,likelihood,separation_matrix,projected_fraction,heldout_metrics

class MathematicalContract(unittest.TestCase):
    def setUp(self):
        # Either observation alone is wholly confounded. The ordered pair
        # separates source through parity while the nuisance remains shared.
        self.p=np.array([[[0.,0.],[1.,1.]],[[0.,1.],[1.,0.]]])
        self.prior=np.array([.5,.5])
    def test_shared_world_complementarity(self):
        self.assertAlmostEqual(information(self.p,self.prior,[0]),0)
        self.assertAlmostEqual(information(self.p,self.prior,[1]),0)
        self.assertAlmostEqual(information(self.p,self.prior,[0,1]),np.log(2))
        self.assertAlmostEqual(separation_matrix(self.p,[0,1])[0,1],1)
        # Illegal per-observation nuisance marginalization loses the effect.
        illegal=likelihood(self.p.mean(axis=1,keepdims=True),[0,1])
        np.testing.assert_allclose(illegal[0],illegal[1])
    def test_no_source_signal(self):
        p=np.repeat(self.p[:1],2,axis=0)
        self.assertAlmostEqual(information(p,self.prior,[0,1]),0)
        self.assertAlmostEqual(separation_matrix(p,[0,1])[0,1],0)
    def test_bruteforce_profile(self):
        rng=np.random.default_rng(8);p=rng.uniform(.01,.99,(3,4,2));q=likelihood(p,[0,1])
        d=separation_matrix(p,[0,1])
        for i,j in itertools.product(range(3),repeat=2):
            brute=min(1-np.sqrt(q[i,n]*q[j,m]).sum() for n,m in itertools.product(range(4),repeat=2))
            self.assertAlmostEqual(d[i,j],brute,places=12)
        sep,rivals=heldout_metrics(p,p,0,[0,1])
        np.testing.assert_allclose(sep,[min(1-np.sqrt(q[0,n]*q[j,m]).sum() for j in [1,2] for m in range(4)) for n in range(4)],atol=1e-12)
    def test_two_scalars_three_nuisances_can_annihilate_information(self):
        b=np.array([[1.,0.,1.],[0.,1.,1.]])
        frac,rank=projected_fraction(np.array([1.,2.]),b)
        self.assertEqual(rank,2);self.assertLess(frac,1e-25)
        frac,rank=projected_fraction(np.array([1.,-1.]),np.ones((2,1)))
        self.assertEqual(rank,1);self.assertAlmostEqual(frac,1)
    def test_exact_matched_probabilities_and_monotonicity(self):
        p=np.random.default_rng(6).random((4,3,3));prior=np.ones(4)/4
        np.testing.assert_allclose(likelihood(p,[0,1]).sum(axis=-1),1)
        self.assertGreaterEqual(information(p,prior,[0,1]),information(p,prior,[0])-1e-12)
        self.assertGreaterEqual(information(p,prior,[0,1],True),information(p,prior,[0,1])-1e-12)
        self.assertTrue(np.all(separation_matrix(p,[0,1])+1e-12>=separation_matrix(p,[0])))
    def test_zero_contrast_is_not_identifiability(self):
        fraction,_=projected_fraction(np.zeros(2),np.eye(2))
        self.assertIsNone(fraction)

if __name__=='__main__':unittest.main()
