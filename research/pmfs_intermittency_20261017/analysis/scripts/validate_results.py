from pathlib import Path
import json,csv,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'results'
b=json.loads((O/'b4_recomputed/FINAL_QA.json').read_text());assert b['pass_all'] and b['matched_free_cell_states']==16128 and b['replayed_observation_windows']==580
r=json.loads((O/'REPLAY20_QA.json').read_text());assert len({a['case'] for a in r})==20 and all(a['status']=='PASS' and a['log_odds_max_error']==0 and a['confidence_max_error']==0 for a in r)
p=json.loads((O/'SOURCE_SCORE_PARITY.json').read_text());assert len(p)==len(r) and max(a['posterior_max_error'] for a in p)<2e-8
controls=json.loads((O/'STRONG_CONTROLS.json').read_text());assert len(controls)==len(p)*16 and len({a['arm'] for a in controls})==4
for c in sorted({a['case'] for a in controls}):
 previous=None
 base=[a for a in controls if a['case']==c and a['arm']=='O0' and a['confidence']=='native' and a['forward']=='native_blur']
 for a in base:
  z=np.load(O/'controls'/(c+'_'+a['update']+'.npz'));assert a['competitor_locked_cell']==previous
  assert np.max(np.abs(z['O0__native__native_blur']-z['native_q']))<2e-8
  previous=int(z['free_indices'][np.argmax(z['native_q'])])
  assert all(not v['task_gain_claim'] for v in controls)
print('PASS: all 20 original histories, all final-owner posteriors, all ordinary control factorials, prior-locked competitors, and the 580-window B4 anchor.')
