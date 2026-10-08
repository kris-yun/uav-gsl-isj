"""Fresh Linux extraction and mathematical replay. No native executable calls."""
from pathlib import Path
import hashlib,json,platform,subprocess,sys,zipfile
import numpy,scipy
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e2_linux_readonly_review');OUT=R/'extracted';RAW=R.parent.parent/'M0_E2_RAW_NATIVE_20261007.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists();receipt=json.loads((R/'LINUX_REVIEW_INPUTS_RECEIPT.json').read_text());assert sha(R/'LINUX_REVIEW_INPUTS.zip')==receipt['input_zip_sha256'];assert sha(RAW)==receipt['uses_verified_VM_native_zip_sha256']
with zipfile.ZipFile(R/'LINUX_REVIEW_INPUTS.zip') as z:assert z.testzip() is None;z.extractall(OUT)
with zipfile.ZipFile(OUT/'R0_FROZEN_ORIGINAL.zip') as z:assert z.testzip() is None;z.extractall(OUT)
E=OUT/'m0_e2_sentinel_20261007';(E/'evidence').mkdir()
with zipfile.ZipFile(RAW) as z:assert z.testzip() is None;z.extractall(E/'evidence')
codes={}
for script in [OUT/'m0_clean_support_r0_20261007/freeze_design.py',E/'analyze_e2_clock_serialization_erratum.py',E/'verify_e2_independent.py']:
    args=[sys.executable,'-B',str(script)]
    if script.name=='freeze_design.py':args+=['--verify']
    with (R/(script.stem+'.stdout.log')).open('wb') as f:codes[script.name]=subprocess.run(args,cwd=E,stdout=f,stderr=subprocess.STDOUT).returncode
    assert codes[script.name]==0,script.name
decision=json.loads((E/'E2_DECISION.json').read_text());ind=json.loads((E/'INDEPENDENT_E2_VERIFICATION.json').read_text());assert decision['verdict']=='M0_E2_CRN_SENTINEL_QUALIFIED' and ind['status']=='INDEPENDENT_E2_VERIFICATION_PASS'
result={'status':'LINUX_FRESH_EXTRACTION_REPLAY_PASS','Python':platform.python_version(),'NumPy':numpy.__version__,'SciPy':scipy.__version__,'input_zip_sha256':receipt['input_zip_sha256'],'native_zip_sha256':sha(RAW),'script_exit_codes':codes,'verdict':decision['verdict'],'native_files_verified':ind['native_files_verified'],'R0_frozen_files_verified':ind['frozen_R0_files_verified'],'new_scientific_runs':0,'simulator_invoked':False,'native_parity_queries':ind['native_sampling_queries_verified'],'scientific_M0_verdict':'NOT_TESTED','remaining_28_launched':False}
(R/'LINUX_REPLAY_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
