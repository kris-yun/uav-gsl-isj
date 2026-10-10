"""Human-approved one-shot six-forward wrapper. Anchor mismatch stops with no retry."""
import sys
sys.dont_write_bytecode=True
import base64,hashlib,json
from pathlib import Path
from remote_local import run

WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[1]
OUT=ROOT/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
budget_path=OUT/'M1_A_FROZEN_FORWARD_BUDGET.json'
approval=dict(answer='批准这6次二维候选计算',origin='Direct human answer to budget question in this chat',
              maximum_calls=6,maximum_combined_wall_s=120,maximum_RSS_bytes=536870912,
              budget_sha256=hashlib.sha256(budget_path.read_bytes()).hexdigest(),
              new_ROS_nodes=0,new_3D_realizations=0,native_posterior_updates=0)
receipt=OUT/'M1_A_USER_BUDGET_APPROVAL.json'
assert not receipt.exists();receipt.write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
provenance=json.loads((OUT/'PREPARED_ENTRY_PROVENANCE.json').read_text(encoding='utf-8'))
code='''from pathlib import Path
import base64,csv,hashlib,json,math,os,signal,subprocess,time,traceback
target=Path('/home/zyc/pmfs_b4_m1_representation_20261010');snapshot=target/'snapshot'
root=target/'forward_calls';assert not root.exists();root.mkdir()
approval=json.loads(base64.b64decode(@@APPROVAL@@))
budget=json.loads((target/'FROZEN_FORWARD_BUDGET.json').read_text())
assert hashlib.sha256((target/'FROZEN_FORWARD_BUDGET.json').read_bytes()).hexdigest()==approval['budget_sha256']
assert hashlib.sha256((target/'m1_candidate_forward').read_bytes()).hexdigest()==@@EXE@@
for name,digest in budget['snapshot_file_hashes'].items():assert hashlib.sha256((snapshot/name).read_bytes()).hexdigest()==digest,name
(root/'USER_APPROVAL.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2))
env=os.environ.copy();env.update(LD_LIBRARY_PATH=@@LIBS@@,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
                               MKL_NUM_THREADS='1',QT_QPA_PLATFORM='offscreen')
ledger=dict(status='RUNNING_APPROVED_ONE_SHOT',attempted_calls=0,completed_calls=0,
            maximum_calls=6,combined_forward_wall_seconds=0.,peak_RSS_bytes=0,records=[],anchor_checks=[],
            ROS_nodes=0,native_updates=0,new_3D_realizations=0)
def save():(root/'EXECUTION_LEDGER.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
def anchor_check(job,out):
    frozen=snapshot/'anchors'/job['job'];row=json.loads((frozen/'NATIVE_ROW.json').read_text());name=row['candidate_id']
    files=[('blurred','maps/'+name+'.f32','maps/'+name+'.f32'),
           ('unblurred','maps/'+name+'_unblurred.f32','unblurred/'+name+'_unblurred.f32'),
           ('points','points/'+name+'.f32','points/'+name+'.f32')]
    checks={}
    for label,a,b in files:
        actual=(out/a).read_bytes();expected=(frozen/b).read_bytes()
        checks[label]=dict(byte_equal=actual==expected,bytes=len(actual),sha256=hashlib.sha256(actual).hexdigest())
        assert actual==expected,job['job']+':'+label+'_BYTE_MISMATCH'
    result=json.loads((out/'RESULT.json').read_text())
    for key in ['rng_before','rng_after']:
        assert result[key]==row[key],key
    for key in ['gaussian_index_before','gaussian_index_after']:
        assert result[key]==int(row[key]),key
    assert result['release_points']==int(row['point_count'])==2000
    assert math.isclose(result['score'],float(row['score']),rel_tol=5e-12,abs_tol=1e-300)
    return dict(job=job['job'],verdict='PASS_EXACT_NATIVE_MAP_POINTS_RNG_PHASE',file_checks=checks,
                score=result['score'],native_score=float(row['score']))
try:
    for number,job in enumerate(budget['jobs']):
        if number>=2:assert len(ledger['anchor_checks'])==2
        assert ledger['attempted_calls']<6
        out=root/job['job'];assert not out.exists()
        ledger['attempted_calls']+=1;save()
        start=time.monotonic();peak=0;reason=None
        with (root/(job['job']+'.stdout')).open('w') as stdout,(root/(job['job']+'.stderr')).open('w') as stderr:
            process=subprocess.Popen([str(target/'m1_candidate_forward'),str(snapshot),str(snapshot/(job['job']+'.csv')),str(out)],
                                     env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            while process.poll() is None:
                rss=0
                for entry in Path('/proc').iterdir():
                    if not entry.name.isdigit():continue
                    try:
                        if os.getpgid(int(entry.name))!=process.pid:continue
                        for line in (entry/'status').read_text().splitlines():
                            if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
                    except (ProcessLookupError,PermissionError,FileNotFoundError):pass
                peak=max(peak,rss)
                elapsed=time.monotonic()-start
                if rss>536870912:reason='FORWARD_RSS_CAP'
                if ledger['combined_forward_wall_seconds']+elapsed>120:reason='COMBINED_FORWARD_WALL_CAP'
                if reason:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=3)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                    break
                time.sleep(.02)
            code=process.wait()
        elapsed=time.monotonic()-start;ledger['combined_forward_wall_seconds']+=elapsed
        ledger['peak_RSS_bytes']=max(ledger['peak_RSS_bytes'],peak)
        record=dict(job=job['job'],wall_seconds=elapsed,peak_RSS_bytes=peak,exit_code=code,resource_stop=reason)
        ledger['records'].append(record);save()
        assert code==0 and reason is None,(job['job'],record)
        result=json.loads((out/'RESULT.json').read_text())
        assert result['forward_calls']==1 and result['native_updates']==result['ROS_nodes']==0
        assert not result['captured_point_substitution']
        ledger['completed_calls']+=1
        if job['is_native_anchor']:ledger['anchor_checks'].append(anchor_check(job,out))
        save()
    ledger['status']='PASS_SIX_APPROVED_FORWARDS_CAPTURED_NO_POSTERIOR_UPDATE'
except Exception as error:
    ledger['status']='STOP_FIRST_TECHNICAL_OR_PARITY_FAILURE_NO_RETRY'
    ledger['error']=repr(error);ledger['traceback']=traceback.format_exc()
finally:
    save()
print(json.dumps(ledger,ensure_ascii=False,indent=2))
'''.replace('@@APPROVAL@@',repr(base64.b64encode(receipt.read_bytes()).decode())).replace('@@EXE@@',repr(provenance['executable_sha256'])).replace('@@LIBS@@',repr(provenance['LD_LIBRARY_PATH']))
compile(code,'approved_forward_remote','exec')
(WORK/'APPROVED_REMOTE_EXECUTION.py').write_text(code,encoding='utf-8')
result=json.loads(run(code,'APPROVED_SIX_EXECUTION',145))
(OUT/'M1_A_EXECUTION_LEDGER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
