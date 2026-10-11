"""Hash-only finalization; no old files, validation rules or physics are modified."""
import hashlib,json,platform
from pathlib import Path
import numpy,cv2,pandas
W=Path(__file__).resolve().parent;ROOT=W.parents[2]
COMBINED=ROOT/'outputs/PMFS_M2_M3_COMBINED_ROOT_CAUSE_20261010'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((COMBINED/'SHA256_MANIFEST.json').read_text());assert all(sha(COMBINED/n)==h for n,h in manifest.items())
m2zip=ROOT/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010_REVIEW.zip'
scope=dict(status='READ_ONLY_PRO_REVIEW_COMPLETED',new_forward_calls=0,new_GADEN=0,new_CFD=0,new_ROS=0,new_training=0,
  unchanged_combined_members=len(manifest),combined_manifest_SHA256=sha(COMBINED/'SHA256_MANIFEST.json'),
  M2_ZIP_SHA256=sha(m2zip),old_verify_combined_SHA256=sha(COMBINED/'verify_combined.py'),old_verify_M3_SHA256=sha(COMBINED/'M3_NEW/verify_m3.py'),
  independently_recomputed_frozen_3D_state_script_SHA256=sha(COMBINED/'M3_NEW/forward_contract_audit/audit_3d_state_aliasing.py'),
  current_environment=dict(python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,opencv=cv2.__version__),
  dependencies='Recompute requires the unchanged previous combined M2/M3 audit root, and original M2 ZIP for the provider integrity script. New package contains derived evidence and provider ZIP, not a fabricated duplicate of physical banks.')
(W/'AUDIT_SCOPE_AND_INPUT_SHA256.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
files={p.relative_to(W).as_posix():sha(p) for p in sorted(W.rglob('*')) if p.is_file() and p.name!='PRO_REVIEW_SHA256SUMS.json' and '__pycache__' not in p.parts}
(W/'PRO_REVIEW_SHA256SUMS.json').write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(sha(W/n)==h for n,h in files.items())
print(json.dumps(dict(files=len(files),bytes=sum((W/n).stat().st_size for n in files),manifest_SHA256=sha(W/'PRO_REVIEW_SHA256SUMS.json'),scope=scope),indent=2))
