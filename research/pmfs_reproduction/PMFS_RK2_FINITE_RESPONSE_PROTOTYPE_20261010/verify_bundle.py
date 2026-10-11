"""Read-only RK2 new-only package verification. No producer/model/infer imports."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,hashlib,importlib.util,time,threading,os

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def module(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def verify(root,parent=None):
    manifest=load(root/'SHA256SUMS.json')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual==set(manifest)|{'SHA256SUMS.json'},'Unexpected/missing package files'
    for n,h in manifest.items():assert sha(root/n)==h,n
    run=root/'RK2_NEW'
    saved,tables=module(root/'verification/verify_rk2_saved_only.py','saved_checker').verify(run)
    provenance=load(run/'NUMERICAL_REPAIR_PROVENANCE.json')
    first=root/'FIRST_NUMERICAL_ATTEMPT_FROZEN'
    for n,h in provenance['first_attempt_hashes'].items():assert sha(first/n)==h,n
    assert not (first/'models').exists() and not (first/'SOURCE_TASK_PREDICTIONS_BLIND.json').exists()
    assert load(first/'EXECUTION_LEDGER.json')['wall_s']+load(run/'EXECUTION_LEDGER.json')['wall_s']<=600
    pro=root/'PRO_RK1_REVIEW_FROZEN'
    pm=load(pro/'SHA256_MANIFEST.json')
    # Original PRO handoff format is a relative-path SHA dict.
    for n,h in pm.items():assert sha(pro/n)==h,n
    assert sha(root/'PRO_RK1_ORIGINAL_HANDOFF.zip')==load(root/'PARENT_REFERENCE.json')['PRO_handoff_ZIP_SHA256']
    assert load(root/'INDEPENDENT_REVIEW/isolated_infer_process_validation_v2/INFER_PROCESS_AUDIT_RESULT.json')['status']=='PASS_ISOLATED_SOURCE_BLIND_INFER_PROCESS'
    full=None
    if parent is not None:
        assert sha(parent/'SHA256SUMS.json')==load(root/'PARENT_REFERENCE.json')['RK1_root_manifest_SHA256']
        full,_=module(root/'verification/verify_rk2.py','full_checker').verify(run,parent)
    return dict(status='PASS_RK2_NEW_ONLY_PACKAGE',manifest_members=len(manifest),first_attempt_members=len(provenance['first_attempt_hashes']),PRO_handoff_members=len(pm),
        saved_only=saved,full_parent_lineage=full,scientific_fits=0,phi_LOS_calls=0,new_physics=0,
        scope='Checks recorded information-isolation evidence, not an isolation rerun. Optional parent enables raw-cache training-lineage check.'),tables

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--parent',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();assert not a.out.exists(),'Use a fresh external QA output directory'
    root=a.root.resolve();out=a.out.resolve();assert out!=root and root not in out.parents
    start=time.perf_counter();peak=[0];stop=threading.Event()
    try:
        import psutil
        proc=psutil.Process()
        def sample():
            while not stop.is_set():
                peak[0]=max(peak[0],proc.memory_info().rss);stop.wait(.02)
        th=threading.Thread(target=sample,daemon=True);th.start()
    except ImportError:th=None
    try:
        result,tables=verify(root,a.parent)
    finally:
        stop.set()
        if th:th.join()
    result['verification_wall_s']=time.perf_counter()-start
    result['verification_sampled_peak_RSS_bytes']=peak[0] or None
    result['peak_sampling_interval_s']=.02
    out.mkdir(parents=True)
    (out/'PACKAGE_VERIFICATION_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
