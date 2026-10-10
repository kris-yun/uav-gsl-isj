import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json, hashlib, importlib.util, csv
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
B4=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(HERE/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
contract={
 'scope':'SOURCE_BLIND_MARGINAL_SCORING_AND_OBSERVATION_ALIGNMENT_DEFINITION_NOT_NEW_EXPERIMENT',
 'physical_bank_split':{'sources':2,'realizations_per_source':4,'reference':[0,1],'heldout':[2,3],'split_unit':'entire independent physical realization'},
 'observation':{'gas_sensor_model':30,'correction_factors':False,'unit':'ppm','PID_response':'float sequential sum of native gas concentrations','MOX_dynamics':False,'aggregation':'same native accepted gas messages; float sequential sum / integer count','accepted_gas_samples_per_B4_block':1,'threshold_ppm':0.1,'threshold_comparison':'>','blocks':50,'stops':10,'blocks_per_stop':5},
 'receptor_schedule':{'all_branches_csv':'FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv','unique_membership_blocks':49,'ambiguous_block_zero_based':40,'earlier_and_boundary_alternatives_predeclared':True,'cannot_count_alternatives_as_two_observations':True,'reference_sampling':'native SampleConcentrations at captured service xyz; choose current frame by new bank actual header time <= physical_target_s < next header; no frame filename extrapolation','start_physical_target_s':322.91661547399997,'end_physical_target_s':534.0860661090001,'sensor_z_m':-0.20000000298023224,'bank_membership_ambiguity_policy':'retain both 50-block branches; score changes/disagreements produce HOLD'},
 'map_operator':{'event_covariates_csv':'MAP_REPLAY_EVENT_COVARIATES.csv','operator':'locked native PMFSLib::EstimateHitProbabilities','p_prior':0.3,'inverse_hit_float':0.6,'inverse_miss_float':0.1,'D':0.4,'cell_size_m':0.25,'kernel_sigma_grid_units':1.5,'kernel_stretch':1.5,'local_estimation_window_grid_units':2,'confidence_sigma_spatial_grid_units':1.0,'confidence_measurement_weight':1.0,'fixed_wind_covariates':'native block average TO direction and speed; identical for all candidates','anchor':'original B4 50 binary events reconstruct logOdds/omega/confidence vs frozen native final input.csv before new evidence interpretation','comparison':'mean reference belief maps vs heldout/observed belief map: descriptive same-object similarity; not independent grid likelihood'},
 'event_probability_estimator':{'method':'Jeffreys Beta posterior mean','alpha':0.5,'beta':0.5,'number_reference_realizations':2,'formula':'(sum_reference_hits + .5)/(2+1)','possible_values':[1/6,.5,5/6],'no_tuned_epsilon_or_temperature':True},
 'scores':{'log':'sum_j[y_j*log(p_j)+(1-y_j)*log(1-p_j)]','log_orientation':'larger better','Brier':'mean_j[(y_j-p_j)^2]','Brier_orientation':'smaller better','report':'per block, per stop, per complete heldout realization, both membership branches','independence_label':'marginal/composite predictive score; NOT joint likelihood or calibrated posterior','score_selection_after_outcome':False},
 'source_blinding':{'scorer':'score_source_blind.py','allowed_input_keys':['reference_events','observation_events'],'candidate_ids':'anonymous, no coordinates or true/wrong roles','heldout_ids':'opaque task; no generating candidate supplied to scoring','freeze':'hash source-blind input and output prior to identity-unblind step','unblind':'separate label file only after score artifact freeze'},
 'unaligned_control':{'definition':'I[native 3D SampleConcentrations(x,y,z)>0 ppm] at same physical sampling time; temporal mean at cell then reference-realization mean','scope':'ideal nonzero arrival; not thresholded PID event; not native 2D filament-centre grid occupation','full_grid':'optional if budget qualified; else leave empty HOLD','native_2D_comparison':'NOT QUALIFIED; no new 2D point source budget; M1 region release cannot prove dimension causality'},
 'interpretation':{'prototype_gate':'small sample only; stable direction is not significance; at least another unselected task still missing','fifty_events_not_fifty_experiments':True,'same_simulator_independent_seed_not_independent_physics':True,'B4_all_positive_not_proof_of_nonidentifiability':True,'no_joint_covariance_inverse_50_or_447_dimensions':True,'no_localization_performance_claim_from_two_candidates':True},
 'original_source_sha256':{str(p.relative_to(B4)).replace('\\','/'):digest(p) for p in [B4/'source/sensor/fake_gas_sensor.cpp',B4/'source/gsl/Common/Algorithm.cpp',B4/'source/gsl/Common/Utils/Math.hpp',B4/'source/gsl/PMFS/PMFS.cpp',B4/'source/gsl/PMFS/PMFSLib.cpp',B4/'source/gsl/PMFS/internal/Simulations.cpp',B4/'source/player/simulation_player.cpp',B4/'source/gaden/include/gaden/datatypes/sources/PointSource.hpp']},
 'native_stop_and_measure_source':{'file':'work/pmfs_r6/package_verification_extract/inputs/official_source/StopAndMeasureState.cpp','sha256':digest(BASE/'work/pmfs_r6/package_verification_extract/inputs/official_source/StopAndMeasureState.cpp')},
}
dump('SCORING_ALIGNMENT_DEFINITION.json',contract)
spec=importlib.util.spec_from_file_location('score_source_blind',HERE/'score_source_blind.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
test=m.source_blind_scores({'anonymous_a':[[1]*50,[1]*50],'anonymous_b':[[0]*50,[0]*50]},{'opaque_test_positive':[1]*50,'opaque_test_negative':[0]*50})
assert test['tasks']['opaque_test_positive']['anonymous_a']['log_sum']>test['tasks']['opaque_test_positive']['anonymous_b']['log_sum']
assert test['tasks']['opaque_test_negative']['anonymous_a']['brier_mean']>test['tasks']['opaque_test_negative']['anonymous_b']['brier_mean']
assert all(x in (1/6,.5,5/6) for p in test['candidate_reference_probabilities'].values() for x in p)
dump('SOURCE_BLIND_SCORE_CODE_UNIT_CHECK.json',{'verdict':'PASS_SYNTHETIC_CODE_CHECK_NOT_PHYSICAL_EXPERIMENT','tests':['positive event favors high probability','negative event favors low probability','exact preregistered smoothing support','no truth metadata accepted'], 'score_sha256':digest(HERE/'score_source_blind.py')})
manifest={p.name:digest(p) for p in HERE.iterdir() if p.is_file() and p.name!='SCORING_CONTRACT_SHA256.json'}
dump('SCORING_CONTRACT_SHA256.json',manifest)
print(json.dumps({'definition':str(HERE/'SCORING_ALIGNMENT_DEFINITION.json'),'files':len(manifest),'new_physical_experiments':0,'source_blind_code_unit_check':'PASS'},ensure_ascii=False))
