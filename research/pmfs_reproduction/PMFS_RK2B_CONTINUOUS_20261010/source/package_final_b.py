"""Exact-byte manifests, bounded final packaging and portable verifier checks."""
from common_b import *
import shutil,zipfile,psutil

def size(p):
    p=Path(p)
    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.is_dir() else (p.stat().st_size if p.exists() else 0)

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def manifest(root):
    value={p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
    dump(root/'MANIFEST_SHA256.json',value)
    return len(value)

def run_bounded(args, name, timeout):
    start=time.perf_counter(); peak=0; reason=None
    out=WORK/(name+'.stdout');err=WORK/(name+'.stderr');assert not out.exists() and not err.exists()
    with out.open('wb') as fo,err.open('wb') as fe:
        p=subprocess.Popen(args,stdout=fo,stderr=fe)
        while p.poll() is None:
            try:
                q=psutil.Process(p.pid);rss=q.memory_info().rss+sum(x.memory_info().rss for x in q.children(recursive=True) if x.is_running());peak=max(peak,rss)
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
            if time.perf_counter()-start>timeout or peak>1024**3:
                reason='WALL_OR_RSS_STOP';p.kill();break
            time.sleep(.1)
        code=p.wait()
    result=dict(name=name,wall_s=time.perf_counter()-start,sampled_peak_RSS_bytes=peak,exitcode=code,resource_stop=reason)
    assert code==0 and reason is None,dict(result=result,error=err.read_text(encoding='utf-8',errors='replace'))
    result['verifier_result']=json.loads(out.read_text(encoding='utf-8'))
    return result

def main():
    start=time.perf_counter();parent=load(PARENT/'SHA256SUMS.json')
    # The parent is already verified; this final confirmation also guards packaging.
    assert all(digest(PARENT/n)==h for n,h in parent.items())
    for log in ['INDEPENDENT_VERIFIER','INDEPENDENT_RAW_AND_TRAINING_QA','INDEPENDENT_TRANSFER_ATTRIBUTION_QA']:
        dump(CORE/(log+'_RESULT.json'),json.loads((CORE/(log+'.stdout')).read_text(encoding='utf-8')))
    s=load(CORE/'stage_status.json');post=load(CORE/'POSTEXECUTION_QA_LEDGER.json')
    qa=load(CORE/'INDEPENDENT_TRANSFER_ATTRIBUTION_QA_LEDGER.json');derived=load(CORE/'REGISTERED_DESCRIPTION_EXPORT_LEDGER.json')
    roots=[Path(load(CORE/'FULL_BANK_PRESERVATION.json')['complete_bank_root']),CORE,RAW,WORK,
           BASE/'work/pmfs_parity_checkout/research/pmfs_reproduction/PMFS_RK2B_CONTINUOUS_20261010']
    sizes={str(p):size(p) for p in roots};charge=sum(sizes.values())
    assert charge+1024**3<6*1024**3
    totalwall=s['campaign_wall_s']+sum(x['wall_s'] for x in post)+qa['wall_s']+derived['wall_s']
    assert totalwall<5400
    dump(CORE/'FINAL_BUDGET_AND_SAFETY_AUDIT.json',dict(status='PASS_BEFORE_PACKAGING',science_and_postexecution_measured_wall_s=totalwall,
        scientific_campaign_wall_s=s['campaign_wall_s'],limit_scientific_campaign_s=5400,
        final_packaging_and_portable_QA_are_delivery_work=True,new_disk_measured_before_archives_bytes=charge,
        conservative_delivery_space_reserve_bytes=1024**3,new_disk_cap_bytes=6*1024**3,
        charged_directories=sizes,VM_active_scientific_processes=[],root_free_bytes=load(CORE/'FINAL_VM_PROCESS_AND_RESOURCE_STATUS.json')['root_free_bytes'],
        root_minimum_free_before_generation_bytes=4*1024**3,
        RSS_limit_per_bounded_stage_bytes=1024**3,all_scientific_stage_exitcodes_zero=all(x['exitcode']==0 for x in s['stages']),
        final_independent_reconstruction_rows=3600,postexecution_export_first_failed_stdout_resource_note='Derived console JSON printing failed after exports; first failed helper wall about 6.7s; peak RSS not recorded for that helper; no physical/fit/inference rerun',
        no_original_data_deleted=True,no_new_VM=True,no_navigation=True,new_CFD=False))
    shutil.copyfile(Path(__file__),CORE/'source'/Path(__file__).name)
    counts={};archives=[]
    for root,cap in [(CORE,15*1024**2),(RAW,256*1024**2)]:
        counts[root.name]=manifest(root)
        path=root.with_suffix('.zip');assert not path.exists(),str(path)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for f in sorted(root.rglob('*')):
                if f.is_file():z.write(f,f.relative_to(root).as_posix())
        assert path.stat().st_size<=cap
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
        archives.append(dict(path=str(path),bytes=path.stat().st_size,SHA256=digest(path),manifested_files=counts[root.name],cap_bytes=cap))
    qa_root=WORK/'FINAL_EXTERNAL_QA';assert not qa_root.exists();qa_root.mkdir()
    for root in [CORE,RAW]:
        dest=qa_root/root.name;dest.mkdir()
        with zipfile.ZipFile(root.with_suffix('.zip')) as z:
            for name in z.namelist():
                target=(dest/name).resolve();assert target.is_relative_to(dest.resolve())
            z.extractall(dest)
        hashes=load(dest/'MANIFEST_SHA256.json')
        actual={f.relative_to(dest).as_posix() for f in dest.rglob('*') if f.is_file()}
        assert actual==set(hashes)|{'MANIFEST_SHA256.json'}
        assert all(digest(dest/n)==h for n,h in hashes.items())
    c=qa_root/CORE.name;r=qa_root/RAW.name
    python=sys.executable
    checks=[run_bounded([python,'-B','-X','utf8',str(c/'source/verify_b.py'),str(c)],'FINAL_EXTRACTED_CORE_VERIFIER',120),
            run_bounded([python,'-B','-X','utf8',str(c/'source/verify_raw_support_b.py'),str(c),str(r)],'FINAL_EXTRACTED_RAW_VERIFIER',120)]
    charge_after=sum(size(p) for p in roots)+sum(a['bytes'] for a in archives)
    assert charge_after<6*1024**3
    proof=dict(status='PASS_FINAL_ARCHIVE_SHA_CRC_EXACT_MANIFEST_AND_PORTABLE_RECOMPUTATION',archives=archives,
        portable_verifier_checks=checks,new_disk_charged_including_archives_extracts_bytes=charge_after,new_disk_cap_bytes=6*1024**3,
        whole_delivery_wall_s=time.perf_counter()-start,full_raw_banks_preserved=True,stopped=True)
    dump(BASE/'outputs/PMFS_RK2B_FINAL_ARCHIVE_VERIFICATION_20261010.json',proof)
    for a in archives:
        Path(a['path']+'.sha256').write_text(a['SHA256']+'  '+Path(a['path']).name+'\n',encoding='utf-8')
    print(json.dumps(proof,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
