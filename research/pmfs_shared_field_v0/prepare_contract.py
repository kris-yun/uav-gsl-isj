"""Verify paired CENTRAL run identities and sign exact development contract."""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
import numpy as np

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,x):path.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
a=p.parse_args();a.root=a.root.resolve();e=a.root/'evidence/pmfs_shared_field_v0';e.mkdir(exist_ok=True)
base=a.root/'evidence/source_probe_crossed_audit_v0'
up=a.root/'research/pmfs_shared_field_v0/upstream'
manifest=json.loads((up/'SHA256_MANIFEST.json').read_text())
assert all(sha(up/n)==h for n,h in manifest.items())
compat=json.loads((base/'SPX_G0_A0_COMPATIBILITY.json').read_text())
paths=[]
for layout in ('P_G1A','P_E2'):
    path=base/f'SPX_G0_CENTRAL_{layout}_10x30.npy';d=compat['crossed_tensors'][f'CENTRAL_{layout}']
    assert sha(path)==d['sha256']
    x=np.load(path,allow_pickle=False)
    assert x.shape==(168,16,10,30) and np.isfinite(x).all() and (x>=0).all()
    paths.append({'layout':layout,'path':str(path),'sha256':sha(path),'shape':list(x.shape)})
panel=list(csv.DictReader((a.assets/'central_panel.tsv').open(),delimiter='\t'))
runs=list(csv.DictReader((a.assets/'central_manifest.tsv').open(),delimiter='\t'))
audit=json.loads((base/'SPX_G0_ASSET_AUDIT.json').read_text())
cube_lookup={(v['source_index'],v['replicate_index']):v for v in audit['cube_inventory'] if v['panel']=='CENTRAL'}
assert len(panel)==168 and len(runs)==2688 and len(cube_lookup)==2688
keyset=set();out=[]
for run in runs:
    s,r=int(run['panel_index']),int(run['replicate'])-1
    assert (s,r) not in keyset;keyset.add((s,r))
    source=panel[s];cube=cube_lookup[s,r]
    assert run['source_id']==source['source_id']==cube['source_id']
    seed=int(run['rng_seed']);assert seed==2026105000+16*s+r+1
    assert cube['sha256']==run['concentration_sha256']
    assert f'rep_{r+1:02d}_seed_{seed}' in cube['path']
    out.append({'source_index':s,'source_id':source['source_id'],'replicate_index':r,'seed':seed,
                'run_id':f"{source['source_id']}/rep_{r+1:02d}_seed_{seed}",
                'cube_sha256':cube['sha256'],'P_G1A_run_id':cube['path'],'P_E2_run_id':cube['path']})
with (e/'RUN_ID_JOIN.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
for name in ('central_panel.tsv','central_manifest.tsv','gate1a_contract.json','e1_probe_contracts.tsv'):
    shutil.copyfile(a.assets/name,e/name)
folds=[[f,f+4,f+8,f+12] for f in range(4)]
contract={
 'status':'SIGNED_BEFORE_OUTER_SCORING','authorization':'latest user pasted method request; package development policy adopted without scientific formula changes',
 'input_zip_sha256':'efddf8c726d5fb358a4d3e0cc074f3360e47907b99c9da2bef69507a85302a68',
 'scope':{'house':'House02','wind':'3,5-1_slow','sources':168,'runs_per_source':16,'protocols':60,
          'reads_per_task':2,'snapshot_indices':[100,550],'new_plumes':0,'sealed_data_read':False,
          'classification':'OPEN method development CV, not fresh confirmation'},
 'inputs':paths,'run_join_sha256':sha(e/'RUN_ID_JOIN.csv'),
 'source_panel_sha256':sha(e/'central_panel.tsv'),
 'folds':folds,'inner_folds':'sorted outer-reference positions modulo3, 8reference/4validation',
 'encoding':{'positive_thresholds':'pooled training-only 1/3 and2/3 quantiles across sources/protocols/times',
             'zero':'exact ppm=0','ties':'unique thresholds merge identical intervals; one alphabet shared by all arms',
             'two_time_symbol':'first_bin*number_bins+last_bin','raw_ppm_retained':True},
 'channel':{'onehot_scale':'R/(R+1)','uniform_scale':'1/(R+1)','uniform_symbols':'all current-fold alphabet symbols',
            'interpretation':'common total Dirichlet pseudocount1; statistical smoothing, not sensor noise or posterior floor'},
 'prior':{'source':'uniform168 microcells','protocol':'uniform60 alternative tasks'},
 'selection':{'rho_grid':[0,.05,.15,.35],'temperature_grid':[.5,1,2,4],
              'shared_and_independent':'independent model-wide selection, same inner CV/mean log score policy',
              'tie_break':'smallest rho; temperature nearest1 then smaller T, within1e-12 mean nats',
              'shuffle':'same selected shared rho; no separate hyperparameter search'},
 'identity_ablation':{'policy':'protocol0 unchanged; for each source/protocol>0 sort reference run IDs by domain-separated SHA256',
                      'domain':'PMFS_SHARED_FIELD_IDENTITY_ABLATION_V0|outer_fold|source_id|protocol|run_id',
                      'reads_concentration_to_set_permutation':False,'per_protocol_marginal_invariance_required':True},
 'models':['NOMINAL','INDEPENDENT_DRO','TEMPERATURE','SHARED_FIELD','SHUFFLED_SHARED'],
 'extra_background_baseline':'none; no Gaussian/JTD/PMFS proxy fitted',
 'solver':{'objective':'maximize conditional entropy under per-source KL weights; same as supplied SLSQP prototype',
           'implementation':'sparse-channel entropic mirror ascent with KL-Bregman projection and independent KL dual risk certificate',
           'saddle_gap_max_nats':2e-6,'constraint_violation_max':2e-8,
           'independent_protocol_max_gap_nats':2e-6,'max_iterations':4000,'max_wall_seconds_per_fit':900,
           'no_posterior_floor':True,'failure':'implementation blocked, never scientific STOP'},
 'endpoint':'per-source mean over16runs and60protocols of paired log2 truth probability gain',
 'bootstrap':{'unit':'whole source, all runs/protocols/folds retained','replicates':10000,'seed':2026092607,
              'interpretation':'OPEN crossfit source-panel sensitivity interval, not fresh/generalization coverage'},
 'retention_rule':{'primary':'shared gains over nominal/independent/temperature each>0 and source-panel95% lower>0',
                   'ablation':'shared gain over identity-shuffled comparator>0 and95% lower>0',
                   'effect_threshold_bits':0,'effect_size_and_cost_reported':'no claim that an arbitrarily tiny positive gain establishes a main innovation',
                   'secondary_metrics':'Brier/rank/distance/tails descriptive, cannot rescue primary comparison',
                   'positive_with_ordinary_baseline_loss':'stop shared-field main-innovation claim',
                   'result_names':['DEVELOPMENT_RETAIN_SHARED_FIELD_CANDIDATE','DEVELOPMENT_STOP_NO_INCREMENT_BEYOND_CONTROLS','DEVELOPMENT_IMPLEMENTATION_BLOCKED']},
 'rank':'deterministic ties by ascending candidate index, no optimistic tie ranks',
 'stop_after_results':True}
write(e/'NUMERICAL_CONTRACT.json',contract)
print('CONTRACT_SIGNED; paired run join',len(out))
