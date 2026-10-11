"""Small software QA of the common optimizer/router, not scientific data fitting."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import unittest,json,hashlib
import numpy as np
import rk2_models as m

COMMON=dict(ridge_lambda=.01,solver_maxiter=600,solver_gtol=1e-8,solver_ftol=1e-12,KKT_relative_tolerance=1e-6)
class SoftwareTests(unittest.TestCase):
    def test_query_fit_analytic_scalar(self):
        X=np.tile(np.arange(1.,21.)[:,None],(10,1));poses=np.repeat(np.arange(10),20)
        h0=np.ones((1,10))*.03;y=X[:,0]*.4
        h,loss,logs=m.common_fit(X,h0,y,poses,COMMON)
        scale=np.sqrt(np.mean(np.arange(1.,21.)**2))
        expected=(.4+.01*.03)/(1+.01)
        self.assertTrue(np.allclose(h,expected,atol=1e-9));self.assertTrue(all(z['KKT_pass'] for z in logs))
    def test_nonnegative_zero_target(self):
        X=np.ones((200,2));poses=np.repeat(np.arange(10),20);y=np.zeros(200)
        h,loss,logs=m.common_fit(X,np.zeros((2,10)),y,poses,COMMON)
        self.assertTrue(np.array_equal(h,np.zeros_like(h)));self.assertEqual(loss,0)
    def test_global_router_does_not_use_source(self):
        f=np.array([[.1,.2,0.,10.],[.1,.2,1.,10.],[.1,.8,1.,10.]])
        spec=dict(kind='L',tree=dict(feature=2,cut=.5,left=0,right=dict(feature=1,cut=.5,left=1,right=2)))
        self.assertEqual(m.route(f,spec).tolist(),[0,1,2])
    def test_physical_floor_float32(self):
        f=np.array([[-7.56,-7.89,.7,40.],[-7.55,-7.88,.7,40.]],dtype=np.float32)
        c,v=m.physical_features(f);self.assertEqual(c.tolist(),[[-1,-1],[0,0]])
    def test_weighted_quantile_and_capacity(self):
        self.assertEqual(m.weighted_quantile(np.array([0.,1.,2.]),np.array([1.,2.,1.]),.5),1)
        k=np.zeros((10,3),dtype=np.int32)
        self.assertEqual(m.capacity(k,dict(kind='U'))['canonical_total_bytes'],920)
        self.assertEqual(m.capacity(k,dict(kind='L',tree=dict(feature=0,cut=.5,left=0,right=1)))['canonical_total_bytes'],952)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SoftwareTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    p=Path(__file__).resolve().parent/'MODEL_SOFTWARE_QA.json'
    if not p.exists():p.write_text(json.dumps(dict(status='PASS' if result.wasSuccessful() else 'FAIL',cases=result.testsRun,failures=len(result.failures),errors=len(result.errors),scientific_dataset_used=False,model_source_SHA256=hashlib.sha256((p.parent/'rk2_models.py').read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
