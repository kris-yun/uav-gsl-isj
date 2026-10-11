"""New diagnostic interventions only; frozen M1/M2 stay untouched."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent
BASE=W.parents[1]
O=BASE/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010'
O.mkdir(exist_ok=True)
contract=dict(parent_M2_commit='c7f06bfd2b180350f5fe7d03b772da5839945d8e',
 user_authorization='2026-10-10 direct human continuation: 接触代码, 分析根本失败物理机制, 实验找出来; new bounded diagnostic interventions, not rerun M2',
 investigation='Separate planar particle support, finite-width observation kernel, candidate source representation, and wall-boundary mechanics.',
 exploratory_after_M2=True,new_GADEN_realizations=0,CFD_runs=0,navigation_goals=0,training_runs=0,
 preserved_data='M1 and M2 raw files, scores, ZIPs and historical verdicts are frozen; new results have separate contract and paths.',
 same_bank_operator_contrast=dict(physical_banks='All 8 existing M2 point-source realizations, same original 50 receptive block times/coordinates',
   reference_reps=[0,1],evaluation_reps=[2,3],evaluation_limitation='Reuses previously examined M2 tasks; new exploratory operator counterfactual, not a newly untouched final test.',
   operators=['PID_NATIVE (existing actual native values, not regenerated)',
              'CENTER_COLUMN (any filament centre in same native 0.25m XY cell; all heights)',
              'CENTER_SENSOR_BAND (same XY cell, abs(z-centre_z)<0.125m; geometric proxy)',
              'PID_CELL_TRUNCATED (native ppm contributions retained only for centres in same XY cell)',
              'PID_NO_GROWTH_KERNEL (same saved paths and mole constants, sigma reset to initial 10cm for observation only)'],
   physical_operator_caveat='Only PID_NATIVE matches actual measurement. Centre operators are deliberately misspecified comparison models. Kernel ablations keep recorded transport fixed and do not claim to be self-consistent new physical simulations.',
   scores=['same frozen Jeffreys beta(.5,.5) per-event predictive log','same mean Brier'],
   uncertainty='Use realization-level paired tables. Do not claim 50 or 447 independent samples or a calibrated joint posterior.',
   contribution_decomposition=['native ppm mass from centres in same XY cell','outside XY-cell mass','same XY and sensor-height band mass','sigma / centre distance / vertical contribution summaries'],
   no_score_switching=True,no_threshold_tuning=True),
 boundary_source_factorial=dict(factors={'source_form':['native uniform 1x1','exact original point'],
                                        'obstacle_response':['native rollback/stop','native rollback then tangential projection of remaining displacement']},
   hypotheses=['H_wall: blocked native paths trap true-source particle cloud and produce deficient predicted support.',
               'H_source: point versus uniform region changes candidate prediction enough to explain source preference.'],
   candidates={'C7':[-3.2,-3.3],'K2':[-1.675,1.495]},
   RNG_bundles='Captured M1 T/W states and Gaussian table phases; same initial bundle within paired contrast, not event-keyed after survival divergence.',
   maximum_new_forward_calls=14,number_of_new_scientific_forward_calls=12,maximum_necessary_native_parity_anchors=2,
   reused_existing_native_uniform_calls=4,
   single_thread=True,combined_forward_wall_s=120,forward_RSS_bytes=536870912,
   build_wall_s=180,build_RSS_bytes=1610612736,new_remote_disk_bytes=200000000,
   native_settings='M1 frozen B4 values unchanged, including wind, grid, D=.4, dt=.1, noise=.2, record200, warmup200-500, blur1.5',
   permitted_motion_change='Only after native obstacle rollback, project remaining displacement tangent to detected grid normal and continue. Free/visibility fastpaths, native step increments and out-of-bounds deletion remain native.',
   representation_note='Exact points are oracle mechanism controls, never deployed source labels.',
   capture=['blurred/unblurred map','native score','per-cell/per-step movement aggregates','blocked/stalled/accepted displacement','initial/final Gaussian phase and RNG','point audit','runtime and hashes'],
   stop_rule='Parity error or resource limit stops; no extra states/seeds/parameters/thresholds or retry of entered forward.'),
 wind_audit='Use existing CFD10 and native captured wind; check true/false exact source vertical profiles. No new wind or wind-plane intervention.',
 decisions='Report which interventions actually change source preference, which fail, and which preserve error; no generic HOLD substituting for available numerical conclusions.')
p=O/'M3_FROZEN_CONTRACT.json';assert not p.exists();p.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
h=hashlib.sha256(p.read_bytes()).hexdigest()
(O/'M3_PRE_COMPUTE_SHA256.txt').write_text(h+'  M3_FROZEN_CONTRACT.json\n',encoding='ascii')
print(json.dumps(dict(contract_SHA256=h,output=str(O)),ensure_ascii=False))
