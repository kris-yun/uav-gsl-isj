#!/usr/bin/env python3
"""Portable diagnostic reproduction; no native plume/performance claim."""
from pathlib import Path
import argparse,sys,json,hashlib,time,platform
import numpy as np
import scipy
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'diagnostics'))
from verify_reference_repairs import q_refinement,entropy_and_safety
from audit_v43 import fixed_prefix_horizon_test,corrected_encoder_tests,diagnostic_run

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--closed-loop',action='store_true',help='Also rerun the 3 × 20-step same-model diagnostic on the shared 65-node q support.')
 args=ap.parse_args();start=time.perf_counter()
 (HERE/'results').mkdir(exist_ok=True)
 fixture=HERE/'data/frozen_historical_observations.json'
 q=q_refinement();repairs=entropy_and_safety();lag=fixed_prefix_horizon_test();historical_tests=corrected_encoder_tests()
 assert all(t['status']=='PASS' for t in historical_tests),historical_tests
 assert lag['difference_by_future_second'][0]==0 and lag['difference_by_future_second'][1]==0
 assert lag['difference_by_future_second'][2]>0
 for run in q:
  exact=run['results'][-1]
  assert exact['q_count']=='analytic continuous uniform' and exact['map_error']==0,exact
 report={'scope':'Executable, deterministic code/approximation diagnostics only. Native S2 backend, synchronized physical sensor interface and publication performance remain UNVERIFIED.',
  'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
  'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
  'same_data_q_refinement':q,'entropy_and_continuous_path_repairs':repairs,'sensor_delay_horizon':lag,
  'historical_v43_assertions':historical_tests,'quick_elapsed_seconds':time.perf_counter()-start,
  'q_closed_loop':None}
 print(json.dumps({'quick_checks':'PASS','seconds':report['quick_elapsed_seconds'],'old_xy_eig':repairs['XY_EIG']['before'],'correct_xy_eig':repairs['XY_EIG']['after'],'old_collision_passed':repairs['continuous_separation']['before_accepted'],'exact_collision_rejects':not repairs['continuous_separation']['after_accepted']},ensure_ascii=False),flush=True)
 if args.closed_loop:
  qnodes=tuple(np.geomspace(.5,4.,65));assert not np.any(np.isclose(qnodes,1.15,atol=1e-12,rtol=0))
  runs=[]
  for mode in ['bio','bio_noidentity','ordinary_projected_full']:
   t=time.perf_counter();r=diagnostic_run(mode,qnodes,steps=20);runs.append(r)
   print(json.dumps({'mode':mode,'map_xy':r['map_xy'],'map_error':r['map_error'],'pathlength':r['pathlength'],'seconds':time.perf_counter()-t}),flush=True)
  report['q_closed_loop']={'scope':'All methods share the same 65 log-spaced q nodes, equal discrete weights, source candidate domain, forward model and measurement-noise seed. Only q support is changed from the historical diagnostic; other old-controller defects are deliberately retained. No continuous-integral or native-performance claim.','runs':runs}
 report['elapsed_seconds']=time.perf_counter()-start
 filename='verification_with_closed_loop.json' if args.closed_loop else 'verification_quick.json'
 (HERE/'results'/filename).write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('Saved results/'+filename,flush=True)
if __name__=='__main__':main()
