import unittest
from controlled_contrasts import contrasts
class ContrastTest(unittest.TestCase):
    def rows(self):
        return [dict(task_id='case',realization_id='r0',common_contract_sha256='frozen',scope='oracle_diagnostic',D=d,V=v,metric=2*d+3*v+4*d*v) for d in [0,1] for v in [0,1]]
    def test_interaction(self):
        r=contrasts(self.rows())[0];self.assertEqual(r['interaction'],4);self.assertEqual(r['D_effect_at_V0'],2)
    def test_reject_mixed_contract(self):
        x=self.rows();x[0]['common_contract_sha256']='changed'
        with self.assertRaises(ValueError):contrasts(x)
    def test_reject_missing_cell(self):
        with self.assertRaises(ValueError):contrasts(self.rows()[:3])
    def test_reject_duplicate(self):
        x=self.rows();x[0]=dict(x[1])
        with self.assertRaises(ValueError):contrasts(x)
if __name__=='__main__':unittest.main()

class ContractGuardTests(unittest.TestCase):
    def test_declared_factor_only(self):
        from contract_guard import audit
        base = {"source": [1, 2, 3], "factors": {"D": 0}, "threshold": 0.1}
        run = {"source": [1, 2, 3], "factors": {"D": 1}, "threshold": 0.1}
        self.assertEqual(audit(base, run, ["factors.D"])["status"], "PASS")

    def test_hidden_threshold_change(self):
        from contract_guard import audit
        base = {"factors": {"D": 0}, "threshold": 0.1}
        run = {"factors": {"D": 1}, "threshold": 0.11}
        self.assertEqual(audit(base, run, ["factors.D"])["status"], "FAIL")

    def test_source_order_change(self):
        from contract_guard import audit
        self.assertEqual(audit({"sources": [1, 2]}, {"sources": [2, 1]}, [])
                         ["status"], "FAIL")
