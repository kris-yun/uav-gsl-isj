"""Validate, render and package actual gate decisions and experiment evidence."""
import pathlib,json,csv,hashlib,zipfile,shutil
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'evidence/lakeshore_observability_r0_r2';EXP=ROOT/'experiments/lakeshore_observability'
final=json.loads((OUT/'FINAL_DECISION.json').read_text());assert final['R1']['execution_status']=='COMPLETED_FULL_864'
assert final['decision'] in ['R1_PASS_LAKESHORE_OBSERVABILITY_DISTORTION','R1_HOLD_WEAK_OR_UNSTABLE','R1_FAIL_STOP_SCENE_MECHANISM']
for name in ['README.md','GENERATION_PLAN.md']:(OUT/f'PROTOCOL_{name}').write_bytes((EXP/name).read_bytes())
for name in ['jgr2025_case_map.csv','jgr2025_coordinate_contract.json','jgr2025_r0_readiness.md']:
 shutil.copyfile(pathlib.Path(r'C:\work\LAKESHORE_GSL_DATA_20261002\evidence\data_audit_20261002')/name,OUT/('BOUNDARY_'+name))
primary=pd.DataFrame(final['R1']['primary']['primary_rows']);summary=pd.read_csv(OUT/'M4_summary_threshold_1.csv')
fig,axs=plt.subplots(1,3,figsize=(13,4),layout='constrained')
for ax,rate in zip(axs,[5,10,20]):
 for env in ['N0','L1','F1','F2']:
  q=summary[(summary.environment==env)&(summary.release==rate)];ax.plot(q.height,100*q.top1,'o-',label=env)
 ax.set_title(f'{rate} filaments/s');ax.set_xlabel('Flight height (m)');ax.set_ylabel('Top-1 success (%)');ax.set_ylim(0,100);ax.grid(alpha=.2);ax.legend()
