"""One-shot seal and complete E2 archive. Never launches native simulation."""
from pathlib import Path
import csv,datetime,hashlib,json,zipfile
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';OUT=Path('D:/ZYC/A-gas/_deliveries/M0_E2_20261007');NAME='M0_E2_CRN_SENTINEL_QUALIFIED_FULL_EVIDENCE_20261007.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
dec=json.loads((R/'E2_DECISION.json').read_text());ind=json.loads((R/'INDEPENDENT_E2_VERIFICATION.json').read_text());assert dec['verdict']=='M0_E2_CRN_SENTINEL_QUALIFIED' and dec['new_wrong_wind_runs']==4 and not dec['remaining_28_launched'];assert ind['status']=='INDEPENDENT_E2_VERIFICATION_PASS'
assert json.loads((R/'LINUX_REPLAY_VERIFICATION.json').read_text())['status']=='LINUX_FRESH_EXTRACTION_REPLAY_PASS'
assert not (R/'E2_EVIDENCE_SEAL.json').exists() and not (R/'E2_EVIDENCE_FILES_SHA256.csv').exists()
original=R.parent/'M0_CLEAN_SUPPORT_DESIGN_R0_FROZEN_20261007.zip';assert sha(original)=='ffdb1be5452f6bb7a3e2500b13e40261a0e1f44223868bcc3f86824d6489f658'
files=sorted(p for p in R.rglob('*') if p.is_file() and not any(t in p.parts for t in ['evidence','__pycache__']) and p.suffix!='.pyc');manifest=R/'E2_EVIDENCE_FILES_SHA256.csv'
with manifest.open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
seal={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':dec['verdict'],'new_wrong_wind_runs':4,'new_U0_runs':0,'remaining_28_runs':0,'scientific_M0_verdict':'NOT_TESTED','manifest_sha256':sha(manifest),'R0_seal_sha256':sha(F/'M0_R0_FREEZE.json'),'raw_native_archive_sha256':sha(R/'M0_E2_RAW_NATIVE_20261007.zip'),'pre_run_seal_unchanged_sha256':sha(R/'E2_EXECUTION_SEAL.json'),'clock_audit_erratum_preserved':True,'E3_authorized':False,'included_files':len(files)}
sealfile=R/'E2_EVIDENCE_SEAL.json';sealfile.write_bytes((json.dumps(seal,indent=2)+'\n').encode());files.extend([manifest,sealfile]);OUT.mkdir(parents=True,exist_ok=True);p=OUT/NAME
guide='''# M0 E2 complete sentinel evidence

Verdict: M0_E2_CRN_SENTINEL_QUALIFIED. Exactly four new S0/r01 wrong-wind runs; zero new U0 and zero E3. Stop.

Unpack R0_FROZEN_ORIGINAL.zip here to obtain m0_clean_support_r0_20261007 beside m0_e2_sentinel_20261007. Unpack its M0_E2_RAW_NATIVE_20261007.zip into evidence/. Read REPORT_zh.md and README_REPRODUCE.md. Run verify_evidence_package.py, analyze_e2_clock_serialization_erratum.py and the unchanged pre-run verify_e2_independent.py on a copy, with NumPy>=1.22 and SciPy. These perform no simulation.

All four native result directories, actual inputs/readback, runtime/source hashes, trajectories/columns/state dumps/parity, clocks, and the full completed U0 S0/r01 reference are included. Original pre-run code, false-HOLD initial audit, and the one-expression clock serialization erratum remain traceable. No scientific contract, threshold, wind, source, gas, route, seed or window changed. Original full E1 archive remains pinned on GitHub; its hash is in the authorization and replay guide.

The remaining 28 wrong-wind runs require fresh user authorization. There is no M0_PASS, posterior damage verdict or algorithm training.
'''
with zipfile.ZipFile(p,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('README_PACKAGE.md',guide);z.write(original,'R0_FROZEN_ORIGINAL.zip')
    for q in sorted(files):z.write(q,'m0_e2_sentinel_20261007/'+q.relative_to(R).as_posix())
with zipfile.ZipFile(p) as z:
    assert z.testzip() is None;assert hashlib.sha256(z.read('R0_FROZEN_ORIGINAL.zip')).hexdigest()==sha(original)
    for q in files:assert hashlib.sha256(z.read('m0_e2_sentinel_20261007/'+q.relative_to(R).as_posix())).hexdigest()==sha(q)
verification={'archive':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'CRC_and_member_hashes':'PASS','member_count':len(files)+2,'verdict':dec['verdict'],'new_wrong_wind_runs':4,'new_U0_runs':0,'remaining_28_runs':0,'clock_serialization_erratum_and_original_false_HOLD_retained':True}
(OUT/'PACKAGE_VERIFICATION.json').write_bytes((json.dumps(verification,indent=2)+'\n').encode());(OUT/(NAME+'.sha256')).write_bytes((verification['sha256']+'  '+NAME+'\n').encode());print(json.dumps(verification,indent=2))
