"""Freeze controls and runtime before new gas generation; H fields are diagnostics."""
import subprocess, numpy as np,pandas as pd
from common import *
subprocess.run(['ssh',HOST,'mkdir -p '+REMOTE],check=True)
binary=subprocess.check_output(['ssh',HOST,'sha256sum '+ADAPTER+' '+LIB],text=True)
assert binary.splitlines()[0].split()[0]=='b2670ae13e933e79004b565ae890b5d99d62cb980e5820bdd563929d4b6b82ec'
assert binary.splitlines()[1].split()[0]=='0b6a2160917a1e8791c1980635b0969c40794b96d591abba31d743758fc5f048'
(OUT/'runtime_binary_hashes_before.txt').write_text(binary)
path=pd.read_csv(OLD/'fixed_path_contract.csv').query('z==10')
indices=np.floor((path.x.to_numpy()+100)/5).astype(int)
gen=HERE/'wind';gen.mkdir(exist_ok=True)
original={name:pd.read_csv(EXP/f'generated_project/wind_simulations/{name}/wind_0.csv') for name in ['N0','F1','F2']}
qc=[]
for env in ENVS:
 base='F1' if env in ['S06','H1','F1'] else ('F2' if env in ['S08','H2','F2'] else 'N0')
 source=EXP/f'generated_project/wind_simulations/{base}/wind_0.csv';d=original[base].copy()
 if env in ['C06','C08']:d['U:0']=.6 if env=='C06' else .8;d[['U:1','U:2']]=0
 if env in ['H1','H2']:d['U:2']=0
 if env in ['S06','S08']:
  cube=d['U:0'].to_numpy().reshape(31,40,80);profile=cube[:,20,indices].mean(axis=1);d['U:0']=np.repeat(profile,40*80);d['U:2']=0
 target=gen/f'{env}.csv'
 if env in ['C20','F1','F2']:target.write_bytes(source.read_bytes())
 else:d.to_csv(target,index=False,float_format='%.9g',lineterminator='\n')
 if env in ['H1','H2']:
  assert np.array_equal(d['U:0'],original[base]['U:0'])
  # Preserve every original horizontal vector byte spelling/precision.
  lines=source.read_text().splitlines();out=[lines[0]]
  for line in lines[1:]:cols=line.split(',');cols[2]='0';out.append(','.join(cols))
  target.write_text('\n'.join(out)+'\n',encoding='utf-8',newline='')
 check=pd.read_csv(target);u=check['U:0'].to_numpy().reshape(31,40,80);w=check['U:2'].to_numpy().reshape(31,40,80);div=np.gradient(u,5,axis=2)+np.gradient(w,5,axis=0)
 row={'environment':env,'native_regular_grid_rows':len(d),'sha256':sha(target),'diagnostic_non_incompressible':env in ['H1','H2'],'max_abs_div_s_inv':float(abs(div[2:-2,2:-2,2:-2]).max()),'w_max':float(w.max()),'w_min':float(w.min()),'u_min':float(u.min()),'u_max':float(u.max())}
 assert np.isfinite(check.to_numpy()).all() and len(check)==99200
 if env not in ['H1','H2']:assert row['max_abs_div_s_inv']<.005
 if env in ['H1','H2']:assert np.array_equal(check['U:0'],original[base]['U:0']) and np.all(check['U:2']==0)
 qc.append(row)
 subprocess.run(['scp',str(target),HOST+':'+REMOTE+'/'+env+'.csv'],check=True)
 cmd=PREFIX+ADAPTER+' '+REMOTE+'/'+env+'.csv '+REMOTE+'/'+env+'_parity.csv'
 subprocess.run(['ssh',HOST,cmd],check=True)
 dest=OUT/f'{env}_parity.csv';subprocess.run(['scp',HOST+':'+REMOTE+'/'+dest.name,str(dest)],check=True)
 q=pd.read_csv(dest);coords=check.set_index(['Points:0','Points:1','Points:2']);expected=coords.loc[list(map(tuple,q[['x','y','z']].to_numpy())),['U:0','U:1','U:2']].to_numpy()
 error=float(np.max(abs(expected-q[['u','v','w']].to_numpy())));assert error<1e-5;row['query_parity_max_error']=error
pd.DataFrame(qc).to_csv(OUT/'wind_QC_and_parity.csv',index=False)
config={'protocol_commit':'c351b287faa74171fded9af122cf4992b9facbb2','environments':ENVS,'source_positions':[[x,y,1] for x,y in SOURCES],'plume_seeds':SEEDS,'primary_release_filaments_s':10,'secondary_releases_conditional':[5,20],'heights_m':HEIGHTS,'threshold_ppm':.001,'threshold_factors':[.5,1,2],'gas_and_path':'unchanged existing frozen adapter;120s warmup,300s query,1Hz,2m/s','S06_S08_definition':'x/y-invariant mean of corresponding F horizontal u over frozen300s XY path at each native z cell; not retuned from gas outcomes','H1_H2_definition':'exact corresponding original horizontal u/v, w=0; numerical diagnostic violating continuity; not physical weather','decision_policy':{'slow_sufficient':'slow C/S creates source-informative30m with >=.25 fractional Top1 improvement over C20, median positive margin, >=6/8 seeds positive margins','horizontal_sufficient':'H meets same information criterion','vertical_increment_supported':'F exceeds all associated C/S/H by >=25pp Top1 AND paired-seed bootstrap95% lower bound of mean margin difference>0 AND >=6/8 seed differences positive','bootstrap_units':'8 paired seed clusters; source-y/x retained within clusters;20000 resamples fixed RNG20261003','otherwise':'mixed/saturated/nonidentifiable; do not claim necessary vertical uplift','secondary_release_interpretable':'original full F30m source-information signal replicates on new seeds and C/S/H comparison yields stable sufficiency or stable incremental attribution; otherwise stop primary without release5/20','no_R1_1_or_R2':'both remain paused regardless of R1A outcome in this task'},'original_R1_decision':'R1_HOLD_WEAK_OR_UNSTABLE'}
(HERE/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
write_json('R1A_CONFIG.json',config)
config['independent_native_process_workers']=4
(HERE/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8');write_json('R1A_CONFIG.json',config)
files=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)+[EXP/'scripts/gaden_adapter.cpp',EXP/'scripts/score_identifiability.py']
(OUT/'PRE_GAS_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files))
print('R1A frozen controls:',len(qc),'seeds:',SEEDS)
