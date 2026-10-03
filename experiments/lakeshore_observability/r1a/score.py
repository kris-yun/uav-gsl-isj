"""Unchanged Brier estimator, paired-seed uncertainty and explicit attribution limits."""
import re,sys,numpy as np,pandas as pd
from scipy.stats import spearmanr
from common import *
sys.path.insert(0,str(EXP/'scripts'));import score_identifiability as frozen
def analyze(rates):
 a=np.full((9,len(rates),9,8,4,300),np.nan);ref=pd.read_csv(OLD/'fixed_path_contract.csv').to_numpy();manifest=[]
 for p in sorted((OUT/'observations').glob('*.csv')):
  m=re.fullmatch(r'(C20|C06|C08|S06|S08|H1|H2|F1|F2)_x(\d+)_y(-?\d+)_r(\d+)_seed(\d+)',p.stem);assert m,p
  env,x,y,r,k=m[1],int(m[2]),int(m[3]),int(m[4]),int(m[5])
  if r not in rates:continue
  d=pd.read_csv(p);assert len(d)==1200 and np.isfinite(d.to_numpy()).all() and (d.concentration>=0).all();assert np.array_equal(d[['time','x','y','z']].to_numpy(),ref)
  for j,z in enumerate(HEIGHTS):a[ENVS.index(env),rates.index(r),SOURCES.index((x,y)),SEEDS.index(k),j]=d[d.z==z].concentration
  manifest.append(dict(path=p.relative_to(ROOT).as_posix(),environment=env,source_x=x,source_y=y,release=r,plume_seed=k,rows=1200,sha256=sha(p)))
 assert np.isfinite(a).all(),'incomplete matrix'
 pd.DataFrame(manifest).to_csv(OUT/'observation_manifest.csv',index=False)
 frozen.ENVS=ENVS;frozen.RATES=rates;main=None;summaries={};allocation=[];rho_rows=[]
 for factor in [.5,1,2]:
  trials=frozen.score(a,.001*factor);trials.seed+=1000;trials['brier_margin']=trials.best_false_brier-trials.true_brier;trials['all_candidate_exact_tie']=(np.isclose(trials.top1,1/9,rtol=0,atol=1e-12))&(trials.true_rank==5)&(abs(trials.brier_margin)<1e-12)
  trials.to_csv(OUT/f'M4_trials_factor_{factor:g}.csv',index=False)
  summary=trials.groupby(['environment','release','height']).agg(top1=('top1','mean'),top3=('top3','mean'),median_rank=('true_rank','median'),median_margin=('brier_margin','median'),minimum_margin=('brier_margin','min'),exact_tie_fraction=('all_candidate_exact_tie','mean')).reset_index()
  hit=a>=.001*factor
  summary['hit_rate']=[float(hit[ENVS.index(row.environment),rates.index(row.release),:,:,HEIGHTS.index(row.height)].mean()) for row in summary.itertuples()]
  summary.to_csv(OUT/f'height_summary_factor_{factor:g}.csv',index=False);summaries[str(factor)]=summary
  if factor==1:main=trials
 hit=a>=.001
 for e,env in enumerate(ENVS):
  for r,rate in enumerate(rates):
   for s,(x,y) in enumerate(SOURCES):
    for k,seed in enumerate(SEEDS):
     lo=float(hit[e,r,s,k,0].mean());hi=float(hit[e,r,s,k,1].mean());ratio=hi/(lo+hi) if lo+hi else 0
     allocation.append(dict(environment=env,release=rate,source_x=x,source_y=y,seed=seed,hit10=lo,hit30=hi,R30=ratio))
 ar=pd.DataFrame(allocation);ar.to_csv(OUT/'R30_allocation_by_source_seed.csv',index=False)
 for (env,rate,seed),q in ar.groupby(['environment','release','seed']):
  g=q.groupby('source_x').agg(hit10=('hit10','mean'),hit30=('hit30','mean'));ratio=g.hit30/(g.hit10+g.hit30);rho=spearmanr(g.index,ratio.fillna(0)).statistic
  rho_rows.append(dict(environment=env,release=rate,seed=seed,spearman=float(rho) if np.isfinite(rho) else None))
 pd.DataFrame(rho_rows).to_csv(OUT/'source_x_R30_spearman.csv',index=False)
 # Peak-order exploration is always labelled secondary, with original settings.
 peak=[]
 for e,env in enumerate(ENVS):
  for r,rate in enumerate(rates):
   for s,(x,y) in enumerate(SOURCES):
    for k,seed in enumerate(SEEDS):
     h,t=np.unravel_index(np.argmax(a[e,r,s,k]),(4,300));q=ref[t*4+h]
     peak.append(dict(environment=env,release=rate,source_x=x,source_y=y,seed=seed,peak_x=q[1],peak_y=q[2],peak_height=q[3]))
 pk=pd.DataFrame(peak);pk.to_csv(OUT/'peak_positions_exploratory.csv',index=False);rs=[]
 for (env,r,k),q in pk.groupby(['environment','release','seed']):
  g=q.groupby('source_x').peak_x.mean();rho=spearmanr(g.index,g.values).statistic;rs.append(dict(environment=env,release=r,seed=k,rho=float(rho) if np.isfinite(rho) else None))
 pd.DataFrame(rs).to_csv(OUT/'source_x_peak_spearman_exploratory.csv',index=False)
 comparisons=[];information=[]
 for rate in rates:
  z30=main[(main.release==rate)&(main.height==30)];baseline=z30[z30.environment=='C20'].top1.mean()
  for env in ENVS:
   q=z30[z30.environment==env];seedmargin=q.groupby('seed').brier_margin.median();info=bool(q.top1.mean()-baseline>=.25 and q.brier_margin.median()>0 and (seedmargin>0).sum()>=6)
   information.append(dict(environment=env,release=rate,informative30=info,top1=float(q.top1.mean()),median_margin=float(q.brier_margin.median()),positive_margin_seed_count=int((seedmargin>0).sum())))
  for full,controls in [('F1',['C06','S06','H1']),('F2',['C08','S08','H2'])]:
   q=z30[z30.environment==full].set_index(['source_x','source_y','seed'])
   for control in controls:
    c=z30[z30.environment==control].set_index(['source_x','source_y','seed']);delta=(q.brier_margin-c.brier_margin).groupby(level='seed').mean().to_numpy();rng=np.random.default_rng(20261003);boot=delta[rng.integers(0,8,(20000,8))].mean(axis=1);lo,hi=np.quantile(boot,[.025,.975]);tp=float(q.top1.mean()-c.top1.mean());positive=int((delta>0).sum())
    comparisons.append(dict(full=full,control=control,release=rate,top1_increment_pp=tp*100,paired_mean_margin_increment=float(delta.mean()),cluster_bootstrap95_low=float(lo),cluster_bootstrap95_high=float(hi),positive_seed_count=positive,large_vertical_increment=bool(tp>=.25 and lo>0 and positive>=6)))
 pd.DataFrame(comparisons).to_csv(OUT/'paired_F_control_comparisons.csv',index=False)
 pd.DataFrame(information).to_csv(OUT/'information_sufficiency.csv',index=False)
 inf=[q for q in information if q['release']==10];slow=any(q['informative30'] for q in inf if q['environment'] in ['C06','C08']);shear=any(q['informative30'] for q in inf if q['environment'] in ['S06','S08']);horizontal=any(q['informative30'] for q in inf if q['environment'] in ['H1','H2']);fullrep=all(q['informative30'] for q in inf if q['environment'] in ['F1','F2'])
 vertical=any(all(q['large_vertical_increment'] for q in comparisons if q['full']==f and q['release']==10) for f in ['F1','F2'])
 decision='R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION' if slow else ('R1A_SHEAR_OR_HORIZONTAL_SUFFICIENT' if shear or horizontal else ('R1A_VERTICAL_INCREMENT_SUPPORTED_WITHIN_MODEL' if vertical else 'R1A_HOLD_NONIDENTIFIABLE'))
 result={'decision':decision,'original_R1_decision':'R1_HOLD_WEAK_OR_UNSTABLE','full_F_new_seed_replication':fullrep,'slow_uniform_sufficient':slow,'shear_control_sufficient':shear,'horizontal_only_sufficient':horizontal,'large_vertical_increment_supported':vertical,'decomposition_interpretable':bool(fullrep and (slow or shear or horizontal or vertical)),'release_levels_evaluated':rates,'realizations':len(manifest),'rows':1200*len(manifest),'information30':information,'paired_comparisons':comparisons,'R1_1_status':'PAUSED_NOT_EXECUTED','R2_status':'NOT_EXECUTED','limitations':['H1/H2 deliberately violate incompressibility and are diagnostic interventions only','C/S match path speed, not every source-to-path residence distribution; F-H is the exact horizontal-field comparison','Source templates share one fixed deterministic wind family; not unseen-weather generalization','8 seed clusters are Monte Carlo replications, not8 meteorological events','No real-lake quantitative uplift claim and no active-sensing benefit claim']}
 write_json('R1A_PRIMARY_DECISION.json' if rates==[10] else 'R1A_FINAL_DECISION.json',result)
 print(json.dumps({k:v for k,v in result.items() if k not in ['paired_comparisons','information30']},indent=2))
 print(summaries['1'].query('height==30').to_string(index=False))
if __name__=='__main__':analyze([10] if len(sys.argv)<2 or sys.argv[1]=='primary' else [5,10,20])
