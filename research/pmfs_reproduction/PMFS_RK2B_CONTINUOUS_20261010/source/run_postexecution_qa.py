"""Export and independent QA only, within remaining original stage budgets."""
from common_b import *
import psutil,shutil
begin=time.perf_counter();ledger=[]
prior=load(CORE/'LOCAL_RUNTIME_LEDGER.json');remaining_diagnostics=600-sum(r['wall_s'] for r in prior if r['stage'] in ['ALL_DIAGNOSTICS','INFORMATION_AUDIT','INDEPENDENT_VERIFIER'])
remaining_readout=900-load(CORE/'GENERATION_LEDGER.json')['response_wall_s']-next(r['wall_s'] for r in prior if r['stage']=='REFERENCE_CACHE')
for n in ['export_support_and_costs.py','verify_raw_support_b.py','make_report_b.py','run_postexecution_qa.py']:shutil.copyfile(WORK/n,CORE/'source'/n)
for script,label,args in [('export_support_and_costs.py','RAW_SUPPORT_AND_COVERAGE_EXPORT',[]),('verify_raw_support_b.py','INDEPENDENT_RAW_AND_TRAINING_QA',[str(CORE),str(RAW)]),('make_report_b.py','REPORT_EXPORT',[])]:
    start=time.perf_counter();peak=0;beat=0;cap=remaining_readout if label.startswith('INDEPENDENT_RAW') else remaining_diagnostics
    with (CORE/(label+'.stdout')).open('w',encoding='utf-8') as out,(CORE/(label+'.stderr')).open('w',encoding='utf-8') as err:
        p=subprocess.Popen([sys.executable,'-B','-X','utf8',str(WORK/script),*args],stdout=out,stderr=err,env=os.environ|dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        try:
            while p.poll() is None:
                rss=psutil.Process(p.pid).memory_info().rss;peak=max(peak,rss);elapsed=time.perf_counter()-start
                assert rss<=1073741824 and elapsed<=cap,'POSTEXECUTION_RESOURCE_LIMIT'
                assert load(CORE/'stage_status.json')['campaign_wall_s']+time.perf_counter()-begin<=5400
                if elapsed-beat>=30:print(json.dumps(dict(stage=label,wall_s=elapsed,RSS_bytes=rss)),flush=True);beat=elapsed
                time.sleep(.2)
        except Exception:
            p.kill();p.wait();raise
    r=dict(stage=label,wall_s=time.perf_counter()-start,sampled_peak_RSS_bytes=peak,exitcode=p.returncode);ledger.append(r);dump(CORE/'POSTEXECUTION_QA_LEDGER.json',ledger)
    assert p.returncode==0,(label,(CORE/(label+'.stderr')).read_text()[-2500:])
    if label.startswith('INDEPENDENT_RAW'):remaining_readout-=r['wall_s']
    else:remaining_diagnostics-=r['wall_s']
    print(json.dumps(r),flush=True)
dump(CORE/'POSTEXECUTION_CODE_SCOPE.json',dict(scope='Mechanical exports, reports and independent verification of preregistered physics/routing/metrics; no scientific endpoint, input, model or head changed',new_source_infer_calls=0,new_fit_calls=0,new_physics_calls=0,frozen_main_sources_unchanged=True,remaining_readout_budget_s=remaining_readout,remaining_diagnostic_budget_s=remaining_diagnostics))
