#!/usr/bin/env python3
"""Independent review: inventory, native parity, repeated maps, moment mixture and ranks."""
import csv,hashlib,io,json,sys,zipfile
import numpy as np
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(sys.argv[1]) as z:
    for line in z.read('SHA256SUMS').decode().splitlines():
        h,path=line.split('  ',1);assert sha(z.read(path))==h,path
    load=lambda path:np.load(io.BytesIO(z.read(path)),allow_pickle=False)
    rows=lambda path:list(csv.DictReader(io.StringIO(z.read(path).decode())))
    bank=rows('forward/candidate_mark_bank.csv');result=json.loads(z.read('evaluation/D0_RESULT.json'))
    parity=json.loads(z.read('NATIVE_PARITY.json'))
    for record in parity['checks']:
        path=f"parity_{record['mode']}/maps/{record['candidate_id']}.f32"
        assert sha(z.read(path))==record['map_sha256']
    for p in z.namelist():
        if p.startswith('forward/') and p.endswith('.f32'):
            assert z.read(p)==z.read(p.replace('forward/','forward_repeat/',1)),p
        if p.startswith('evaluation/'):
            assert z.read(p)==z.read(p.replace('evaluation/','evaluation_repeat/',1)),p
    for e in range(3):
        probes=rows(f'inputs/env_{e}/probes.csv')
        for s in range(6):
            ps=[];us=[]
            for k in range(11):
              for rep in range(1,9):
                prefix=f'forward/env_{e}/source_{s}/state_{k}_replica_{rep}'
                ps.append(np.frombuffer(z.read(prefix+'.p.f32'),'<f4').astype(float));us.append(np.frombuffer(z.read(prefix+'.u.f32'),'<f4').astype(float))
            pm=np.mean(ps,axis=0);um=np.mean(us,axis=0)
            b=[r for r in bank if int(r['environment_index'])==e and int(r['source_index'])==s]
            for r,pr in zip(b,probes):
                ix=int(pr['cell_index']);p=float(r['presence_prob']);u=float(r['multiplicity_mean_unconditional']);m=float(r['multiplicity_mean_conditional'])
                assert p==pm[ix] and u==um[ix] and m==(u/p if p>0 else 0)
    # Recompute scores using the closed-form constrained-regression RSS.
    targets=load('protocol/JTD_E2_FRESH_TARGET_10x30.npy');refs=load('protocol/JTD_E2_REFERENCE_12x10x30.npy')
    candidate=rows('evaluation/CANDIDATE_SCORES_ALL.csv');details=rows('evaluation/TARGET_DETAIL_ALL.csv')
    def mark(obs,pred):
        obs=np.asarray(obs,dtype=np.float64);pred=np.asarray(pred,dtype=np.float64);hit=obs>0;n=int(hit.sum())
        if n<4:return 0.0
        yy=np.log(obs[hit]);xx=np.log(np.maximum(pred[hit],1e-9));yy=yy-yy.mean();xx=xx-xx.mean()
        vx=float(xx@xx);cov=float(xx@yy)
        rss=float(yy@yy)-(max(0.,cov)**2/vx if vx>1e-12 else 0.)
        return -.5*n*np.log(max(rss,1e-12)/n)
    independent=[];max_error=0.
    for e in range(3):
      sourcebank=[sorted([r for r in bank if int(r['environment_index'])==e and int(r['source_index'])==s],key=lambda r:int(r['probe_rank'])) for s in range(6)]
      prob=np.clip([[float(r['presence_prob']) for r in b] for b in sourcebank],1e-6,1-1e-6)
      mu=np.array([[float(r['multiplicity_mean_conditional']) for r in b] for b in sourcebank])
      count=(refs[e]>0).sum(axis=1);upper=np.divide(refs[e].sum(axis=1),count,out=np.zeros((6,10,30)),where=count>0)
      for s in range(6):
        for j in range(4):
          obs=targets[e,s,j];hit=obs>0;oc=np.sum(hit[None,:,:]*np.log(prob[:,None,:])+(1-hit[None,:,:])*np.log1p(-prob[:,None,:]),axis=(1,2))
          ml=np.array([mark(obs,np.broadcast_to(m,(10,30))) for m in mu]);ul=np.array([mark(obs,m) for m in upper])
          for k in range(6):
            record=next(r for r in candidate if int(r['environment_index'])==e and int(r['source_index'])==s and int(r['target_index'])==j and int(r['candidate_index'])==k)
            err=max(abs(float(record['occurrence_ll'])-oc[k]),abs(float(record['conditional_mark_ll'])-ml[k]),abs(float(record['upper_mark_ll'])-ul[k]));assert err<1e-7,err;max_error=max(max_error,err)
          expected=next(r for r in details if int(r['environment_index'])==e and int(r['source_index'])==s and int(r['target_index'])==j)
          rs={key:int(1+np.sum(v>v[s])) for key,v in [('B0',oc),('M',oc+ml),('U',oc+ul)]}
          for key,r in rs.items():assert r==int(float(expected['rank_'+key]))
          independent.append({'environment_index':e,'source_index':s,'target_index':j,**rs})
    print(json.dumps({'pass':True,'inventory_files':len(z.read('SHA256SUMS').decode().splitlines()),'native_maps_exact':174,'forward_maps_repeated':6336,'targets_independently_scored':len(independent),'maximum_closed_form_score_error':max_error,'decision':result['decision']},indent=2))
