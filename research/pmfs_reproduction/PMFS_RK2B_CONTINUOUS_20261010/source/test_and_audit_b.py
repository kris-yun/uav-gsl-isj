"""Formula/shape tests before physics; actual whitelisted process audits after fit."""
from common_b import *
import numpy as np, tempfile, shutil
from rk2b_infer import infer,future

def software():
    x=np.zeros((3,2,50),np.float32);x[1]=1;x[2,0]=1;y=np.ones(50,np.float32)
    r=infer(x,y);assert r['top1'].tolist()==[1]
    assert np.allclose(r['event_probability'][:,0],[1/6,5/6,1/2])
    assert np.allclose(r['scores'],np.log([1/6,5/6,1/2]))
    c=infer(x,y,'H1',1);assert c['top1'].tolist()==[1] and c['CRPS'][1].max()==0
    xx=np.concatenate([x,x],axis=1);assert np.allclose(infer(xx,y,'H1',1)['scores'],c['scores'])
    p=np.array([2,0,1]);assert np.allclose(infer(x[p],y)['prob'],r['prob'][p])
    a=infer(x,y,blocks=np.arange(25));y2=y.copy();y2[25:]=0;assert np.array_equal(a['prob'],infer(x,y2,blocks=np.arange(25))['prob'])
    assert not np.array_equal(future(x,y,a['prob'])['predicted_hit_probability'],np.zeros(25))
    bad=0
    for inp in [np.zeros((3,1,50)),np.zeros((3,2,49)),np.full((3,2,50),np.nan),np.full((3,2,50),-1)]:
        try:infer(inp,y)
        except AssertionError:bad+=1
    assert bad==4
    dump(CORE/'PREPHYSICAL_SOFTWARE_TESTS.json',dict(status='PASS',tests=['H0 Jeffreys/manual log','continuous CRPS zero and repeated ensemble','candidate permutation','future exclusion from prefix25','four illegal tensor shapes/values'],physical_calls=0))

def audit():
    reg=load(CORE/'experiment_registry.json');records=[]
    for M in [2,4] if reg['mode']==24 else [2]:
        status=load(CORE/f'M{M}/MODEL_STATUS.json');scale=load(CORE/f'M{M}/HEAD_SCALE_FROZEN.json')['H1_scale']
        for method in status['methods']:
            with np.load(CORE/f'M{M}/forecasts/{method}.npz',allow_pickle=False) as z:x=z['reference_response_ppm'][:,:M];ids=z['candidate_ids']
            for head in ['H0','H1']:
                with np.load(CORE/'scalar_observations/O00.npz',allow_pickle=False) as z:y=z['observed_ppm']
                with tempfile.TemporaryDirectory(prefix='rk2b_whitelist_') as tmp:
                    root=Path(tmp);shutil.copyfile(WORK/'rk2b_infer.py',root/'kernel.py');shutil.copyfile(WORK/'isolated_infer.py',root/'isolated_infer.py')
                    forbidden=WORK/'FORBIDDEN_HIDDEN_FIXTURE_DO_NOT_READ.txt';assert not forbidden.exists();forbidden.write_text('test particles/truth/Q forbidden',encoding='utf-8')
                    def run(values,labels):
                        np.savez(root/'forecast.npz',predicted_ppm=values,candidate_ids=labels);np.savez(root/'observation.npz',observed_ppm=y)
                        dump(root/'config.json',dict(head=head,scale=scale,forbidden_path=str(forbidden)))
                        p=subprocess.run([sys.executable,'-I','-B',str(root/'isolated_infer.py')],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=30);assert p.returncode==0,p.stderr
                        return json.loads(p.stdout)
                    try:
                        a=run(x,ids);forbidden.write_text('replaced hidden content and no truth map',encoding='utf-8');b=run(x,ids);forbidden.unlink();c=run(x,ids)
                        permutation=np.array([2,0,1]);d=run(x[permutation],np.array(['anonymous_C','anonymous_A','anonymous_B']))
                        assert a['result']==b['result']==c['result'];assert np.allclose(d['result']['prob'],np.array(a['result']['prob'])[permutation]);assert a['denied_illegal_read']
                        expected=infer(x,y,head,scale);assert np.allclose(expected['prob'],a['result']['prob'])
                        records.append(dict(M=M,method=method,head=head,replaced_hidden_invariant=True,removed_hidden_invariant=True,renamed_and_permuted_equivariant=True,truth_map_absent=True,explicit_illegal_read_blocked=True,actual_child_processes=4,opened_paths=a['opened_paths'],audit_scope='Python open events in fresh subprocess; not a kernel-system-call sandbox'))
                    finally:
                        if forbidden.exists():forbidden.unlink()
    dump(CORE/'ACTUAL_INFORMATION_ISOLATION_AUDIT.json',dict(status='PASS_SCALAR_ONLY_PROCESS_INVARIANCE',records=records,child_processes=sum(r['actual_child_processes'] for r in records),all_methods_and_heads_tested=True,test_hidden_physical_assets_mounted_in_infer=False))
if __name__=='__main__':software() if sys.argv[1]=='software' else audit()
