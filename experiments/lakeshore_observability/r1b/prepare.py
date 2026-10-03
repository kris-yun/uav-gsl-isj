"""Operationalize ambiguities before ANY new gas output, then audit native wind IO."""
import subprocess, numpy as np, pandas as pd
from common import *
config={'protocol_commit':'f4d322a82ea21c1097108d71cb2cdc37e4233c76','scenes':SCENES,'environments':ENVS,'sources':SOURCES,'seeds':SEEDS,'release_levels':RATES,'threshold_ppm':.001,'threshold_factors':[.5,1,2],'prefixes_s':[30,60,120,300],'primary_endpoint':{'height_m':10,'prefix_s':300,'threshold_factor':1},'secondary_height_m':30,'unchanged_native_parameters':'methane;120s warmup;300s fixed XY ladder;1Hz;native adapter also records60/100m for byte-identical runtime, excluded from analysis','workers':4,'wind_construction':'original divergence-free streamfunction, same H100/dz15/dx35/background0.4; frozen original F1/F2 amplitude, translate front only; no gas-based tuning','uniform_match':'native cell u mean over fixed300s XY trajectory at z10; v=w=0','profile_match':'native cell u mean over same XY trajectory at EACH z; x/y-invariant, v=w=0','estimator':'Equal-prior release-pooled source/time hit probability with one Beta(1,1) prior: (1+sum of21 hits)/23, seven training seeds times three equally weighted releases; paired test seed excluded from ALL releases/candidates. Same temporal Brier; aligns protocol exploratory estimator.','ties':'absolute1e-12 Brier tolerance; equal probability across minimizers; fractional Top1, rank, expected Euclidean error and signed bias; retain individual prediction probabilities','front_lock_rule':'For each strength and baseline separately, calculate most-affected source-x by largest error fraction averaged over y/release/seeds; tied maxima use mean x. Across90/120/150 require all three scenes have errors, nondecreasing modal region and >=30m endpoint movement. Error-weighted centroid supplied as sensitivity only. Fixed source grid stays unchanged. This conservative discrete-grid operational definition is frozen before new gas, not an extra meteorological claim.','seed_direction_rule':'>=6/8 seeds with positive oracle-minus-baseline Top1 AND nonzero mean signed x bias in pooled-error majority direction; zero-x errors count against70% direction rule','scene_gate':'same baseline arm must satisfy oracleTop1>=.9; penalty>=.2; mean error>=5m OR error_fraction>=.2; signed majority among all errors>=.7; seed count>=6; strength/arm family front-lock rule; negative uniform truth/self-template Top1>=.9 for all6','decision_rule':'PASS >=4/6 scenes fulfill all gates and all negative controls; HOLD >=4/6 fulfill gates except front-lock and negatives pass but <4 fulfill all; otherwise FAIL. No selecting a passing prefix or threshold.','stop':'no R1.1/R2/PMFS/training/active-sensing/CFD; original decisions unchanged; gas robustness conditional on R1B PASS'}
(HERE/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8'); write_json('R1B_CONFIG.json',config)
subprocess.run(['ssh',HOST,'mkdir -p '+REMOTE],check=True)
binary=subprocess.check_output(['ssh',HOST,'sha256sum '+ADAPTER+' '+LIB],text=True)
assert binary.split()[0]=='b2670ae13e933e79004b565ae890b5d99d62cb980e5820bdd563929d4b6b82ec'
assert binary.splitlines()[1].split()[0]=='0b6a2160917a1e8791c1980635b0969c40794b96d591abba31d743758fc5f048'
(OUT/'runtime_binary_hashes_before.txt').write_text(binary)
ref=pd.read_csv(OLD/'fixed_path_contract.csv'); path=ref[ref.z==10]
idx=np.floor((path.x.to_numpy()+100)/5).astype(int); k10=int((10+5)//5)
wind=HERE/'wind';wind.mkdir(exist_ok=True);qc=[]
for scene in SCENES:
 front=int(scene.split('_')[0][2:]);strength=int(scene[-1])
 x=np.arange(-97.5,300,5);y=np.arange(-97.5,100,5);z=np.arange(-2.5,150,5)
 Z,Y,X=np.meshgrid(z,y,x,indexing='ij');zz=np.maximum(Z,0)
 f=.5*(1-np.tanh((zz-100)/15))
 integral=lambda a:.5*(a-15*(np.log(np.cosh((a-100)/15))-np.log(np.cosh(-100/15))))
 mean=integral(150)/150;I=integral(zz)-zz*mean;g=f-mean
 s=.5*(1-np.tanh((X-front)/35));sp=-.5/35/np.cosh((X-front)/35)**2
 amp=json.loads((OLD/f'wind_F{strength}_QC.json').read_text())['amplitude']
 u=.4+amp*s*g;w=-amp*sp*I;v=np.zeros_like(u)
 profile=u[:,20,idx].mean(axis=1);speed=float(profile[k10])
 for arm in ['F','C','S']:
  env=arm+'_'+scene;U=u if arm=='F' else (np.full_like(u,speed) if arm=='C' else np.broadcast_to(profile[:,None,None],u.shape));W=w if arm=='F' else np.zeros_like(w)
  d=pd.DataFrame({'U:0':U.ravel(),'U:1':v.ravel(),'U:2':W.ravel(),'Points:0':X.ravel(),'Points:1':Y.ravel(),'Points:2':Z.ravel()});target=wind/f'{env}.csv'
  if arm=='F' and front==120:
   target.write_bytes((EXP/f'generated_project/wind_simulations/F{strength}/wind_0.csv').read_bytes())
  else:d.to_csv(target,index=False,float_format='%.9g',lineterminator='\n')
  check=pd.read_csv(target);U=check['U:0'].to_numpy().reshape(31,40,80);W=check['U:2'].to_numpy().reshape(31,40,80)
  div=np.gradient(U,5,axis=2)+np.gradient(W,5,axis=0);err=float(abs(div[2:-2,2:-2,2:-2]).max());assert err<.005 and np.isfinite(check.to_numpy()).all()
  subprocess.run(['scp',str(target),HOST+':'+REMOTE+'/'+target.name],check=True)
  subprocess.run(['ssh',HOST,PREFIX+ADAPTER+' '+REMOTE+'/'+target.name+' '+REMOTE+'/'+env+'_parity.csv'],check=True,stdout=subprocess.DEVNULL)
  dest=OUT/(env+'_parity.csv');subprocess.run(['scp',HOST+':'+REMOTE+'/'+dest.name,str(dest)],check=True)
  q=pd.read_csv(dest);coord=check.set_index(['Points:0','Points:1','Points:2']);expected=coord.loc[list(map(tuple,q[['x','y','z']].to_numpy())),['U:0','U:1','U:2']].to_numpy();parity=float(abs(expected-q[['u','v','w']].to_numpy()).max());assert parity<1e-5
  qc.append(dict(environment=env,front_x=front,strength=strength,amplitude=amp,matched_speed=speed,wmax=float(W.max()),max_fd_div=err,query_parity=parity,rows=len(check),sha256=sha(target)))
  print(env,'parity',parity,flush=True)
pd.DataFrame(qc).to_csv(OUT/'wind_QC_and_parity.csv',index=False)
files=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)+[EXP/'scripts/gaden_adapter.cpp',OLD/'fixed_path_contract.csv',EXP/'R1A_POSTHOC_MODEL_MISMATCH_AND_R1B.md']
(OUT/'PRE_GAS_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files))
print('FROZEN:18 wind fields,3888 realizations; all scoring definitions hashed before gas.')
