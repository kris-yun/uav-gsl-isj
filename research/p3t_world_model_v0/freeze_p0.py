"""Create P0 provenance record from independently recovered physical inputs."""
import hashlib,json,csv,shutil
from pathlib import Path
import numpy as np
from scipy.stats import multivariate_normal
root=Path(__file__).resolve().parents[2];e=root/'evidence/p3t_d0_gaussian_support_20261001'
old=Path(r'D:\ZYC\A-gas\_worktrees\ocb-r2-census-20260930\evidence\pmfs3d_r1_oracle_ranking_20261001\frozen_inputs')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=lambda name,data:(e/name).write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
raw=json.loads((e/'physical_provenance/RAW_HEADER_AUDIT.json').read_text())
assert len({r['total_moles_per_filament'] for r in raw})==1
assert len({r['all_gas_moles_per_cm3'] for r in raw})==1
mass=raw[0]['total_moles_per_filament'];air=raw[0]['all_gas_moles_per_cm3']
params=dict(total_moles_per_filament=mass,all_gas_moles_per_cm3=air,initial_sigma_cm=10.,growth_gamma_cm2_per_s=15.,sigma_formula='sqrt(100 + 15 * age_seconds)',gas_detection_threshold_ppm=0.1,concentration_unit='ppm',coordinate_unit='m',sigma_unit='cm',gaussian_cutoff='distance < 3*sigma_cm/100',line_of_sight='original 3D occupancy, historical Gaden-RT endpoint and cell-step check',G2_G3_identical=True,emission_budget='R1 unchanged: 5 per recording step, dt=float32(0.2); warmup dt*2; do not rescale to historical 7/s',charter_threshold_operator='>=',historical_native_threshold_operator='>',zero_threshold_equalities_required=True)
dump('P0_PHYSICS_PARAMS.json',params)
files=[];runtime=[]
for case in sorted(old.iterdir()):
 if not case.is_dir():continue
 dest=e/'inputs'/case.name;dest.mkdir(parents=True,exist_ok=True)
 update=case/'context_bank/source_update_0005'
 for name in ['measured_hit_probability.csv']:
  p=update/name;shutil.copy2(p,dest/name);files.append(dict(path=str(p),retained_copy=str((dest/name).relative_to(e)),sha256=sha(p)))
 for p in sorted((case/'resolved_runtime').rglob('*')):
  if p.is_file():
   text=p.read_text(errors='replace');assert 'th_gas_present' not in text
   target=dest/'resolved_runtime'/p.relative_to(case/'resolved_runtime');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
   runtime.append(dict(case=case.name,file=str(p),sha256=sha(p),th_gas_present_override=False))
assert len(runtime)>=4
for p in sorted((e/'inputs').rglob('*')):
 if p.is_file():files.append(dict(path=str(p.relative_to(e)),sha256=sha(p)))
dump('P0_THRESHOLD_RUNTIME_AUDIT.json',runtime)
source_manifest=json.loads((e/'physical_provenance/REMOTE_SOURCE_SHA256.json').read_text())
files+=source_manifest
for p in sorted((root/'research/p3t_world_model_v0').glob('*')):
 if p.is_file():files.append(dict(path=str(p.relative_to(root)),sha256=sha(p)))
dump('P0_INPUT_SHA256.json',files)
parity=json.loads((e/'P0_TRAJECTORY_PARITY.json').read_text());assert parity['pass'] and parity['trajectory_files']==972
synthetic=list(csv.DictReader((e/'GAUSSIAN_SYNTHETIC.csv').open()));errors=[]
for row in synthetic:
 age=float(row['age_s']);d=float(row['distance_m']);sigma=np.sqrt(100+15*age)
 independent=1e6*mass/air*multivariate_normal.pdf([100*d,0,0],mean=[0,0,0],cov=np.eye(3)*sigma*sigma)
 errors.append(abs(float(row['concentration_ppm'])-independent)/independent)
assert max(errors)<2e-6
dump('INDEPENDENT_GAUSSIAN_SOFTWARE_CHECK.json',dict(pass_=True,reference='SciPy normalized multivariate-normal density in cm; separate implementation',synthetic_probes=len(synthetic),maximum_relative_error=max(errors),tiny_sigma_center_support_and_off_center_underflow=True,physical_params_sha256=sha(e/'P0_PHYSICS_PARAMS.json')))
(e/'P0_PROVENANCE.md').write_text('''# P0 provenance

Decision: P3T_D0_P0_PROVENANCE_AND_TRAJECTORY_PASS.

Both original ROS1 House01 2,4-1_fast / House02 3,5-1_fast launch files set gas10, center10 ppm, sigma0=10 cm, gamma=15 cm²/s, 298 K, 1 atm. Eight actual legacy iteration headers uniquely agree on mass=6.440736978853164e-06 mol and air=4.0894632701667424e-05 mol/cm³. Stored sigma values agree with legacy analytical sigma=sqrt(sigma0²+gamma*age); current Gaden-RT Euler growth is NOT substituted. Stored mass avoids legacy pi approximation ambiguity.

Historical Gaussian query: isotropic normalized 3D Gaussian in centimeters, summed in ppm, strict radius<3sigma cutoff, occupancy line-of-sight. Physical growth uses known center ages from the unchanged R1 release/advance loop, not target fitting. Scipy Gaussian-density calculation independently checks twenty deterministic probes.

Threshold: frozen exact_b24 Algorithm.cpp defaults th_gas_present=0.1; all four retained resolved runtime files have no override. StopAndMeasureState uses strict >. D0 explicitly freezes >=; equality occurrences will be audited, never tuned.

972 center trajectories exported using exact original deterministic source draws, transport keys, float timestep and collision helpers. All 972 predicted point maps and eight score tables byte-match frozen R1. G2 embeds the 2D path at the frozen sensor plane; G3 retains original xyz. Reference libraries and source unchanged. Full bank stored on shared mount, hashes retained here.

Scope limits frozen BEFORE Gaussian evaluation: R1 emits five centers/0.2s (25/s), not the historical variable 7/s law. Preserve R1 center count and apply actual historical per-filament mass; do not rescale mass or change release rate. Historical VGR dynamic sensor filtering/stop aggregation remains baked into measured PMFS maps. This D0 tests instantaneous physical Gaussian support with the frozen threshold; it does NOT reproduce the complete historical sensor transfer function or prove point support was the sole mismatch. State0 CFD and old R1 hypotheses are development conditions. No new plume, live runtime, or probability-calibration claim.
''')
(e/'P0_DECISION.md').write_text('P3T_D0_P0_PROVENANCE_AND_TRAJECTORY_PASS\n\nUnique physical parameters and exact R1 parity verified. Gaussian truth rankings not computed. Proceed only with frozen G2/G3 representation comparison.\n')
print('P0_PASS',parity['trajectory_bytes'],max(errors),len(runtime))
