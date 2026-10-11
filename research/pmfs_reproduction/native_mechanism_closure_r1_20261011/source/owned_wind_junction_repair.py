from common_n import *
import shutil
data=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011').resolve();canon=data/'SHARED_IDENTICAL_CFD_INPUTS';names=sorted(p.name for p in canon.iterdir());assert len(names)==11
expected={n:sha(canon/n) for n in names};proof=[]
for bank in (data/'factorial').iterdir():
 if not bank.is_dir() or not (bank/'QUALIFICATION.json').exists():continue
 wind=bank/'bank/wind';assert wind.resolve().is_relative_to(data) and not wind.is_symlink();assert sorted(p.name for p in wind.iterdir())==names
 assert all(sha(wind/n)==expected[n] for n in names);amount=sum((wind/n).stat().st_size for n in names);backup=wind.with_name('wind_verified_duplicate_backup');assert not backup.exists();wind.rename(backup)
 # Native NTFS junction is supported even though the HGFS server rejects Linux symlink creation.
 script="$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path '"+str(wind).replace("'","''")+"' -Target '"+str(canon).replace("'","''")+"' | Out-Null"
 p=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,text=True)
 if p.returncode:backup.rename(wind);raise RuntimeError(p.stderr)
 assert all(sha(wind/n)==expected[n] and (wind/n).stat().st_ino==(canon/n).stat().st_ino for n in names)
 assert backup.resolve().is_relative_to(data) and not backup.is_symlink() and sorted(p.name for p in backup.iterdir())==names
 # Delete only11 named, verified duplicate files; the canonical copies and all gas frames remain.
 for n in names:(backup/n).unlink()
 backup.rmdir();proof.append(dict(logical_directory=wind.as_posix(),canonical_directory=canon.as_posix(),bytes_redundant=amount))
result=dict(status='PASS_NATIVE_NTFS_JUNCTION_STORAGE_ONLY',records=proof,unique_canonical_bytes=sum((canon/n).stat().st_size for n in names),saved_bytes=sum(r['bytes_redundant'] for r in proof)-sum((canon/n).stat().st_size for n in names),CFD_SHA256=expected,all_gas_frames_unchanged=True,original_CFD_assets_untouched=True)
dump(CORE/'OWN_WIND_STORAGE_DEDUPLICATION.json',result);dump(data/'OWN_WIND_STORAGE_DEDUPLICATION.json',result)
code='''from pathlib import Path
import hashlib,json
d=Path(DATA);names=NAMES;expected=EXPECTED
for p in (d/'factorial').iterdir():
 if p.is_dir() and (p/'QUALIFICATION.json').exists():
  assert all(hashlib.sha256((p/'bank/wind'/n).read_bytes()).hexdigest()==expected[n] for n in names)
print(json.dumps({'status':'PASS_VM_READS_ALL32_JUNCTION_BANK_WIND_IDENTICALLY'}))
'''.replace('DATA',repr(DATA)).replace('NAMES',repr(names)).replace('EXPECTED',repr(expected))
r=json.loads(run_remote(code,'native_host_junction_VM_read_verification',120));dump(CORE/'WIND_STORAGE_VM_READ_VERIFY.json',r)
print(json.dumps({'status':result['status'],'saved_bytes':result['saved_bytes'],'VM_read_pass':r['status']}))
