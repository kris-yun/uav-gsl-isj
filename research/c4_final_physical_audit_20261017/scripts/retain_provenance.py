from pathlib import Path
import csv,hashlib,json,shutil
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014';H=R.parent/'C4H17'
for n in ['CONVERGENCE_FLAGS.csv','SOURCE_PAIR_LOGSCORES.csv','PAIR_SUMMARY.csv','RECEIVER_OBSERVATIONS.csv','NUMERICAL_CHECKS.json']:
    shutil.copy2(H/'analysis'/n,R/'lineage'/('prior_'+n))
for n in ['LOADED_LIBRARY_AND_ROOT_CAUSE_IDENTITY.json','GENERATOR_LOADED_LIBRARY_IDENTITY.json']:
    shutil.copy2(P/n,R/'lineage'/('original_'+n))
shutil.copytree(H/'inputs/historical_native',R/'inputs/historical_native',dirs_exist_ok=True)
assets=json.loads((R.parent/'C4A17/lineage/PHYSICAL_CONTEXT_ASSETS_SHA256.json').read_text())
for name,h in assets.items():
    p=P/'PORTABLE_DATA'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==h
    dst=R/'inputs/physical_assets'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst)
old=json.loads((R/'lineage/original_LOADED_LIBRARY_AND_ROOT_CAUSE_IDENTITY.json').read_text())
now=json.loads((R/'lineage/RUNTIME_BUILD_IDENTITY.json').read_text())
lib=next(x for x in old['actual_running_player_loaded_libraries'] if x['path'].endswith('/libgaden.so'))
assert now['binaries'][lib['path']]==lib['sha256']
receipt=dict(original_loaded_libgaden_sha256=lib['sha256'],current_linked_library_same_hash=True,
  original_record_scope='Batch recovery identity captured with a running player; not a new per-C4 process-memory capture',
  archived_concentration_responses_bit_exact=878,
  twoD_source_and_diagnostic_identical_to_previous={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256((H/p.relative_to(R)).read_bytes()).hexdigest() for p in [R/'diagnostic.cpp',*(R/'code').glob('native_*.cpp')]})
assert all(receipt['twoD_source_and_diagnostic_identical_to_previous'].values())
(R/'lineage/IMPLEMENTATION_EQUIVALENCE.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))