fig.savefig(OUT/'R1_M4_height_identifiability.png',dpi=160);plt.close(fig)
report='''# R1 offline mechanism report

Decision: **DECISION**.

Primary fails because N0 and F1/F2 all have88.89pp height Top1 spread, so the negative-control contrast is absent. At mid release10, N0 is100% Top1 at10m and11.11% at30/60/100m; F1/F2 are100% at10/30m and11.11% at60/100m. Rank1 versus5 is shared by controls. The present data show an extension of the detectable height to30m, not a front-specific low-level false-negative blind zone. M1 upwind-cone capture is100% and M2 blind fraction0. M3 F1 front-peak fraction41.67% versus N033.33% at mid release is weak secondary evidence only; HOLD does not certify the primary mechanism. Threshold sensitivities do not rescue primary. R2 is not run.

R0_GO precedes N0 parity PASS, native RNG repeatability PASS, wind QC PASS and 12-realization smoke PASS. Then parameters, gas generation and scorer sources were frozen before the 864-realization matrix. No PMFS, learned model, closed loop or House rerun was involved.

Adapter: ros2_gaden family, minimal native C++ CLI against unchanged pre-existing GADEN core 3.0 in PF_DEI_V3_GADEN_BUILD. Python bindings absent. Main source commit17adaf650a4f11d29aa049cf0661e9f9ea2e636f, main core9e93c36ae1af74f6a62c42f1c9d7b813153222ed, historically modified. Isolated build's Git links are broken; source/binary hashes are authoritative, its original commit is not asserted.

Geometry is explicit native Environment occupancy: flat solid layer -5..0m; free interior0..150m; outer lateral/top cells are outlets. No shoreline wall. Native ParseOpenFoamVectorCloud preprocesses every regular CSV. Native RunningSimulation generates/query filaments, no replacement concentration field or postprocessing lift. No runtime package/kernel was installed, upgraded or edited.

N0 u=2m/s. L1 u=.4+1.6*f(z). F1/F2 divergence-free streamfunction: u=.4+A*s(x)*(f(z)-mean(f)), w=-A*sprime(x)*I(z), I(0)=I(150)=0. Compensating upper return flow preserves continuity. H=100m, widths15m vertical/35m horizontal. w maxima.5/1m/s. This is an ideal mechanism ablation, not fitted transient weather. N0 random100 query-point error0; finite-difference divergence maxima1.071e-4/2.142e-4s^-1.

Methane:5/10/20filaments/s, initial centre20ppm, sigma100cm, growth gamma10000cm²/s, native noise.02,298K/1atm. These are frozen synthetic dispersion settings, not inferred from public weather. Native buoyancy is unchanged across conditions. Eight explicit plume seeds30001..30008; OMP1, separate process per realization;120s warmup then300s fixed1Hz queries. Gas fields evolve in memory; exported C data are native trajectory observations, with replay defined by frozen seeds and binaries.

M4 removes the held-out seed from all9 source templates, Beta(1,1) smoothing and Brier ranking. Exact ties receive average rank/fractional Top1/Top3 credit; all misses remain chance-level. Heights10/30/60/100m share one2m/s XY ladder, period220s. Hit threshold.001ppm, sensitivity.0005/.002ppm. No per-environment thresholds.

## Primary gate

PRIMARY_TABLE

## Height results

M4_TABLE

## Secondary gate

SECONDARY_JSON

Full source/seed data are in M1/M2/M3_threshold_*.csv and M4_trials_threshold_*.csv. M1 conditions on gas hits. M2 reports paired trajectory-time sample fractions, not geographic area: repeated visits do not represent square metres. M3 compares peak source/front distance and predeclared15m band, requiring>=2 source-x groups, more front peaks than N0 and median peak closer to front than source, across>=2/3 release levels. This operationalizes a qualitative screening criterion, not a high-fidelity quantitative conclusion.

R2 is allowed only after matched primary+secondary PASS. R1 FAIL/HOLD stops active probing. Initial R0 whole-profile-slope interpretation error was corrected to README local-structure criterion before any gas results; event windows remained unchanged. JGR averaged XZ data provide only background ranges, never transient3D input.
'''
report=report.replace('DECISION',final['decision']).replace('PRIMARY_TABLE',primary.to_markdown(index=False)).replace('M4_TABLE',summary.to_markdown(index=False)).replace('SECONDARY_JSON','```json\n'+json.dumps(final['R1']['secondary'],indent=2)+'\n```')
(OUT/'R1_MECHANISM_REPORT.md').write_text(report,encoding='utf-8')
(OUT/'runtime_audit.md').write_text(report.split('## Primary gate')[0].replace('# R1 offline mechanism report','# GADEN runtime audit')+'\nObserved runtime sources/binaries in runtime_*.txt and runtime_binary_hashes.txt; actual parity and seed validations in N0_parity.json/seed_repeatability.json.\n',encoding='utf-8')
freeze=[]
for line in (OUT/'PRE_R1_FREEZE_SHA256SUMS.txt').read_text().splitlines():
 digest,name=line.split('  ',1);p=ROOT/name
 if p.name=='package_evidence.py':continue # delivery bookkeeping, completed after scores
 freeze.append({'path':name,'match':p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==digest})
assert all(x['match'] for x in freeze),freeze
inputs=json.loads((OUT/'R0_input_hashes.json').read_text());assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
obs=pd.read_csv(OUT/'observation_manifest.csv');assert len(obs)==864
parity=pd.read_csv(OUT/'N0_parity.csv');assert len(parity)==100 and np.max(abs(parity[['u','v','w']].to_numpy()-[2,0,0]))<1e-5
validation={'full_realizations':864,'rows':864*1200,'frozen_physics_scoring_config_hashes_unchanged':freeze,'raw_inputs_unchanged':True,'N0_parity_verified':True,'R1_decision':final['decision'],'R2_execution_status':final['R2']['execution_status'],'png_signature':(OUT/'R1_M4_height_identifiability.png').read_bytes().startswith(b'\x89PNG')}
(OUT/'DELIVERY_VALIDATION.json').write_text(json.dumps(validation,indent=2))
members=sorted(p for base in [OUT,EXP] for p in base.rglob('*') if p.is_file() and p.name not in ['MANIFEST.csv','SHA256SUMS.txt','observations.tar.gz'] and '__pycache__' not in p.parts)
rows=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in members]
with (OUT/'MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rows)
(OUT/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['path']+'\n' for r in rows))
target=pathlib.Path(r'C:\work\LAKESHORE_OBSERVABILITY_R0_R1_EVIDENCE_20261003.zip')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in members+[OUT/'MANIFEST.csv',OUT/'SHA256SUMS.txt']:z.write(p,str(p.relative_to(ROOT)).replace('\\','/'))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for row in rows:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
digest=hashlib.sha256(target.read_bytes()).hexdigest();target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n')
print(json.dumps({'ZIP':str(target),'SHA256':digest,'bytes':target.stat().st_size,'files':len(members)+2},indent=2))
