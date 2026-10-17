"""Bounded native kernel build, parity and predeclared prediction controls. Run on Linux."""
from pathlib import Path
import json, subprocess, time, resource, os, sys, argparse, hashlib, csv
import numpy as np
R=Path(__file__).resolve().parents[1];W=R.parent
P=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
sys.path.insert(0,str(P.parent))
from native_analysis import analyze,Directory
plan=json.loads((R/'FROZEN_PLAN.json').read_text())
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
ledgerpath=R/'EXECUTION.json';ledger=json.loads(ledgerpath.read_text()) if ledgerpath.exists() else []
def run(cmd,tag,timeout=300):
    assert not (R/f'logs/{tag}.stdout').exists(),tag
    before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
    with (R/f'logs/{tag}.stdout').open('w') as out,(R/f'logs/{tag}.stderr').open('w') as err:
        p=subprocess.run(cmd,stdout=out,stderr=err,env=env,timeout=timeout)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    row=dict(command=cmd,tag=tag,exit_code=p.returncode,wall_s=time.monotonic()-start,
             cpu_user_s=after.ru_utime-before.ru_utime,cpu_system_s=after.ru_stime-before.ru_stime,
             cumulative_max_child_rss_kib=after.ru_maxrss)
    ledger.append(row);ledgerpath.write_text(json.dumps(ledger,indent=2))
    print(tag,p.returncode,round(row['wall_s'],3),flush=True)
    assert p.returncode==0,row
    assert sum(x['cpu_user_s']+x['cpu_system_s'] for x in ledger)<plan['maximum_child_cpu_s']

ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['parity','contrasts']);ap.add_argument('--attempt',type=int,default=1);a=ap.parse_args()
build=Path(os.environ.get('C4_BUILD_DIR','/tmp/c4a17_build'))
if a.stage=='parity':
    hashes={}
    for p in (R/'code').rglob('*'):
        if p.is_file():hashes[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
    build_manifest=f'lineage/BUILD_INPUT_SHA256_attempt{a.attempt}.json'
    (R/build_manifest).write_text(json.dumps(hashes,indent=2))
    for case in ['C4','C3']:
        e=next(x for x in json.loads((P/'CASE_INDEX.json').read_text())['cases'] if x['case']==case)
        if not (R/f'results/{case}_ORIGINAL_RECOMPUTATION.json').exists():
            start=time.monotonic();result=analyze(case,e['metadata'],Directory(P/e['native_path']))
            (R/f'results/{case}_ORIGINAL_RECOMPUTATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
            print('original_analyze',case,round(time.monotonic()-start,3),flush=True)
    run(['cmake','-S',str(R/'code'),'-B',str(build)],f'cmake_configure_attempt{a.attempt}')
    run(['cmake','--build',str(build),'-j2'],f'cmake_build_attempt{a.attempt}')
    parity=[]
    for item in plan['cases']:
        case,ep=item['case'],item['epoch'];key=f'{case}_update_{ep}'
        native=P/f'cases/{case}/native_execution/runtime/updates/update_{ep}'
        dest=R/f'results/parity_attempt{a.attempt}/{key}'
        run([str(build/'forward'),'parity',str(R/'inputs'/key),str(native),str(dest),'0',key],f'parity_{key}_attempt{a.attempt}')
        scores=list(csv.DictReader((dest/'scores.csv').open()))
        old={r['candidate_id']:r for r in csv.DictReader((native/'candidates.csv').open())}
        rawmax=blurmax=scoremax=0
        for row in scores:
            ident=row['id']
            for suffix in ['_unblurred.f32','.f32']:
                x=np.fromfile(native/'maps'/(ident+suffix),'<f4');y=np.fromfile(dest/'maps'/(ident+suffix),'<f4')
                delta=float(np.max(np.abs(x-y)))
                if suffix.startswith('_'):rawmax=max(rawmax,delta)
                else:blurmax=max(blurmax,delta)
            scoremax=max(scoremax,abs(float(row['logscore'])-float(old[ident]['logscore'])))
        parity.append(dict(case=case,epoch=ep,candidates=len(scores),max_raw_abs=rawmax,max_blur_abs=blurmax,max_logscore_abs=scoremax))
        (R/f'results/PARITY_attempt{a.attempt}.json').write_text(json.dumps(parity,indent=2))
        assert rawmax==0 and blurmax==0 and scoremax<1e-10,parity[-1]
    (R/'results/PARITY_PASS.json').write_text(json.dumps(dict(status='PASS_ALL_CAPTURED_RAW_BLURRED_MAPS',cases=parity,build_manifest=build_manifest),indent=2))
else:
    assert (R/'results/PARITY_PASS.json').exists()
    for name,h in json.loads((R/json.loads((R/'results/PARITY_PASS.json').read_text())['build_manifest']).read_text()).items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
    for item in plan['cases']:
        case,ep=item['case'],item['epoch'];key=f'{case}_update_{ep}'
        native=P/f'cases/{case}/native_execution/runtime/updates/update_{ep}'
        for seed in plan['prediction_rng_states']:
            for mode in ['region','coarse_equal','fine']:
                tag=f'{key}_{mode}_{seed}';dest=R/'results/predictions'/tag
                if (dest/'COMPLETE.json').exists():
                    print('reuse_complete',tag,flush=True);continue
                if dest.exists():
                    tag+='_dispatch_retry1';dest=R/'results/predictions'/tag
                    if (dest/'COMPLETE.json').exists():
                        print('reuse_complete',tag,flush=True);continue
                run([str(build/'forward'),mode,str(R/'inputs'/key),str(native),str(dest),str(seed),tag],tag)
                complete_files=list((R/'results/predictions').glob('*/COMPLETE.json'))+list((R/'results').glob('parity*/*/COMPLETE.json'))
                total_calls=sum(json.loads(p.read_text())['simulations'] for p in complete_files)
                assert total_calls<=plan['maximum_forward_calls'],total_calls
                # 0.75 GiB is an operational guard for concurrent host activity, not a scientific criterion.
                assert __import__('shutil').disk_usage(R).free>0.75*1024**3
    (R/'results/CONTRASTS_COMPLETE.json').write_text(json.dumps(dict(status='ALL_FROZEN_CONTROLS_COMPLETE',calls=total_calls)))
