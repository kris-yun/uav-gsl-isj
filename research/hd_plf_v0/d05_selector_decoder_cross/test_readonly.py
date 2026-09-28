import unittest
from audit_and_cross import cross, summarize, group_cross

class Checks(unittest.TestCase):
    def setUp(self):
        self.d={'episodes':[{'environment':0,'source_index':0,'target_index':0,
         'anchor_cell':1,'feasible_goals':2,
         'LF-u':{'selected_cell':10,'selected_minus_median_rank_gain':0},
         'LF-rawu':{'selected_cell':11,'selected_minus_median_rank_gain':-1}}]}
        self.obs=[dict(environment=0,source_index=0,target_index=0,goal_cell=g,decoder=a,expected_rank=r)
          for a,vals in [('LF-u',[(10,1),(11,3)]),('LF-rawu',[(10,2),(11,4)])] for g,r in vals]
    def test_summary(self):
        out=summarize(self.d)
        self.assertEqual(out[0]['equal_to_median'],1)
        self.assertEqual(out[1]['below_median'],1)
    def test_cross_four_cells(self):
        rows=cross(self.d,self.obs)
        values={(r['decoder'],r['selector']):r['expected_final_rank'] for r in rows}
        self.assertEqual(values[('LF-u','LF-u')],1)
        self.assertEqual(values[('LF-u','LF-rawu')],3)
        self.assertEqual(values[('LF-rawu','LF-u')],2)
        self.assertEqual(values[('LF-rawu','LF-rawu')],4)
    def test_uniform_and_oracle(self):
        rows=cross(self.d,self.obs)
        d={(r['decoder'],r['selector']):r for r in rows}
        self.assertEqual(d[('LF-rawu','uniform_actions_exact_mean')]['expected_final_rank'],3)
        self.assertEqual(d[('LF-rawu','truth_oracle_diagnostic_only')]['regret_to_oracle_rank'],0)
        self.assertEqual(len(group_cross(rows)),8)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError): cross(self.d,self.obs+[self.obs[0]])
    def test_missing_action_rejected(self):
        with self.assertRaises(ValueError): cross(self.d,self.obs[:-1])
    def test_swap_context_counterexample(self):
        # Two sources, two environments; each environment separately identifies S.
        def observation(s,e): return s^e
        pairs={(observation(s,e),e):s for s in (0,1) for e in (0,1)}
        self.assertEqual(len(pairs),4)
        # Exact environment invariance forces phi(0)==phi(1), erasing source identity.
        phi={0:0,1:0}
        self.assertEqual(phi[observation(0,0)],phi[observation(0,1)])
        self.assertEqual(phi[observation(0,0)],phi[observation(1,0)])

if __name__=='__main__': unittest.main(verbosity=2)
