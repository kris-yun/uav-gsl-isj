"""Archive-only review inputs; no simulation."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent;OUT=R/'LINUX_REVIEW_INPUTS.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists()
files=sorted(p for p in R.rglob('*') if p.is_file() and 'evidence' not in p.parts and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='M0_E2_RAW_NATIVE_20261007.zip')
original=R.parent/'M0_CLEAN_SUPPORT_DESIGN_R0_FROZEN_20261007.zip'
with zipfile.ZipFile(OUT,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(original,'R0_FROZEN_ORIGINAL.zip')
    for p in files:z.write(p,'m0_e2_sentinel_20261007/'+p.relative_to(R).as_posix())
receipt={'input_zip_sha256':sha(OUT),'bytes':OUT.stat().st_size,'files':len(files)+1,'contains_simulator_outputs':False,'uses_verified_VM_native_zip_sha256':'f2833ae96a9650a3734206867036cb2ac82da424b3a95a5634b162a9c4dff670'}
(R/'LINUX_REVIEW_INPUTS_RECEIPT.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode());print(json.dumps(receipt,indent=2))
