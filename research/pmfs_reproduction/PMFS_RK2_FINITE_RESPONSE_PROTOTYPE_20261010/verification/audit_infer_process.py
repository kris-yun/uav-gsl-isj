"""Isolated RK2 scalar-inference process audit; no fitting or physical query.

Parent copies only four frozen forecast NPZ, four scalar observation JSON,
and the frozen inference source into a new audit directory. One -I -B child
loads them under a Python audit hook; it never receives the parent bundle,
training state, geometry, raw readers, hidden particle tables, or truth map.
This is observable Python-event and dependency isolation evidence, not a
claim that sys.addaudithook instruments every native-library system call.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

MODEL_IDS=('F','U_query','S_query','L')
OBS_IDS=('O00','O01','O02','O03')

def canonical_path(path):
    return os.path.normcase(os.path.realpath(os.fspath(path)))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def comparison(a,b,scope='root'):
    """Structural and finite-number comparison, independent of JSON order."""
    if isinstance(a,dict) and isinstance(b,dict):
        if set(a)!=set(b):raise AssertionError((scope,'key mismatch',set(a)^set(b)))
        return max([comparison(a[k],b[k],scope+'.'+k) for k in a]+[0.0])
    if isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):raise AssertionError((scope,'length mismatch'))
        return max([comparison(x,y,f'{scope}[{i}]') for i,(x,y) in enumerate(zip(a,b))]+[0.0])
    if type(a) in (int,float) and type(b) in (int,float):
        if not math.isfinite(a) or not math.isfinite(b):raise AssertionError((scope,'nonfinite'))
        difference=abs(a-b)
        if difference>1e-15:raise AssertionError((scope,a,b,difference))
        return difference
    if a!=b:raise AssertionError((scope,a,b))
    return 0.0

def child(config):
    """No child subprocess/socket and no output writes; JSON goes to stdout."""
    import importlib.util
    data_files={canonical_path(v):k for k,v in config['data_files'].items()}
    source=canonical_path(config['infer_source'])
    logs=[];blocked=[];qa_blocked=[];phase='software_QA'
    prefix=Path(sys.base_prefix)
    stdlib=canonical_path(prefix/'Lib')
    site_packages=canonical_path(prefix/'Lib/site-packages')
    allowed_dependencies=[canonical_path(prefix/'DLLs'),canonical_path(prefix/'Library/bin'),
                         canonical_path(prefix/'Lib/site-packages/numpy'),canonical_path(prefix/'Lib/site-packages/numpy.libs'),
                         canonical_path(prefix/'Lib/site-packages/mkl')]
    forbidden_terms=('evaluation_only','parent_m2m3','reference_contribution_cache','runtime_models','/models/','\\models\\',
                     'rk2_models','verify_raw_receiver_queries','train_counts','filaments','truth_mapping')
    def under(path,directory):
        return path==directory or path.startswith(directory+os.sep)
    def allowed_dependency(path):
        return (under(path,stdlib) and not under(path,site_packages)) or any(under(path,p) for p in allowed_dependencies)
    def audit(event,args):
        if event.startswith('socket.') or event.startswith('subprocess.') or event in ('os.system','os.posix_spawn','os.posix_spawnp'):
            entry=dict(event=event,path=None,phase=phase,reason='network/process creation forbidden')
            (qa_blocked if phase=='software_QA' else blocked).append(entry)
            raise PermissionError(entry['reason'])
        if event!='open':return
        supplied=args[0]
        if isinstance(supplied,int):
            if supplied in (0,1,2):return
            entry=dict(event=event,path=str(supplied),phase=phase,reason='nonstandard file descriptor open forbidden')
            (qa_blocked if phase=='software_QA' else blocked).append(entry)
            raise PermissionError(entry['reason'])
        path=canonical_path(supplied);mode=args[1];flags=args[2]
        writing=(isinstance(mode,str) and any(v in mode for v in ('w','a','+','x'))) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing:
            reason='child is read-only'
        elif path in data_files:
            logs.append(dict(event=event,path=path,classification='allowed_scalar_data',input_name=data_files[path],phase=phase));return
        elif path==source:
            logs.append(dict(event=event,path=path,classification='allowed_infer_source',phase=phase));return
        elif allowed_dependency(path) and not any(t in path.lower() for t in forbidden_terms):
            logs.append(dict(event=event,path=path,classification='stdlib_or_numpy_dependency',phase=phase));return
        else:reason='path not in exact scalar-data/source/dependency whitelist'
        entry=dict(event=event,path=path,phase=phase,reason=reason)
        (qa_blocked if phase=='software_QA' else blocked).append(entry)
        raise PermissionError(reason)
    sys.addaudithook(audit)
    # This forbidden file exists in the isolated fixture. The event hook must
    # block the attempt before any bytes are returned. It is never a protected
    # historical file and its path is not among the eight allowed data files.
    try:
        with open(config['forbidden_QA_file'],'rb') as f:f.read()
    except PermissionError:
        illegal_read_QA='PASS_BLOCKED_BEFORE_READ'
    else:raise AssertionError('audit hook allowed artificial forbidden read')
    phase='actual_inference'
    spec=importlib.util.spec_from_file_location('rk2_isolated_scalar_infer',config['infer_source'])
    inference=importlib.util.module_from_spec(spec);sys.modules[spec.name]=inference
    # Read the sole allowed source directly; avoid probing a nonexistent local
    # __pycache__ file during SourceFileLoader's normal import lookup.
    code=Path(config['infer_source']).read_bytes()
    exec(compile(code,config['infer_source'],'exec'),inference.__dict__)
    results=[];permutation_checks=[]
    for model in MODEL_IDS:
        fp=config['data_files']['forecast_'+model]
        forecasts,plan=inference.load_forecast_npz(fp,model)
        inverse={f'UnlabelledCandidate{i:03d}':c.candidate_id for i,c in enumerate(reversed(forecasts.candidates))}
        renamed=inference.ForecastSet(model,tuple(inference.ForecastCandidate(newid,c.reference_response_ppm,c.physical_source_xyz)
            for newid,c in zip(inverse,reversed(forecasts.candidates))))
        for observation_id in OBS_IDS:
            op=config['data_files']['observation_'+observation_id]
            baseline=inference.infer_files(fp,op,model)
            results.append(dict(model_id=model,observation_id=observation_id,result=baseline))
            observed=inference.load_observation_json(op)
            permuted=inference.infer(renamed,observed)
            left={r['candidate_id']:r for r in baseline['candidates']}
            right={inverse[r['candidate_id']]:dict(r,candidate_id=inverse[r['candidate_id']]) for r in permuted['candidates']}
            difference=comparison(left,right,model+'.'+observation_id+'.candidate_permutation')
            assert set(baseline['top1_candidate_ids'])=={inverse[c] for c in permuted['top1_candidate_ids']}
            permutation_checks.append(dict(model_id=model,observation_id=observation_id,status='PASS',maximum_number_difference=difference,
                probability_sum=math.fsum(c['source_probability'] for c in baseline['candidates'])))
    accessed={r['path'] for r in logs if r['classification']=='allowed_scalar_data'}
    assert accessed==set(data_files),(accessed^set(data_files))
    assert len(results)==16 and len(permutation_checks)==16 and not blocked
    result=dict(status='PASS_ISOLATED_INFERENCE_EIGHT_DATA_FILES',results=results,permutation_checks=permutation_checks,
        illegal_read_software_QA=illegal_read_QA,software_QA_blocked_attempts=qa_blocked,actual_blocked_attempts=blocked,
        actual_open_events=logs,allowed_data_unique_paths=sorted(accessed),allowed_data_unique_count=len(accessed),
        inference_cases=16,child_no_hidden_or_truth_inputs=True,child_can_only_read_frozen_scalar_forecasts_observations=True,
        no_producer_no_physical_reader_no_model_fit=True,isolated_flags=sys.flags.isolated,dont_write_bytecode=sys.dont_write_bytecode,
        audit_scope='Python audit open/process/socket events after startup imports; does not trace uninstrumented native I/O.')
    print(json.dumps(result,ensure_ascii=False,separators=(',',':')))

def parent(package,out,python):
    import shutil
    import subprocess
    package=Path(package).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    required=[package/'source/rk2_infer.py',package/'SOURCE_TASK_PREDICTIONS_BLIND.json']
    required += [package/'candidate_forecasts'/f'{model}.npz' for model in MODEL_IDS]
    required += [package/'observable_inputs'/f'{oid}.json' for oid in OBS_IDS]
    for p in required:
        if not p.is_file():raise FileNotFoundError(p)
    isolated=out/'isolated_scalar_inputs';isolated.mkdir()
    source=isolated/'rk2_infer.py';shutil.copyfile(package/'source/rk2_infer.py',source)
    data_files={};copied_hashes={}
    for model in MODEL_IDS:
        original=package/'candidate_forecasts'/f'{model}.npz';target=isolated/f'forecast_{model}.npz';shutil.copyfile(original,target)
        assert sha(original)==sha(target);data_files['forecast_'+model]=str(target);copied_hashes[str(original)]=sha(original)
    for oid in OBS_IDS:
        original=package/'observable_inputs'/f'{oid}.json';target=isolated/f'observation_{oid}.json';shutil.copyfile(original,target)
        assert sha(original)==sha(target);data_files['observation_'+oid]=str(target);copied_hashes[str(original)]=sha(original)
    forbidden=isolated/'forbidden_read_software_QA.json';forbidden.write_text('{"forbidden_fixture":true}',encoding='utf-8')
    cfg=dict(data_files=data_files,infer_source=str(source),forbidden_QA_file=str(forbidden))
    command=[python,'-I','-B',str(Path(__file__).resolve()),'--child-config',json.dumps(cfg,separators=(',',':'))]
    start=time.perf_counter()
    completed=subprocess.run(command,cwd=isolated,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',timeout=60)
    (out/'ISOLATED_CHILD_STDOUT.json').write_text(completed.stdout,encoding='utf-8')
    (out/'ISOLATED_CHILD_STDERR.txt').write_text(completed.stderr,encoding='utf-8')
    if completed.returncode!=0:raise AssertionError(('isolated inference child failed',completed.returncode,completed.stderr))
    actual=json.loads(completed.stdout)
    expected=json.loads((package/'SOURCE_TASK_PREDICTIONS_BLIND.json').read_text(encoding='utf-8'))
    a={(r['model_id'],r['observation_id']):r['result'] for r in actual['results']}
    b={(r['model_id'],r['observation_id']):r['result'] for r in expected}
    assert set(a)==set(b) and len(a)==16
    maxdiff=max(comparison(a[k],b[k],'.'.join(k)) for k in a)
    frozen_hashes={str(p):sha(p) for p in required}
    record=dict(status='PASS_ISOLATED_SOURCE_BLIND_INFER_PROCESS',source_package=str(package),output=str(out),
        child_command_flags=['-I','-B'],child_count=1,child_exit_code=completed.returncode,
        wall_seconds=time.perf_counter()-start,inference_cases=16,source_score_recomputation_max_abs_difference=maxdiff,
        exact_data_whitelist_unique_count=actual['allowed_data_unique_count'],actual_illegal_reads=0,
        actual_blocked_attempts=actual['actual_blocked_attempts'],software_QA_blocked_attempts=actual['software_QA_blocked_attempts'],
        candidate_rename_permutation_cases=actual['permutation_checks'],
        frozen_input_SHA256=frozen_hashes,copied_data_SHA256=copied_hashes,infer_source_SHA256=sha(source),
        child_hidden_truth_files_not_present=True,child_training_and_parent_paths_not_provided=True,
        actual_open_trace_file='ISOLATED_CHILD_STDOUT.json',
        scope_limit='The parent copies/compares frozen results. Child only reads scalar files and infer source plus stdlib/numpy; audit does not instrument every native system call.')
    (out/'INFER_PROCESS_AUDIT_RESULT.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ['candidate_rename_permutation_cases','frozen_input_SHA256','copied_data_SHA256']},ensure_ascii=False,indent=2))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path);parser.add_argument('--out',type=Path)
    parser.add_argument('--python',default=sys.executable);parser.add_argument('--child-config')
    args=parser.parse_args()
    if args.child_config:child(json.loads(args.child_config))
    else:
        if args.package is None or args.out is None:parser.error('--package and --out are required')
        parent(args.package,args.out,args.python)
if __name__=='__main__':main()
