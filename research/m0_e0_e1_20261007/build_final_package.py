"""One-shot evidence seal/ZIP; no native execution, no edits to R0."""
from pathlib import Path
import csv,datetime,hashlib,json,zipfile
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';DELIVERY=Path('D:/ZYC/A-gas/_deliveries/M0_E0_E1_20261007');NAME='M0_E0_E1_BASELINE_QUALIFIED_FULL_EVIDENCE_20261007.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
decision=json.loads((R/'E1_DECISION.json').read_text(encoding='utf-8'));assert decision['verdict']=='M0_E1_BASELINE_QUALIFIED' and decision['actual_U0_runs']==8 and decision['actual_wrong_wind_runs']==0
assert json.loads((R/'INDEPENDENT_E1_VERIFICATION.json').read_text())['status']=='INDEPENDENT_E1_VERIFICATION_PASS'
assert json.loads((R/'E1_POST_RESOURCE_SNAPSHOT.json').read_text())['resource_gate_pass']
freeze=R/'E1_EVIDENCE_SEAL.json';manifest=R/'E1_EVIDENCE_FILES_SHA256.csv';assert not freeze.exists() and not manifest.exists()
files=sorted(p for p in R.rglob('*') if p.is_file() and not any(x in p.parts for x in ['staging','evidence','__pycache__']) and p.suffix!='.pyc')
with manifest.open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
seal={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':decision['verdict'],'U0_runs':8,'wrong_wind_runs':0,'M0_scientific_verdict':'NOT_TESTED','R0_frozen_seal_sha256':sha(F/'M0_R0_FREEZE.json'),'execution_scope':'E0+E1 completed then stopped','E2_authorized':False,'manifest_sha256':sha(manifest),'native_raw_zip_sha256':sha(R/'M0_E0_E1_RAW_NATIVE_20261007.zip'),'included_execution_files':len(files)}
freeze.write_bytes((json.dumps(seal,indent=2)+'\n').encode());files.extend([manifest,freeze])
old=R.parent/'M0_CLEAN_SUPPORT_DESIGN_R0_FROZEN_20261007.zip';assert sha(old)=='ffdb1be5452f6bb7a3e2500b13e40261a0e1f44223868bcc3f86824d6489f658'
DELIVERY.mkdir(parents=True,exist_ok=True);archive=DELIVERY/NAME
guide='''# M0 E0/E1 complete evidence\n\nVerdict: M0_E1_BASELINE_QUALIFIED. Eight U0 baselines; zero wrong-wind runs. Stop.\n\nUnzip the unchanged R0_FROZEN_ORIGINAL.zip here to create m0_clean_support_r0_20261007 beside m0_e0_e1_20261007. Inside the execution folder, unpack M0_E0_E1_RAW_NATIVE_20261007.zip into evidence/. Read REPORT_zh.md and README_REPRODUCE.md. Verify relative file hashes with E1_EVIDENCE_FILES_SHA256.csv. Review can run verify_r0_portable.py, analyze_e1.py and verify_e1_independent.py without launching ROS or GADEN. Preserve the pre-run source seal.\n\nThe raw native archive contains all inputs, wind decoder readback, all eight native output directories, clocks, state dumps, source snapshots, per-run argv/env/time/RSS and runtime dependency hashes. No threshold/source/route/seed/window was changed. Wrong-wind CRN is still pending E2; no M0_PASS or PRIMARY_GO claim.\n'''
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('README_PACKAGE.md',guide);z.write(old,'R0_FROZEN_ORIGINAL.zip')
    for p in sorted(files):z.write(p,'m0_e0_e1_20261007/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert hashlib.sha256(z.read('R0_FROZEN_ORIGINAL.zip')).hexdigest()==sha(old)
    for p in files:assert hashlib.sha256(z.read('m0_e0_e1_20261007/'+p.relative_to(R).as_posix())).hexdigest()==sha(p)
result={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'CRC_and_member_hashes':'PASS','member_count':len(files)+2,'verdict':'M0_E1_BASELINE_QUALIFIED','U0_runs':8,'wrong_wind_runs':0,'E2_authorized':False}
(DELIVERY/'PACKAGE_VERIFICATION.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());(DELIVERY/(NAME+'.sha256')).write_bytes((result['sha256']+'  '+NAME+'\n').encode())
print(json.dumps(result,indent=2))
