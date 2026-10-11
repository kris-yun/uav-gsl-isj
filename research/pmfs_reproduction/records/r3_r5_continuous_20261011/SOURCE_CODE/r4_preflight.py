"""No truth tasks: equal known constant wind, future perturbation and sensor law tests."""
import hashlib,json,pathlib,time
import numpy as np
from scipy.special import ndtr
from r4_infer import run_method,likelihood
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def main():
    d=json.loads((OUT/'R4_PREREGISTRATION.json').read_text(encoding='utf-8'));c={k:v for k,v in d.items() if k!='tasks'}
    w=np.full((500,2),np.nan);w[::5]=[.6,0]
    obs={'y':np.full(50,.01),'wind_obs':w,'warmup':np.tile([.6,0],(10,1)),'step':np.arange(1,51)*10,'receiver_cells':np.array([[r['row'],r['col']] for r in d['route']])}
    start=time.perf_counter();a,ma=run_method(obs,c,9199,'B0_FIXED');b,mb=run_method(obs,c,9199,'B1_TRANSIENT')
    equal=float(np.max(abs(a['source_posterior']-b['source_posterior'])));assert equal<1e-12, equal
    changed={k:v.copy() for k,v in obs.items()};changed['y'][20:]=.2;changed['wind_obs'][200::5]=[-.4,.3]
    cf,mcf=run_method(changed,c,9199,'B1_TRANSIENT');future1=float(np.max(abs(b['source_posterior'][:20]-cf['source_posterior'][:20])));assert future1==0
    pf,mpf=run_method(obs,c,9199,'B2_JOINT_PF');pf2,mpf2=run_method(changed,c,9199,'B2_JOINT_PF');future2=float(np.max(abs(pf['source_posterior'][:20]-pf2['source_posterior'][:20])));assert future2==0
    assert abs(np.exp(likelihood(0,np.array([0.])))[0]-.5)<1e-14
    assert np.allclose(np.exp(likelihood(0,np.array([0.,.01,.1]))),ndtr(-np.array([0.,.01,.1])/.02),atol=1e-14)
    result={'status':'PASS','truth_tasks_generated':0,'same_known_constant_B0_B1_posterior_maxdiff':equal,'B1_future_perturbation_prefix_maxdiff':future1,'B2_future_perturbation_prefix_maxdiff':future2,'left_censored_likelihood_CDF':True,'wind_only_ORACLE_capability':True,'wall_s':time.perf_counter()-start,'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'note':'Numerical/causal tests only; finite-PF convergence not proven'}
    (OUT/'R4_INTERFACE_PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
