from common_n import *
import shutil
checkout=BASE/'work/pmfs_parity_checkout';dest=checkout/'research/pmfs_reproduction/native_mechanism_closure_r1_20261011';assert not dest.exists();dest.mkdir(parents=True)
# Complete compact CORE; high-volume per-cell table remains in verified ZIP.
omitted={}
for p in CORE.rglob('*'):
 if not p.is_file():continue
 if p.stat().st_size>10*2**20:omitted[p.relative_to(CORE).as_posix()]=dict(SHA256=sha(p),bytes=p.stat().st_size,delivery='Verified review ZIP');continue
 target=dest/p.relative_to(CORE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
meta=load(BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_REVIEW_SHA256.json');dump(dest/'REVIEW_ZIP_DELIVERY.json',dict(SHA256=meta['SHA256'],bytes=meta['bytes'],members=meta['members'],portable_review=meta['verification'],omitted_big_core_table=omitted,RAW_location='Verified review ZIP/local immutable outputs; numerical raw maps not duplicated into Git',scope='Compact code/report/table record. CORE manifest indexes entire ZIP CORE, so omitted big-table entries require ZIP for complete verification.'))
(dest/'README.md').write_text('''# PMFS native mechanism closure R1

Same-engine domain/vertical interventions, same-state sensor-readout contrasts, verified native cold replay, and six precommitted fresh realizations. Start with 00_READ_FIRST_FOR_PRO_zh.md and MECHANISM_CLOSURE_REPORT_zh.md.

This record preserves E3/B4 original decisions and all counterexamples. Five-point diagnostic scores are distinct from full447-cell N0 posteriors. No navigation/CFD/training runs were added. Full-map treatment gain is not tested.

The local verified review ZIP contains RAW maps/query values/selected original snapshots. REVIEW_ZIP_DELIVERY.json records its SHA256 and portable verification. A complete RAW audit requires that ZIP; Git alone is a compact evidence record.
''',encoding='utf-8')
print(str(dest));print('git_copy_bytes',sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()))
