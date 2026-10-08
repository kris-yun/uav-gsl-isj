"""Final evidence seal and complete lossless ZIP, then SHA-verified byte parts."""
from pathlib import Path
import csv,datetime,hashlib,json,zipfile
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';OUT=Path('D:/ZYC/A-gas/_deliveries/M0_FINAL_20261007')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
decision=json.loads((R/'FINAL_DECISION.json').read_text());ind=json.loads((R/'INDEPENDENT_FINAL_VERIFICATION.json').read_text());linux=json.loads((R/'LINUX_FINAL_REPLAY_VERIFICATION.json').read_text());assert decision['verdict']==ind['independent_verdict']==linux['verdict'] and ind['status']=='INDEPENDENT_FINAL_VERIFICATION_PASS' and linux['status']=='LINUX_COMPLETE40_FRESH_REPLAY_PASS'
name='M0_'+decision['verdict']+'_ALL40_FULL_EVIDENCE_20261007.zip';assert not (R/'FINAL_EVIDENCE_SEAL.json').exists()
manifest=R/'FINAL_EVIDENCE_FILES_SHA256.csv';files=sorted(p for p in R.rglob('*') if p.is_file() and not any(x in p.parts for x in ['evidence','frozen','__pycache__']) and p.suffix!='.pyc')
with manifest.open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
seal={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':decision['verdict'],'scientific_runs':40,'new_E3_runs':28,'retries_or_extra_runs':0,'qualified_runs':40,'R0_frozen_seal_sha256':sha(F/'M0_R0_FREEZE.json'),'E3_pre_run_seal_sha256':sha(R/'E3_EXECUTION_SEAL.json'),'manifest_sha256':sha(manifest),'included_files':len(files),'independent_Windows_and_Linux_pass':True,'STOP':True};sealfile=R/'FINAL_EVIDENCE_SEAL.json';sealfile.write_bytes((json.dumps(seal,indent=2)+'\n').encode());files.extend([manifest,sealfile])
original=R.parent/'M0_CLEAN_SUPPORT_DESIGN_R0_FROZEN_20261007.zip';assert sha(original)=='ffdb1be5452f6bb7a3e2500b13e40261a0e1f44223868bcc3f86824d6489f658';OUT.mkdir(parents=True,exist_ok=True);archive=OUT/name
guide='''# M0 complete40 scientific evidence

Verdict: M0_STOP. All40 runs qualified; exactly28 new E3, no retries or extras. Stop this frozen candidate mechanism route. FSR dataset construction remains independent.

Unpack unchanged R0_FROZEN_ORIGINAL.zip here. In m0_e3_final_20261007, verify FINAL_EVIDENCE_SEAL/manifest, and unpack all six M0_NATIVE_*.zip into one evidence/ folder. Read REPORT_zh.md and README_REPRODUCE.md. Numerical review calls evaluate_final.py, verify_final_independent.py and verify_secondary_global.py, with no simulator. The native partitions cover all40 originals plus runtime/source/input/output hashes, time/RSS/argv/env/logs, all iterations and state/ROI/global/parity outputs. Primary code was sealed before E3; frozen scientific gate was not modified. Independent Windows and fresh Linux replay agree.

GitHub's ordered byte parts reassemble this exact complete ZIP with FULL_ARCHIVE_PARTS.json and reassemble_full_archive.py. No part is discarded. No source/seed/route/window/threshold redesign, neural training or new simulation follows the verdict.
'''
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('README_PACKAGE.md',guide);z.write(original,'R0_FROZEN_ORIGINAL.zip')
    for p in sorted(files):z.write(p,'m0_e3_final_20261007/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and hashlib.sha256(z.read('R0_FROZEN_ORIGINAL.zip')).hexdigest()==sha(original)
    for p in files:assert hashlib.sha256(z.read('m0_e3_final_20261007/'+p.relative_to(R).as_posix())).hexdigest()==sha(p)
partsdir=OUT/'parts';partsdir.mkdir();parts=[]
with archive.open('rb') as f:
    i=0
    while chunk:=f.read(45000000):
        i+=1;p=partsdir/(name+'.part'+str(i).zfill(3));p.write_bytes(chunk);parts.append({'name':p.name,'bytes':len(chunk),'sha256':sha(p)})
joined=hashlib.sha256()
for q in parts:
    with (partsdir/q['name']).open('rb') as f:
        while block:=f.read(1024*1024):joined.update(block)
assert joined.hexdigest()==sha(archive)
partmanifest={'archive_name':name,'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'parts':parts,'part_order':'listed order','verdict':decision['verdict'],'scientific_runs':40,'new_E3_runs':28,'all40_qualified':True,'independent_replay_pass':True};(partsdir/'FULL_ARCHIVE_PARTS.json').write_bytes((json.dumps(partmanifest,indent=2)+'\n').encode());(OUT/(name+'.sha256')).write_bytes((partmanifest['archive_sha256']+'  '+name+'\n').encode())
receipt={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'CRC_and_all_member_hashes':'PASS','byte_parts_reassembly_hash':'PASS','parts':len(parts),'outer_members':len(files)+2,'verdict':decision['verdict'],'scientific_runs':40,'new_E3_runs':28,'qualified_runs':40};(OUT/'PACKAGE_VERIFICATION.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode());print(json.dumps(receipt,indent=2))
