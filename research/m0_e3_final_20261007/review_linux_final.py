"""Fresh ZIP replay of complete all40 evidence, no native executable invoked."""
from pathlib import Path
import hashlib,json,platform,subprocess,sys,zipfile
import numpy,scipy
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007/final_linux_review');OUT=R/'extracted';ROOT=Path('/home/zyc/ros2_ws')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists()
receipt=json.loads((R/'LINUX_REVIEW_INPUT_RECEIPT.json').read_text());assert sha(R/'FINAL_LINUX_REVIEW_INPUTS.zip')==receipt['sha256']
with zipfile.ZipFile(R/'FINAL_LINUX_REVIEW_INPUTS.zip') as z:assert z.testzip() is None;z.extractall(OUT)
E=OUT/'m0_e3_final_20261007';D=E/'evidence';D.mkdir();manifest=json.loads((E/'M0_NATIVE_PACKAGES_MANIFEST_20261007.json').read_text())
for q in manifest['packages']:
    p=ROOT/q['name'];assert sha(p)==q['sha256']
    with zipfile.ZipFile(p) as z:assert z.testzip() is None;z.extractall(D)
codes={}
for script in [OUT/'m0_clean_support_r0_20261007/freeze_design.py',E/'evaluate_final.py',E/'verify_final_independent.py',E/'verify_secondary_global.py']:
    args=[sys.executable,'-B',str(script)]
    if script.name=='freeze_design.py':args+=['--verify']
    with (R/(script.stem+'.stdout.log')).open('wb') as f:codes[script.name]=subprocess.run(args,cwd=E,stdout=f,stderr=subprocess.STDOUT).returncode
    assert codes[script.name]==0,script.name
dec=json.loads((E/'FINAL_DECISION.json').read_text());ind=json.loads((E/'INDEPENDENT_FINAL_VERIFICATION.json').read_text());assert dec['verdict']==ind['independent_verdict']
result={'status':'LINUX_COMPLETE40_FRESH_REPLAY_PASS','verdict':dec['verdict'],'Python':platform.python_version(),'NumPy':numpy.__version__,'SciPy':scipy.__version__,'script_exit_codes':codes,'raw_files_verified':ind['native_files_verified'],'qualified_runs':40,'input_archive_sha256':receipt['sha256'],'new_scientific_runs':0,'native_executable_invoked':False,'max_posterior_difference':ind['max_posterior_difference'],'STOP':True}
(R/'LINUX_FINAL_REPLAY_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
