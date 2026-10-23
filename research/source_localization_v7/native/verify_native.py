"""Independent post-run QA; no training, tuning or performance re-runs."""
from pathlib import Path
import csv,ctypes as ct,json,subprocess,sys,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gsl_discrimination.data import SynchronousBlock
from gsl_discrimination.m1_opponent.raw_joint import load_observation_model
from gsl_discrimination.navigation.bridge import JsonLineBackend
from recover_assets import ROOT,OUT,PROTO,sha,write

def main():
    freeze=json.loads((OUT/'MODEL_FREEZE.json').read_text())
    model_hash_pass=all(sha(OUT/f)==h for f,h in freeze['models'].items())
    code_hash_pass=all(sha(ROOT/f)==h for f,h in freeze['code_sha256'].items())
    assert model_hash_pass and code_hash_pass
    lib=ct.CDLL(str((ROOT/'native/native_query.dll').resolve()))
    f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    i32=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
    lib.m1_features.argtypes=[f64,f64,ct.c_int,f64,ct.c_int,f64,f64];lib.m1_features.restype=ct.c_int
    lib.m1_symbol.argtypes=[ct.c_double,f64,ct.c_double,f64,i32,ct.c_int];lib.m1_symbol.restype=ct.c_int
    lib.raw_joint_symbol.argtypes=[f64,ct.c_int,f64,ct.c_int,ct.c_double];lib.raw_joint_symbol.restype=ct.c_int
    lib.categorical_posterior.argtypes=[f64,ct.c_int,ct.c_int,ct.c_int,f64];lib.categorical_posterior.restype=ct.c_int
    r1=json.loads((OUT/'R1_EXTRACTION_RESULT.json').read_text());proto=json.loads(PROTO.read_text())
    models={v:load_observation_model(OUT/'models'/v) for v in proto['variants']}
    checks=[];features_error=0.;posterior_error=0.
    for record in r1['blocks']:
        if record['split']!='dev':continue
        b=SynchronousBlock.load_npz(OUT/record['path']);raw=np.ascontiguousarray(b.values,dtype=np.float64)
        times=np.ascontiguousarray(b.times_s,dtype=np.float64)
        for name,m in models.items():
            expected=int(m.encode(0,raw,times,m.contract))
            if name=='raw_joint':
                symbol=lib.raw_joint_symbol(raw,raw.size,np.ascontiguousarray(m.centers[0]),m.channel.shape[-1],float(m.scales[0]))
                feature_diff=0.
            else:
                specs=np.array([[s.lag_s,s.decay_s,s.inhibition,s.bias,0 if s.kind=='gradient' else 1] for s in m.bank.specs],dtype=np.float64)
                e=np.zeros(1);h=np.zeros(len(specs))
                assert lib.m1_features(raw,times,len(times),specs,len(specs),e,h)==0
                pe,ph=m.bank.extract(raw,times,m.contract)
                feature_diff=max(abs(float(pe)-e[0]),float(np.max(np.abs(ph-h))))
                features_error=max(features_error,feature_diff)
                selected=np.array(m.selection[0],dtype=np.int32)
                symbol=lib.m1_symbol(e[0],h,float(m.even_thresholds[0]),np.ascontiguousarray(m.odd_thresholds[0]),selected,len(selected))
            assert symbol==expected
            table=np.ascontiguousarray(m.channel.probabilities[0,:,0,:])
            post=np.zeros(2)
            assert lib.categorical_posterior(table,2,m.channel.shape[-1],symbol,post)==0
            ref=table[:,symbol]/table[:,symbol].sum();error=float(np.max(np.abs(post-ref)))
            posterior_error=max(posterior_error,error)
            checks.append({'world_id':record['run_id'],'method':name,'symbol':symbol,
                           'python_symbol':expected,'feature_max_error':feature_diff,'posterior_max_error':error})
    assert features_error<1e-12 and posterior_error<1e-14
    write('CPP_INFERENCE_QA.json',{'status':'PASS','blocks_times_variants':len(checks),
          'max_feature_error':features_error,'max_posterior_error':posterior_error,'checks':checks,
          'source_cpp_sha256':sha(ROOT/'native/native_query.cpp'),'library_sha256':sha(ROOT/'native/native_query.dll'),
          'scope':'actual compiled C++17 readout and M1/raw-joint inference, not native ROS controller'})
    # Actual process round-trip against the recovered world. Not the analytic
    # demonstration server. Refuse a second consumption and an unknown action.
    run=proto['authorized_runs'][0]
    bridge=JsonLineBackend([sys.executable,str(ROOT/'native/gaden_executor/server.py'),'--run',run,
           '--output',str(OUT/'component_probe')],OUT/'native_component.stderr.log',timeout_s=20)
    try:
        description=bridge.call('describe')
        assert description['schema']=='gsl-native-fixed-probe-component-1'
        assert not description['motion_controller_qualified']
        actual=bridge.call('execute',action=0)
        block=SynchronousBlock.load_npz(actual['block_path'])
        reference=SynchronousBlock.load_npz(OUT/'blocks'/(run+'.npz'))
        assert np.array_equal(block.values,reference.values)
        assert np.array_equal(block.local_wind_mps,reference.local_wind_mps)
        try:bridge.call('execute',action=0)
        except RuntimeError as e:duplicate=str(e)
        else:raise AssertionError('duplicate accepted')
        try:bridge.call('execute',action=1)
        except RuntimeError as e:invalid=str(e)
        else:raise AssertionError('unknown action accepted')
    finally:bridge.close()
    write('NATIVE_COMPONENT_QA.json',{'status':'PASS_READONLY_FIXED_PROBE_COMPONENT',
          'description':description,'actual_result':actual,'same_values_and_wind_as_extraction':True,
          'duplicate_rejected':duplicate,'invalid_action_rejected':invalid,
          'full_gsl_action_bridge_or_UAV_qualified':False})
    # Independent CSV arithmetic and paired classification outcomes.
    with (OUT/'PER_WORLD_M1.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    arithmetic=[]
    for method in sorted({r['method'] for r in rows}):
        rr=[r for r in rows if r['method']==method]
        arithmetic.append({'method':method,'mean_MAP_error_m':sum(float(r['map_error_m']) for r in rr)/len(rr),
                           'strict_correct':sum(int(r['top1'])==1 and r['top1_tie']=='False' for r in rr),
                           'ties':sum(r['top1_tie']=='True' for r in rr)})
    original=json.loads((OUT/'R2_RESULT.json').read_text())
    for r in arithmetic:
        ref=next(x for x in original['summaries'] if x['method']==r['method'])
        assert abs(r['mean_MAP_error_m']-ref['mean_MAP_error_m'])<1e-12
        assert r['strict_correct']==ref['strict_correct'] and r['ties']==ref['ties']
    write('INDEPENDENT_QA.json',{'status':'PASS_WITH_DECLARED_SCIENTIFIC_LIMITS',
          'frozen_models_unchanged':model_hash_pass,'frozen_fit_code_unchanged':code_hash_pass,
          'cpp_inference_pass':True,'native_process_component_pass':True,'csv_arithmetic_pass':True,
          'seal_or_H03_observations_read':False,'new_propagation':0,'new_ROS':0,'summary':arithmetic})
    print('QA_PASS',len(checks),features_error,posterior_error)

if __name__=='__main__':main()
