import unittest
import numpy as np
from gsl_discrimination.m1_opponent import OpponentBank,SamplingContract,calibrate_source_contrast,joint_error_kernel,apply_joint_error_channel
from gsl_discrimination.channel import FiniteChannel,JointPosterior


class OpponentTests(unittest.TestCase):
    def setUp(self):
        self.rng=np.random.default_rng(11);self.t=np.arange(21)*.1
        self.contract=SamplingContract(True,maximum_step_s=.11,bandwidth_calibrated=True)

    def test_exact_mirror_equivariance(self):
        x=self.rng.uniform(0,2,(7,21,2));b=OpponentBank.causal_default()
        e,h=b.extract(x,self.t,self.contract);er,hr=b.extract(x[...,::-1],self.t,self.contract)
        np.testing.assert_allclose(e,er);np.testing.assert_allclose(h,-hr,atol=1e-14)

    def test_static_is_just_gradient(self):
        x=np.array([[1.,3.]])
        e,h=OpponentBank().extract(x,[50.2998],SamplingContract(False))
        self.assertAlmostEqual(h[0],(np.log(2)-np.log(4))/2)
        self.assertAlmostEqual(e,(np.log(2)+np.log(4))/2)

    def test_sparse_snapshots_cannot_be_temporal(self):
        with self.assertRaisesRegex(ValueError,'BLOCKED'):
            OpponentBank.causal_default().extract(np.ones((3,2)),[50.,100.,150.],SamplingContract(False))

    def test_bad_sensor_clock_refused(self):
        with self.assertRaisesRegex(ValueError,'mimic'):
            OpponentBank.causal_default().extract(np.ones((21,2)),self.t,
                SamplingContract(True,clock_error_s=.1,maximum_step_s=.11,bandwidth_calibrated=True))

    def test_calibrated_encoding_matches_frequency(self):
        x=np.empty((1,2,1,100,1,2))
        x[0,0,0]=self.rng.uniform(.1,.3,(100,1,2))+[3.,0.]
        x[0,1,0]=self.rng.uniform(.1,.3,(100,1,2))+[0.,3.]
        m=calibrate_source_contrast(x,[0.],SamplingContract(False),[[0,0],[1,0]],['a'],['s0','s1'],[1.])
        self.assertEqual(m.selection,[[0]])
        for s in range(2):
            codes=m.encode(0,x[0,s,0]);n=np.bincount(codes,minlength=m.channel.shape[-1])+1./m.channel.shape[-1]
            np.testing.assert_allclose(m.channel.probabilities[0,s,0],n/n.sum())
        self.assertTrue(m.receipt['static_mode'])

    def test_new_symbol_prior_projects_to_old_marginal(self):
        from gsl_discrimination.m1_opponent.calibration import _counts
        base=self.rng.integers(0,2,(2,1,40));odd=self.rng.integers(0,3,(2,1,40))
        p=_counts(base,2,1.);joint=_counts(base+2*odd,6,1.)
        np.testing.assert_allclose(joint.reshape(2,1,3,2).sum(2),p)

    def test_nonuniform_time_average_is_integral(self):
        x=np.expm1(np.array([[0.,0.],[1.,0.],[3.,0.]]))
        e,h=OpponentBank().extract(x,[0.,1.,3.],SamplingContract(False))
        self.assertAlmostEqual(float(e),.75)
        self.assertAlmostEqual(float(h[0]),.75)

    def test_shared_nuisance_not_reintegrated(self):
        p=np.array([[[[.99,.01],[.01,.99]],[[.5,.5],[.5,.5]]]])
        ch=FiniteChannel(p,[1.],[[0,0],[1,0]],['a'],['0','1'])
        post=JointPosterior(ch)
        post.update(0,0,'x');post.update(0,0,'y')
        likelihood=np.array([(.99**2+.01**2)/2,.5**2]);expected=likelihood/likelihood.sum()
        np.testing.assert_allclose(post.source,expected)
        with self.assertRaisesRegex(ValueError,'twice'):post.update(0,0,'x')

    def test_joint_burst_error_not_independent_bits(self):
        k=joint_error_kernel(2,[.9,0,0,.1])
        self.assertEqual(k[0,3],.1);self.assertEqual(k[0,1],0.)
        ch=FiniteChannel(np.array([[[[1,0,0,0]],[[0,0,0,1]]]]),[1],[[0,0],[1,1]],['a'],['0','1'])
        noisy=apply_joint_error_channel(ch,k)
        np.testing.assert_allclose(noisy.probabilities[0,0,0],[.9,0,0,.1])

if __name__=='__main__':unittest.main()
