"""Truth producer. Inference consumer never receives this truth registry."""
import hashlib,json,pathlib
from datetime import datetime,timezone
import numpy as np
from r4_transport import step
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def generate():
    p=OUT/'R4_PREREGISTRATION_REV1.json'; d=json.loads(p.read_text(encoding='utf-8'))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==(OUT/'R4_PREREGISTRATION_REV1.sha256').read_text().split()[0]
    raw=OUT/'raw';public=raw/'observations';truthdir=raw/'evaluation_only';public.mkdir(parents=True,exist_ok=True);truthdir.mkdir(exist_ok=True)
    config={k:v for k,v in d.items() if k not in ['tasks','created_UTC']}
    (OUT/'R4_PUBLIC_MODEL_CONFIG.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    registered=[];physical=[]
    for t in d['tasks']:
        name=t['task_id']; target=public/(name+'.npz')
        if target.exists():raise RuntimeError('Frozen task already generated; no overwrite')
        q_rng=np.random.default_rng(t['release_seed']);w_rng=np.random.default_rng(t['wind_truth_seed']);y_rng=np.random.default_rng(t['gas_sensor_seed']);ws_rng=np.random.default_rng(t['wind_sensor_seed'])
        rhoq=np.exp(-.2/10);rhow=np.exp(-.2/3);logq=q_rng.normal(0,.08);ew=w_rng.normal(0,.015,2)
        angle=t['base_angle_rad']+(0 if t['regime']=='constant' else .8*np.sin(t['phase_rad']))
        w0=.6*np.array([np.cos(angle),np.sin(angle)])+ew;warmup=w0+ws_rng.normal(0,.02,(10,2))
        wind=np.zeros((500,2));wobs=np.full((500,2),np.nan);q=np.zeros(500);mass=np.zeros(500);fields=[];con=[];latent=[];raw_y=[];observed=[]
        c=np.zeros((24,24));src=d['inference']['source_support'][t['true_source_id']];cum=0.;maxres=0.;minimum=0.
        for k in range(500):
            time=k*.2;period=d['wind']['period_s'][t['regime']]
            angle=t['base_angle_rad']+(0 if period is None else .8*np.sin(2*np.pi*time/period+t['phase_rad']))
            ew=rhow*ew+np.sqrt(1-rhow*rhow)*.015*w_rng.normal(size=2)
            wind[k]=np.clip(.6*np.array([np.cos(angle),np.sin(angle)])+ew,-1,1)
            if k%5==0:wobs[k]=wind[k]+ws_rng.normal(0,.02,size=2)
            logq=rhoq*logq+np.sqrt(1-rhoq*rhoq)*.08*q_rng.normal();q[k]=np.exp(logq-.5*.08**2)
            c=step(c,wind[k]);c[src['row'],src['col']]+=.2*q[k]/.25;cum+=.2*q[k];mass[k]=c.sum()*.25
            maxres=max(maxres,abs(mass[k]-cum));minimum=min(minimum,float(c.min()))
            if (k+1)%10==0:
                r=d['route'][(k+1)//10-1];value=c[r['row'],r['col']];noisy=value+y_rng.normal(0,.02)
                con.append(value);raw_y.append(noisy);observed.append(max(0.,noisy));fields.append(c.copy())
        assert maxres<1e-9 and minimum>=0
        np.savez_compressed(target,y=np.array(observed),wind_obs=wobs,warmup=warmup,step=np.array([r['step'] for r in d['route']]),receiver_cells=np.array([[r['row'],r['col']] for r in d['route']]))
        np.savez_compressed(truthdir/(name+'.npz'),true_source_id=t['true_source_id'],wind=wind,release=q,concentration=np.array(con),raw_sensor=np.array(raw_y),gas_fields=np.array(fields),mass=mass)
        registered.append({'task_id':name,'split':t['split'],'inference_seed':t['inference_seed'],'file':str(target.relative_to(OUT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'true_source_in_observation_file':False})
        physical.append({'task_id':name,'max_mass_residual_mg':maxres,'min_concentration':minimum,'final_mass_mg':mass[-1],'wind_distinct_frames':int(len(np.unique(wind,axis=0))),'observations':50,'positive_detections':int(np.sum(np.array(observed)>.05))})
    (OUT/'R4_PUBLIC_OBSERVATION_REGISTRY.json').write_text(json.dumps(registered,indent=2)+'\n',encoding='utf-8')
    (OUT/'R4_GENERATION_VALIDITY.json').write_text(json.dumps({'UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS_CONTROLLED_MATH','tasks':physical,'independent_streams':'release/wind/gas sensor/wind sensor distinct seeds per whole task','no_parameter_fitting':True},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'generated_tasks':len(registered),'max_mass_residual':max(p['max_mass_residual_mg'] for p in physical)},ensure_ascii=False),flush=True)
if __name__=='__main__':generate()
