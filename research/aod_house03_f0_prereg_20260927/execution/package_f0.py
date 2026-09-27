#!/usr/bin/env python3
"""Package committed F0 evidence, verifying working bytes against Git blobs."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,shutil
W=Path(__file__).resolve().parents[3]
R='research/aod_house03_f0_prereg_20260927';E='evidence/aod_house03_f0_prereg_20260927'
BASE='25803d287aa299f78a06458e37437a91c3fa3890'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=W)
def main():
    head=git('rev-parse','HEAD').decode().strip();assert head!=BASE
    branch=git('branch','--show-current').decode().strip();assert branch=='research/aod-house03-f0-prereg-20260927'
    assert not git('status','--porcelain','--',R,E).strip()
    result=json.loads((W/E/'F0_RESULT.json').read_text());assert result['decision']=='AOD_H03_F0_READY_FOR_PREREG'
    files=git('ls-tree','-r','--name-only',head,'--',R,E).decode().splitlines();payload={}
    for n in files:
        b=(W/n).read_bytes();assert git('show',head+':'+n)==b,n;payload[n]=b
    for line in payload[E+'/F0_SHA256SUMS.txt'].decode().splitlines():
        h,n=line.split('  ',1);assert sha(payload[n])==h,n
    gitstate=dict(branch=branch,base_commit=BASE,final_commit=head,decision=result['decision'],committed_F0_files=len(files),working_files_match_committed_blobs=True,scoped_working_tree_clean=True,gaden_executed=0,pmfs_forward_executed=0,F1_authorized=False)
    payload['GIT_STATE.json']=(json.dumps(gitstate,indent=2)+'\n').encode()
    detailed=dict(result,final_commit=head);detailed.pop('final_commit_record',None)
    payload['F0_RESULT_WITH_COMMIT.json']=(json.dumps(detailed,indent=2)+'\n').encode()
    payload['F0_COMMITTED_PATCH.diff']=git('diff','--binary',BASE,head,'--',R,E)
    payload['README.md']=(f'# AOD House03 F0 review\n\nDecision: **{result["decision"]}**\n\nBranch: `{branch}`\n\nBase: `{BASE}`\n\nFinal commit: `{head}`\n\nRead `{E}/F0_FREEZE_REPORT.md` first. The complete panel, route segments, wind hashes, future seeds and independent verification are under `{E}`. Original protocol and execution/audit scripts are under `{R}`.\n\nF0 has generated no gas and executed no forward or score. F1 remains unauthorized. Before F1 execution, bind the frozen physical 50-second observation slots to simulator timestamps and adequate duration; historical frame numbers are not seconds.\n').encode()
    payload['REVIEW_SHA256SUMS.txt']=''.join(f'{sha(b)}  {n}\n' for n,b in sorted(payload.items())).encode()
    out=Path(r'D:\ZYC\A-gas\_staging\AOD_H03_F0_READY_FOR_PREREG_REVIEW_20260927.zip');assert not out.exists()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(payload.items()):
            zi=zipfile.ZipInfo(n,(2026,9,27,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,b)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for line in z.read('REVIEW_SHA256SUMS.txt').decode().splitlines():h,n=line.split('  ',1);assert sha(z.read(n))==h,n
    delivery=Path(r'C:\Users\50176\Downloads')/out.name;assert not delivery.exists();shutil.copy2(out,delivery)
    receipt=dict(gitstate,review_zip_path=str(delivery),review_zip_bytes=delivery.stat().st_size,review_zip_sha256=sha(delivery.read_bytes()),review_files=len(payload),review_hashes_verified=True)
    root=Path(r'D:\ZYC\A-gas\_staging\AOD_H03_F0_EXECUTION_20260927')
    (root/'DELIVERY_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (delivery.with_suffix('.zip.sha256')).write_text(f'{receipt["review_zip_sha256"]}  {delivery.name}\n')
    shutil.copy2(W/E/'F0_FREEZE_REPORT.md',root/'F0_FREEZE_REPORT.md')
    (root/'F0_RESULT_WITH_COMMIT.json').write_text(json.dumps(detailed,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
