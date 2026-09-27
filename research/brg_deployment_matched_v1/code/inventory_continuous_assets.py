import os,json,pathlib,collections
home=pathlib.Path('/home/zyc')
selected=[p for p in home.iterdir() if p.is_dir() and any(k in p.name.lower() for k in ('jtd_e2','r0_','d1r','e2_','qa_pmfs','c0_5_real','vgr_data'))]
selected=[p/'OPEN_DISCOVERY' if p.name=='E2_CROSS_ENVIRONMENT_168_RUNS_20260925' else p for p in selected]
selected += [pathlib.Path('/mnt/hgfs/workspace/GADEN_files/scenarios')/h/'gas_simulations' for h in ('House01','House02')]
records=[]
for root in selected:
    if not root.exists(): continue
    dirs=[]; counts=collections.Counter(); examples={}; total=0
    for current,sub,files in os.walk(root):
        sub[:]=[s for s in sub if s not in ('.git','__pycache__','build','install','log','node_modules','wind','SEALED_DEV_HOLDOUT','SEALED_FINAL_HOUSE')]
        rel=pathlib.Path(current).relative_to(root)
        if len(rel.parts)>8: sub[:]=[]; continue
        if any('house03' in s.lower() for s in rel.parts): sub[:]=[]; continue
        kind=collections.Counter()
        for name in files:
            suffix=pathlib.Path(name).suffix or '<none>'
            counts[suffix]+=1; kind[suffix]+=1
            if len(examples.setdefault(suffix,[]))<4: examples[suffix].append(str(pathlib.Path(current)/name))
        if files and (len(files)>=20 or any(k in name.lower() for name in files for k in ('manifest','time_map','provenance'))):
            dirs.append({'directory':str(current),'count':len(files),'types':dict(kind),'sample':sorted(files)[:3],'last':sorted(files)[-3:]})
    records.append({'root':str(root),'counts':dict(counts),'examples':examples,'directories':dirs})
    print(json.dumps({k:records[-1][k] for k in ('root','counts')}),flush=True)
out=home/'brg_v1_continuous_asset_inventory_20260928.json'
out.write_text(json.dumps(records,indent=2),encoding='utf8')
print('INVENTORY',out)
for r in records:
    print(json.dumps({k:r[k] for k in ('root','counts')}))
    for d in r['directories']:
        if d['count']>=100 or any('time_map' in n.lower() for n in d['sample']+d['last']): print(json.dumps(d))
