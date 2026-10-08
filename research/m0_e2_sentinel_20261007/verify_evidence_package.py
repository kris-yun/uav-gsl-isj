"""Read-only, cross-platform E2 outer evidence seal and frozen hashes."""
from pathlib import Path
import csv,hashlib,json,zipfile
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
seal=json.loads((R/'E2_EVIDENCE_SEAL.json').read_text());assert sha(R/'E2_EVIDENCE_FILES_SHA256.csv')==seal['manifest_sha256']
with (R/'E2_EVIDENCE_FILES_SHA256.csv').open(encoding='utf-8') as f:files=list(csv.DictReader(f))
for q in files:assert sha(R/q['path'])==q['sha256'] and (R/q['path']).stat().st_size==int(q['bytes']),q['path']
with (F/'M0_R0_FILES_SHA256.csv').open(encoding='utf-8') as f:r0=list(csv.DictReader(f))
for q in r0:assert sha(F/q['path'])==q['sha256']
assert sha(R/'M0_E2_RAW_NATIVE_20261007.zip')==seal['raw_native_archive_sha256']
with zipfile.ZipFile(R/'M0_E2_RAW_NATIVE_20261007.zip') as z:assert z.testzip() is None
print(json.dumps({'E2_evidence_and_CRC':'PASS','frozen_R0_files_verified':len(r0),'execution_files_verified':len(files),'scientific_runs':4,'E3_runs':0},indent=2))
