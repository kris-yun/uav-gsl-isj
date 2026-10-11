"""Verify the actual ZIP in a fresh directory, with independent read-only scripts."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,zipfile,subprocess,time,os,psutil
BASE=Path(__file__).resolve().parents[2]
DEST=BASE/'work/rk2_fresh_zip_validation'
assert not DEST.exists();DEST.mkdir()
ZIP=BASE/'outputs/PMFS_RK2_PROTOTYPE_REVIEW_BUNDLE_20261010_REVIEW.zip'
ROOT=DEST/'package';ROOT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(ZIP) as z:
    assert z.testzip() is None
    for info in z.infolist():
        dest=(ROOT/info.filename).resolve()
        assert ROOT.resolve() in dest.parents and not info.is_dir(),info.filename
        assert not ((info.external_attr>>16)&0o170000)==0o120000,'No archive symlinks'
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(info))
before={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file()}
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
def run(label,args):
    start=time.perf_counter();peak=0
    with (DEST/(label+'.stdout')).open('w',encoding='utf-8') as out,(DEST/(label+'.stderr')).open('w',encoding='utf-8') as err:
        p=subprocess.Popen([sys.executable,'-B','-X','utf8',*map(str,args)],stdout=out,stderr=err,env=env)
        while p.poll() is None:
            try:
                ps=psutil.Process(p.pid);rss=ps.memory_info().rss
                for c in ps.children(recursive=True):
                    try:rss+=c.memory_info().rss
                    except psutil.Error:pass
                peak=max(peak,rss)
            except psutil.Error:pass
            if time.perf_counter()-start>60:
                p.terminate();raise RuntimeError('Read-only verifier exceeded60s')
            time.sleep(.02)
    assert p.returncode==0,(label,(DEST/(label+'.stderr')).read_text(encoding='utf-8'))
    return dict(status='PASS',exitcode=p.returncode,wall_s=time.perf_counter()-start,sampled_process_tree_peak_RSS_bytes=peak)
full=run('full_verification',[ROOT/'verify_bundle.py','--root',ROOT,'--parent',BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010','--out',DEST/'full_QA'])
isolated=run('isolated_infer',[ROOT/'verification/audit_infer_process.py','--package',ROOT/'RK2_NEW','--out',DEST/'isolated_infer_QA'])
after={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file()}
assert before==after,'Verifiers altered package bytes'
record=dict(status='PASS_FRESH_ARCHIVE_FULL_LINEAGE_AND_ISOLATED_INFER',ZIP_SHA256=sha(ZIP),ZIP_bytes=ZIP.stat().st_size,
    root_manifest_SHA256=sha(ROOT/'SHA256SUMS.json'),files_unchanged=len(before),full_verification=full,isolated_infer=isolated,
    all_verification_wall_s=full['wall_s']+isolated['wall_s'],new_scientific_fits=0,phi_LOS_calls=0,new_physics=0,
    cold_compressed_archive_CRC='PASS',fresh_extraction=str(ROOT),note='Independent verifier repeats cached-state arithmetic and scalar infer only; no experiment rerun.')
(DEST/'FRESH_ARCHIVE_VALIDATION.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'outputs/PMFS_RK2_FRESH_ARCHIVE_VALIDATION.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
