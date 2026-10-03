"""Run native seeded GADEN in isolated processes, sequentially and gate checked."""
import pathlib,subprocess,json,time,argparse,hashlib,os
ROOT=pathlib.Path(__file__).resolve().parents[3];EXP=ROOT/'experiments/lakeshore_observability';OUT=ROOT/'evidence/lakeshore_observability_r0_r2';REMOTE='/home/zyc/lakeshore_observability_20261003';HOST='zyc@192.168.111.128'
PREFIX='source /opt/ros/humble/setup.bash; export LD_LIBRARY_PATH=/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH; export OMP_NUM_THREADS=1; '
def run(env,x,y,rate,seed,tag=None):
 tag=tag or f'{env}_x{x}_y{y}_r{rate}_seed{seed}'
 local=OUT/'observations'/f'{tag}.csv';local.parent.mkdir(exist_ok=True)
 if local.exists():return local
 cmd=PREFIX+f'export GADEN_RNG_SEED={seed}; {REMOTE}/adapter {REMOTE}/{env}.csv {REMOTE}/{tag}.csv {x} {y} {rate}'
 start=time.time();r=subprocess.run(['ssh',HOST,cmd],capture_output=True,text=True)
 (OUT/f'{tag}_runtime.log').write_text(r.stdout+r.stderr)
 if r.returncode: raise RuntimeError(r.stderr)
 subprocess.run(['scp',HOST+':'+REMOTE+'/'+tag+'.csv',str(local)],check=True)
 print(tag,'seconds',round(time.time()-start,2),flush=True);return local
def main(mode):
 assert json.loads((OUT/'R0_wisco_effect_summary.json').read_text())['decision']=='R0_GO'
 assert json.loads((OUT/'N0_parity.json').read_text())['decision']=='PASS'
 if mode=='seed_check':
  import pandas as pd,numpy as np
  a=run('N0',50,0,10,30001,'seed_check_a');b=run('N0',50,0,10,30001,'seed_check_b');c=run('N0',50,0,10,30002,'seed_check_c')
  aa=pd.read_csv(a);bb=pd.read_csv(b);cc=pd.read_csv(c)
  result={'same_seed_exact_match':bool(np.array_equal(aa.to_numpy(),bb.to_numpy())),'different_seed_concentration_differs':bool(np.any(aa.concentration.to_numpy()!=cc.concentration.to_numpy())),'positive_samples':int((aa.concentration>0).sum()),'rows':len(aa),'seed_contract':'GADEN_RNG_SEED; OMP_NUM_THREADS=1; one process per realization'}
  result['pass']=result['same_seed_exact_match'] and result['different_seed_concentration_differs']
  (OUT/'seed_repeatability.json').write_text(json.dumps(result,indent=2));print(result);assert result['pass'];return
 assert json.loads((OUT/'seed_repeatability.json').read_text())['pass']
 envs=['N0','F1'] if mode=='smoke' else ['N0','L1','F1','F2']; sources=[(20,0),(50,0),(80,0)] if mode=='smoke' else [(x,y) for x in [20,50,80] for y in [-20,0,20]]; rates=[10] if mode=='smoke' else [5,10,20]; seeds=[30001,30002] if mode=='smoke' else list(range(30001,30009))
 for env in envs:
  assert json.loads((OUT/f'wind_{env}_QC.json').read_text())['pass']
  subprocess.run(['scp',str(EXP/f'generated_project/wind_simulations/{env}/wind_0.csv'),HOST+':'+REMOTE+'/'+env+'.csv'],check=True)
 if mode=='full':assert json.loads((OUT/'smoke_matrix_validation.json').read_text())['pass']
 for env in envs:
  for x,y in sources:
   for rate in rates:
    for seed in seeds:run(env,x,y,rate,seed)
 (OUT/f'{mode}_execution.json').write_text(json.dumps({'environments':envs,'sources':sources,'rates_filaments_s':rates,'seeds':seeds,'realizations':len(envs)*len(sources)*len(rates)*len(seeds)},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['seed_check','smoke','full']);main(p.parse_args().mode)
