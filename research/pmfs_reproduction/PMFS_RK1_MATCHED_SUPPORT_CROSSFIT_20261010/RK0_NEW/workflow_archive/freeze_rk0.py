import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parent;B=W.parents[1]
M2=B/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010';O=B/'outputs/PMFS_RK0_RESPONSE_STATE_NECESSITY_20261010'
assert not O.exists();O.mkdir();(O/'source').mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['run_rk0.py','cache_native.py']:
    shutil.copy2(W/n,O/'source'/n)
shutil.copy2(M2/'independent_raw_query_verify/verify_raw_receiver_queries.py',O/'source/verify_raw_receiver_queries.py')
m=json.loads((M2/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
selected={n:h for n,h in m.items() if n.startswith('native_reference_evidence/realizations/') or n in [
 'observation_lineage/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv',
 'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv','source_blind_inputs/branch_0.json',
 'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json','score_source_blind.py','native_reference_evidence/FROZEN_METADATA.json',
 'independent_raw_query_verify/verify_raw_receiver_queries.py']}
for n,h in selected.items():assert sha(M2/n)==h,n
meta=json.loads((M2/'native_reference_evidence/FROZEN_METADATA.json').read_text(encoding='utf-8'))
c=dict(
 stage='RK0 oracle response-kernel and hidden-state necessity, not old stopped M4',
 parent_M2M3_commit='4d15d0d93b5d33b1d7d18b12b4cf8095f1cfe66c',
 user_authorization='Continuation of direct human request to learn supplied PRO reasoning and perform bounded mechanism experiments; this stage reads existing data only. No authorization is inferred for proposed 24 new realizations.',
 PRO_handoff_ZIP_SHA256=sha(Path('C:/Users/50176/Downloads/PRO_M2M3_独立复核与跨领域机制候选_20261010.zip')),
 reference_realizations=['C7_0','C7_1','K2_0','K2_1'],previously_seen_exploratory_evaluation=['C7_2','C7_3','K2_2','K2_3'],
 receivers='Ten exact native poses ordered by stop0..9, 51 membership rows/50 original blocks retained; alternative branch never additional fitting exposure.',
 fit_exposure='All four reference banks, all 50 branch0 planned snapshot exposures. Compute 49 unique frames once, duplicate frame weights numerator and denominator identically. These are correlated records, not independent realizations.',
 origin_x=meta['origin_x'],origin_y=meta['origin_y'],cell_size=.25,
 XY_counting='Mathematical floor on original .25m origin lattice; include navigation nonfree and outside2Dframe cells. This explicit independent gas lattice is not a claim of native C++ trunc parity outside bounds.',
 U='N(cell) times pooled reference stationary h(cell,receiver); h=sum every native per-particle ppm contribution divided by count of ALL particle exposures, including zero response.',
 S='Same estimator and gas counts, up to4 physical classes perXY: global reference-only exposure-weighted median Z x median sigma_cm (>=split high). No heldout state used to fit bins or kernel.',
 F='Existing native3D/PID snapshot readout. No new physics process or concentration query executable.',
 missing_policy='Never fill an unobserved cell/class h with0 or heldout mean. Mark point concentration UNSUPPORTED; lower/upper contribution interval uses nonnegativity and fixed native single-particle peak bound (initial10cm, or high-sigma class threshold) plus original native numerical allowance. These intervals are not calibrated and do not bound covered-class model error.',
 scoring='Same M2 per-event Jeffreys(.5,.5), two reference events -> p in{1/6,1/2,5/6}; marginal log sum and mean Brier, native original and four real heldout events. Apply nativefloat32 .1ppm threshold to each realization total before reference pooling.',
 randomness_limit='Population variations retained across finite oracle realizations; conditional-mean h omits residual within-class response variation. Not deployment or calibrated full likelihood.',
 gate='S needs truth-directed mean log and Brier contrast gains on at least2 previously seen heldout tasks, means not adverse, plus common-complete-support receptor MSE reduction on same tasks; full coverage reported independently. Small gains do not establish main innovation.',
 R_control='Only if S passes stated exploratory source+common-support response gate: one four-class SHA256(salt + little-endian native f32 x,y,z,sigma bits) mod4 control, salt PMFS_RK0_NONPHYSICAL_F32_STATE_HASH_v1. Same kernel/count estimator, no sourceID/time/serial/labels. No other random grouping.',
 source_blinding='Pool reference physical records without candidate/true identity in h or class split. Save and hash source-blind U/S/F inputs+scores before analysis-only generator mapping. R params fixed now even if triggered later.',
 wall_limit_seconds=600,process_RSS_limit_bytes=1073741824,new_disk_limit_bytes=2147483648,
 native_first_anchor='One existing C7_0 native_cpp_receiver_total, then remaining196 cross-frame caches; original tolerance abs3e-7+rel5e-6 unchanged. All204 reference actualquery totals checked.',
 stop='Hash/time/source/geometry mismatch, native anchor failure, nonfinite, wall/RSS/disk limit. No retrying the experiment after poor performance, extra seed, state cap increase or parameter selection.',
 new_gas_realizations=0,new_CFD=0,new_navigation=0,new_network_training=0,new_candidate_forward=0,new_VM=0,
 inputs_sha256=selected,executable_source_sha256={p.name:sha(p) for p in (O/'source').iterdir() if p.is_file()})
(O/'frozen_contract.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'PRE_RUN_CONTRACT_SHA256.txt').write_text(sha(O/'frozen_contract.json')+'  frozen_contract.json\n',encoding='ascii')
print(json.dumps(dict(output=str(O),contract_SHA256=sha(O/'frozen_contract.json'),frozen_inputs=len(selected),budget_seconds=600,new_physics=0),indent=2))
