"""Freeze authorized eight-run maximum and ordinary controls before new physics."""
from pathlib import Path
import csv,json,shutil,datetime,subprocess,zipfile
from protocol import *
from recover_assets import OCC,geometry_receipt,run_path
from extract_existing_worlds import points_for_probes

def main():
 if (OUT/'PROTOCOL.json').exists():raise RuntimeError('protocol already frozen')
 proposal=PROJECT/'results/source_pair_observability_20261023/NEXT_SINGLE_PROPOSAL.json'
 p=json.loads(proposal.read_text());assert p['maximum_new_gas_worlds']==8
 assert shutil.disk_usage('D:/').free>=p['minimum_free_disk_before_run_bytes']
 refs=OUT/'historical_source_reference';refs.mkdir(parents=True,exist_ok=True)
 zpath=Path('D:/ZYC/A-gas/_staging/OCB_R2_GENERATOR_REFOUNDATION_REVIEW_20260929.zip')
 keep=['evidence/ocb_r2/BUILD_PROVENANCE.md','evidence/ocb_r2/UPSTREAM_PARENT_DIRTY.patch',
 'evidence/ocb_r2/UPSTREAM_CORE_DIRTY.patch','research/ocb_r2/READONLY_TIMELINE.patch']
 with zipfile.ZipFile(zpath) as z:
  for n in keep:(refs/Path(n).name).write_bytes(z.read(n))
 expected={'parent_diff_sha256':'5c2b3c543ffd1ed082efd686ba05491b6aa9acc02bb4b834b3ab47186a9c6f6e',
 'core_diff_sha256':'6a1304d213dd84e70cd6b440e66db3c98e01f78b2c138a849799a117973dd01c',
 'mathutils':'0a30c798bd4c413adc30748e70cb643f32a65c570d08b41ac0df2c5aabb2cfff',
 'running':'98b9ab100d7cf220524ecb5c15a150da91016407fe5452a4700201164910f995',
 'timeline_patch':'e875f61355ced7e17d490d2f28eb82951c28c3372060358e805fa7ebcef067d1',
 'binary_sha256':ELF_SHA,'parent_head':'17adaf650a4f11d29aa049cf0661e9f9ea2e636f',
 'core_head':'9e93c36ae1af74f6a62c42f1c9d7b813153222ed','occupancy':sha(OCC)}
 assert sha(refs/'UPSTREAM_CORE_DIRTY.patch')==expected['core_diff_sha256']
 assert sha(refs/'UPSTREAM_PARENT_DIRTY.patch')==expected['parent_diff_sha256']
 manifests=[]
 for r in range(1,5):
  root=run_path(f'ocb_r2_cfg00_r{r:02d}');m=json.loads((root/'RUN_MANIFEST.json').read_text())
  assert m['generator_binary_sha256']==ELF_SHA and m['master_seed']==2026900000+r
  assert m['simulation_parameters']['source_position_z']=='0.40'
  manifests.append({'run':m['run_id'],'sha256':sha(root/'RUN_MANIFEST.json'),'path':str(root/'RUN_MANIFEST.json')})
 base=json.loads(Path(manifests[0]['path']).read_text())['simulation_parameters']
 for m in manifests[1:]:
  other=json.loads(Path(m['path']).read_text())['simulation_parameters']
  assert {k:v for k,v in base.items() if k!='results_location'}=={k:v for k,v in other.items() if k!='results_location'}
 assets=json.loads((PROJECT/'results/native_20261023/assets/ocb_r2_cfg00_r01.json').read_text())
 winds=[{'index':int(Path(w['path']).name.rsplit('_',1)[1]),'sha256':w['sha256']} for w in assets['wind']]
 with (PROJECT/'evidence/discovery/ocb_r2/metadata/E1_HOUSE_PROBE_CONTRACTS.tsv').open() as f:
  probes=sorted([x for x in csv.DictReader(f,delimiter='\t') if x['house']=='House01'],key=lambda x:int(x['probe_rank']))
 geometry=geometry_receipt(p['source_xyz_m']);pool_geometry=geometry_receipt(points_for_probes(probes))
 assert all(x['legal_free'] for x in geometry+pool_geometry)
 cfg={'schema':'sameheight-three-source-ordinary-observability-v1','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'proposal_sha256':sha(proposal),
 'human_authorization':'2026-10-23 user approved same-height three-source proposal, maximum eight new worlds, TRAIN-only selection then one frozen DEV check; no threshold tuning, M2/M3 or ROS closed loop',
 'source_ids':['A','B','C'],'source_xyz_m':p['source_xyz_m'],'master_seeds':p['master_seeds'],
 'TRAIN_repeats':[1,2],'DEV_repeats':[3,4],'reuse_A':manifests,'old_lower_height_B_not_reused':True,
 'maximum_new_attempts':8,'maximum_generation_wall_s':5400,'maximum_new_scientific_bytes':805306368,
 'minimum_free_disk_before_run_bytes':2147483648,'budget_semantics':'new scientific content including gas frames and one shared wind bundle; byte-identical wind snapshots can be hardlinked to frozen inputs, while both logical and deduplicated sizes are reported; never change physical output',
 'expected_identity':expected,'expected_wind':winds,'base_parameters':base,
 'expected_record_count':1803,'expected_timeline_sha256':assets['timeline_sha256'],
 'occupancy_path_alias':GUEST+'/shared_workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv',
 'path_adaptation':'read-only vmhgfs mount in task-owned directory because original /mnt/hgfs/workspace is absent after boot; same SHA, no map edits',
 'physical_parameters_unchanged_except_source_xyz':True,'legacy_temperature_pressure_binding_preserved':True,
 'absolute_Q_or_real_PID_not_certified':True,'all_probe_pools':probes,'source_legality':geometry,'pool_legality':pool_geometry,
 'window_anchors_s':list(range(50,951,50)),'duration_s':20,'native_timestamps_only':True,'maximum_native_step_s':0.61,
 'pair_separation_m':[0.3,2.0],'detection_threshold_ppm':0.1,'tie_tolerance':'abs(d-min)<=1e-12*max(1,maxabs(d)); multiple minima are ties',
 'TRAIN_protocol':'six physical worlds; two realization folds: all-source r01 templates evaluate r02, then reverse; no frame split',
 'known_amplitude_score':'ordinary mean-square distance in log1p ppm; no calibrated density claim',
 'unknown_gain_score':'nonnegative least-squares common gain in physical ppm; separate sensitivity; not applied to thresholded fractions',
 'controls':['single full window','single time mean','single 0.1ppm hit fraction','static pair mean','equal-scalar-budget static pair','pair hit fractions','ordered full pair','unordered joint multiset','sorted side marginals','equal-scalar-budget ordered pair'],
 'equal_scalar_budget':'N single readings versus 2*floor(N/2) dual readings at every second native time; not a flight/hardware cost claim',
 'strong_single_control':'at the selected anchor, best TRAIN-only single among all 30 probes and full/mean/hitfraction, not only the chosen pair endpoints',
 'single_tie_break':'strict TRAIN correct count, worst normalized source margin, mean then hitfraction then full, probe rank',
 'dual_selection':'one eligible pair-window maximizing equal-budget static pair strict-correct minus strongest same-window global single; then dual strict-correct, worst margin, smaller separation, earlier anchor, lexicographic probes; no M1 scores',
 'DEV_rule':'freeze one pair, one same-window global single, all prototypes, code and metrics before any new DEV response decoding; evaluate six DEV worlds once, including two already-open A controls; never label whole panel new blind validation',
 'primary_reporting':['per-world three-source ranking and exact ties','B/C confusion','XY MAP error in this fixed three-candidate diagnosis','paired delta versus strongest frozen ordinary single','A normal-control harm'],
 'dynamic_scope':'ordered versus unordered and static are secondary necessity diagnostics, not M1 algorithm validation',
 'stop':'identity/parameter/budget failure stops; preserve first failures; no retry for score, extra seed, House, M1/M2/M3, active controller or ROS robot loop'}
 write('PROTOCOL.json',cfg)
 write('LOCAL_INPUT_GATE.json',{'status':'PASS_LOCAL_INPUTS_AWAIT_GUEST_IDENTITY','protocol_sha256':sha(OUT/'PROTOCOL.json'),
 'historical_reference_zip_sha256':sha(zpath),'all_sources_and_120_pool_cells_free':True,'four_A_manifests_match':True,
 'new_physics_started':0,'DEV_new_concentration_decoded':0,'frozen_O24_changed':False})
 print('LOCAL_INPUT_FREEZE_PASS',sha(OUT/'PROTOCOL.json'))

if __name__=='__main__':main()
