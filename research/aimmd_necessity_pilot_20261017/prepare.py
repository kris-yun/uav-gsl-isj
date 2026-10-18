from pathlib import Path
import json,csv,hashlib,shutil,datetime
R=Path(__file__).resolve().parent;H=R.parent/'C4H17'
assert not (R/'FROZEN_PLAN.json').exists(),'No refreeze'
for n in ['code','inputs','logs','results','analysis','lineage']:(R/n).mkdir(exist_ok=True)
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  identity='Fixed-horizon 2026 corrected-wind PMFS numerical necessity pilot; not a 2024 reproduction or a new physical world',
  objective='Test whether undersampled task-relevant paths create source-pair numerical error before introducing a sampler',
  cases=[dict(key='C4_update_1',truth_job='fine_truth_1272',competitor_job='fine_competitor',competitor_cell=514,diagnostic_stops=[2,4,5]),
         dict(key='C3_update_2',truth_job='fine_truth_1099',competitor_job='fine_competitor',competitor_cell=807,diagnostic_stops='all consumed receptors')],
  warmup_steps=1800,warmup_dt=.2,record_steps=200,record_dt=.1,
  physical_target='E of the native whole-population blurred 20s occupancy map after the frozen 360s warmup; score is ell(E map), separately report E ell(map). No steady-state claim.',
  native_multifilament_event='For each cell and timestep, indicator(at least one native filament centre); never replace it with single-particle first passage or sum of weighted hits.',
  reference_replicates_per_source=128,independent_MC_batches=24,MC_replicates_per_source_per_batch=4,
  states='Deterministic SHA256 prediction-state design; fresh native constructor cache/index/RNG, cyclic 2500-value Gaussian table unchanged; not new GADEN world seeds',
  total_primary_source_calls=896,parity_source_calls=4,maximum_source_call_starts=900,
  maximum_child_cpu_s=900,maximum_host_wall_s=2700,maximum_payload_MiB=256,minimum_VM_free_GiB=5,
  rare_path_screen=dict(maximum_descriptive_fraction_of_births_visiting_receptor=.01,minimum_observed_distinct_visitors=3,
    caution='Filaments share native randomness, so this is a descriptive rarity screen, not independent Bernoulli inference.'),
  numerical_task_screen=dict(reference_uncertainty_rule='Compare disjoint reference halves and linearised whole-cloud replicate standard error; no confidence claim from particles/frames',
    material_rare_region_score_error_fraction=.2,score_neighbourhood_chebyshev_radius_cells=5,
    path_error_link='Report exact source-pair logscore error from the frozen rare receptor neighbourhood, its signed covariance contribution, and reference-relative ordering errors'),
  conditional_gate2=dict(required='Only if material task-relevant low-path sampling error is identified with a qualified finite-horizon reference and a mathematically admissible sampling state/weight.',
    comparators=['ordinary MC','ordinary stratification/weighted ensemble','receptor source-contrast guided forward path sampling'],
    pass_criterion='At matched inclusive CPU cost, pair-score RMSE at least 20% lower than strongest ordinary comparator, no increase in incorrect ordering. Training/proposal/resampling/reweighting charged.',
    same_kernel_and_event_required=True,no_backwards_wind_reversal=True,no_network_before_necessity=True),
  conditional_task_gate='More accurate numerical estimates cannot be called task improvements if the qualified target source-pair score still prefers the wrong source. Do not alter physics/scoring/horizon to make it pass.',
  stop='If necessity/reference/target qualification fails, preserve negative/HOLD evidence and stop. No time/seed/parameter search, new worlds, ROS, weak/strong 2x2 completion or C4 unique-cause pursuit.')
(R/'FROZEN_PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
for p in (H/'code').iterdir():
    if p.is_file():shutil.copy2(p,R/'code'/p.name)
shutil.copy2(H/'diagnostic.cpp',R/'diagnostic.cpp')
for case in plan['cases']:shutil.copytree(H/'inputs'/case['key'],R/'inputs'/case['key'])
old=list(csv.DictReader((H/'inputs/jobs.csv').open()));jobs=[];parity=[];states=set()
for c in plan['cases']:
    for ident in [c['truth_job'],c['competitor_job']]:
        prior=next(x for x in old if x['key']==c['key'] and x['job_id']==ident and x['seed']=='2026101701')
        parity.append(prior)
        for phase,n in [('reference',128),('evaluation',96)]:
            for k in range(n):
                label='AIMMD_PATH_NECESSITY_PILOT_20261017/v1|'+phase+'|'+c['key']+'|'+ident+'|'+str(k)
                state=1+int.from_bytes(hashlib.sha256(label.encode()).digest()[:8],'little')%2147483645
                assert state not in states;states.add(state)
                jobs.append(dict(prior,seed=str(state),rng_before='PENDING_NATIVE_CONSTRUCTOR',gaussian_before='0',phase=phase,replicate=str(k)))
def write(p,a):
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
write(R/'inputs/NEW_PREDICTION_STATES.csv',jobs);write(R/'inputs/PARITY_JOBS.csv',parity)
for c in plan['cases']:
    for p in (H/'inputs'/c['key']).glob('cache_*_2026101701.f32'):shutil.copy2(p,R/'inputs'/c['key']/p.name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'lineage/UNCHANGED_KERNELS.json').write_text(json.dumps({n:dict(sha256=sha(R/n),equals_previous=sha(R/n)==sha(H/n)) for n in ['diagnostic.cpp','code/native_forward.cpp','code/native_math.cpp','code/support.hpp']},indent=2))
(R/'lineage/PRIOR_TARGET_MAPS.json').write_text(json.dumps([dict(key=x['key'],job_id=x['job_id'],seed=x['seed'],raw_sha256=sha(H/'results'/x['key']/'W360_R20'/x['seed']/x['job_id']/'raw.f32'),blur_sha256=sha(H/'results'/x['key']/'W360_R20'/x['seed']/x['job_id']/'blur.f32')) for x in parity],indent=2))
print('FROZEN: 896 primary whole-cloud source simulations, 4 exact parity calls; fixed 360+20 seconds only.')
