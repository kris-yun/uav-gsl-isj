"""Supervise authorized serial campaign and all registered analyses, no retuning."""
from common_b import *
import psutil,signal,shutil

def footprint(p):return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
def main():
    reg=load(CORE/'experiment_registry.json');data=Path(reg['host_data_path']);ledger=[];start=time.perf_counter();beat=0
    def bounded(cmd,label,cap):
        nonlocal beat
        begin=time.perf_counter();peak=0;reason=None
        with (CORE/(label+'.stdout')).open('w',encoding='utf-8') as out,(CORE/(label+'.stderr')).open('w',encoding='utf-8') as err:
            process=subprocess.Popen(cmd,stdout=out,stderr=err,env=os.environ|dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            try:
                while process.poll() is None:
                    now=time.perf_counter();rss=0
                    try:
                        pp=psutil.Process(process.pid);rss=pp.memory_info().rss+sum(p.memory_info().rss for p in pp.children(recursive=True) if p.is_running())
                    except psutil.Error:pass
                    peak=max(peak,rss)
                    if rss>1073741824:raise RuntimeError('LOCAL_RSS_CAP_1GIB')
                    if now-begin>cap:raise RuntimeError(label+'_STAGE_TIME_CAP')
                    if now-start>5400:raise RuntimeError('ALL_SCIENCE_CAP')
                    if now-beat>30:
                        prog=dict(stage=label,stage_wall_s=now-begin,campaign_wall_s=now-start,RSS_bytes=rss,alive=True)
                        if label=='VM_SERIAL_GENERATION' and (data/'progress.json').exists():prog['VM']=load(data/'progress.json')
                        elif (CORE/'progress.json').exists():prog['stage_detail']=load(CORE/'progress.json')
                        print(json.dumps(prog),flush=True)
                        with (CORE/'CAMPAIGN_PROGRESS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(prog)+'\n')
                        dump(CORE/'CAMPAIGN_LIVE.json',prog);beat=now
                        disk=footprint(data)+footprint(CORE)+footprint(RAW)+footprint(WORK)
                        assert disk<=reg['new_disk_cap_bytes'],'COMBINED_NEW_DISK_CAP'
                        assert shutil.disk_usage(data).free>=4294967296 and shutil.disk_usage(CORE).free>=4294967296,'HOST_DISK_MARGIN'
                    time.sleep(.2)
            except Exception as error:
                reason=repr(error)
                try:process.send_signal(signal.CTRL_BREAK_EVENT);process.wait(timeout=10)
                except Exception:
                    try:
                        pp=psutil.Process(process.pid)
                        for c in pp.children(recursive=True):c.kill()
                        pp.kill()
                    except psutil.Error:pass
                raise
            finally:
                code=process.wait();r=dict(stage=label,wall_s=time.perf_counter()-begin,sampled_process_tree_peak_RSS_bytes=peak,exitcode=code,resource_stop=reason);ledger.append(r);dump(CORE/'LOCAL_RUNTIME_LEDGER.json',ledger)
        assert code==0,(label,code,(CORE/(label+'.stderr')).read_text(encoding='utf-8')[-2000:])
    try:
        bounded(SSH+['python3 '+REMOTE+'/generate_b.py'],'VM_SERIAL_GENERATION',2800)
        gen=load(data/'GENERATION_LEDGER.json');assert gen['status'].startswith('PASS') and len(gen['records'])==24
        dump(CORE/'GENERATION_LEDGER.json',gen)
        response_remaining=900-gen['response_wall_s'];assert response_remaining>0
        bounded([sys.executable,'-B',str(WORK/'build_reference_cache.py')],'REFERENCE_CACHE',response_remaining)
        for M in [2,4]:bounded([sys.executable,'-B',str(WORK/'fit_reference_models.py'),str(M)],f'MODEL_M{M}',900)
        budget=600
        for script,args,label in [('analyze_b.py',[],'ALL_DIAGNOSTICS'),('test_and_audit_b.py',['audit'],'INFORMATION_AUDIT'),('verify_b.py',[str(CORE)],'INDEPENDENT_VERIFIER')]:
            t=time.perf_counter();bounded([sys.executable,'-B',str(WORK/script),*args],label,budget);budget-=time.perf_counter()-t;assert budget>0
        dump(CORE/'stage_status.json',dict(status='COMPLETE_ALL_REGISTERED_BRANCHES',mode=24,stages=ledger,campaign_wall_s=time.perf_counter()-start,no_navigation=True,new_CFD=False,new_models_beyond_frozen_L=False,stopped_after_one_registered_campaign=True))
    except Exception as error:
        dump(CORE/'stage_status.json',dict(status='TECHNICAL_OR_RESOURCE_STOP',error=repr(error),stages=ledger,campaign_wall_s=time.perf_counter()-start,scientific_failure_not_used_as_stop=True));raise
    print(json.dumps(load(CORE/'stage_status.json'),indent=2),flush=True)
if __name__=='__main__':main()
