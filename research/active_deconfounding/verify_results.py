"""Independent artifact/geometry/probability audit; no gate tuning."""
import hashlib,json,pathlib,sys
import numpy as np
root=pathlib.Path(sys.argv[1]);designs=pathlib.Path(sys.argv[2]);dest=pathlib.Path(sys.argv[3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=[]
for c in sorted(root.glob('House??_seed?')):
    dpath=designs/(c.name+'.json');d=json.loads(dpath.read_text());s=json.loads((c/'selection.json').read_text());e=json.loads((c/'evaluation.json').read_text())
    width=d['geometry']['width'];free=set(map(int,d['partition']))
    checks={'truth_blind_selection':s['truth_read'] is False,'design_sha':s['design_sha256']==sha(dpath),
            'response_sha':s['response_sha256']==sha(c/'responses.f32'),
            'selection_frozen_before_evaluation':e['selection_sha256_before_truth']==sha(c/'selection.json')}
    for name,st in s['strategies'].items():
        pair=st['pair'];checks[name+'_in_frozen_design']=pair in d['pairs']
        checks[name+'_budget']=pair['duration_s']<=d['remaining_s']+1e-8
        ok=True
        for path in [pair['first_path'],pair['second_path']]:
            ok &= all(x in free for x in path)
            ok &= all(abs(u%width-v%width)+abs(u//width-v//width)==1 for u,v in zip(path,path[1:]))
        checks[name+'_grid_paths']=bool(ok)
        delta=np.array(e['strategies'][name]['pair_minus_single']);checks[name+'_separation_monotonic']=bool(np.all(delta>=-1e-12))
        checks[name+'_source_information_monotonic']=st['source_MI_nats']>=st['first_source_MI_nats']-1e-12
    # Recompute heldout minima directly on the four-outcome distribution,
    # independent of screen.py's affinity factorization.
    shape=json.loads((c/'COMPLETE.json').read_text());p=np.memmap(c/'responses.f32',dtype='<f4',mode='r',shape=(35,shape['sources'],shape['cells']))
    leaf=s['source_leaf_indices'];ids=[d['sources'][i]['id'] for i in leaf];true=ids.index(e['true_owner'])
    for name,st in s['strategies'].items():
        ca,cb=[x['cell_index'] for x in st['actions']]
        a=np.asarray(p[:,leaf,ca],float);b=np.asarray(p[:,leaf,cb],float)
        joint=np.stack([(1-a)*(1-b),a*(1-b),(1-a)*b,a*b],axis=-1)
        checks[name+'_normalization']=bool(np.max(np.abs(joint.sum(axis=-1)-1))<1e-12)
        values=[]
        for n in range(27,35):
            affinity=np.sqrt(joint[:27]*joint[n,true]).sum(axis=-1)
            affinity[:,true]=-np.inf
            values.append(float(np.clip(1-affinity.max(),0,1)))
        checks[name+'_bruteforce_separation']=bool(np.allclose(values,e['strategies'][name]['heldout_min_separation'],atol=1e-12,rtol=0))
    audit.append({'case':c.name,'checks':checks,'pass':all(checks.values())})
assert len(audit)==6
payload={'cases':audit,'all_pass':all(x['pass'] for x in audit),'point_robot_only':True,'native_response_model_external_validation':False}
dest.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps({'all_pass':payload['all_pass'],'cases':len(audit)}));assert payload['all_pass']
