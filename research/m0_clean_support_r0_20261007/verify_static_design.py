"""Independent R0 math/contract audit. NO simulator, field asset, CFD or launcher.

The A check differentiates a full scalar potential with numpy.gradient,
rather than importing the builder's separable curl. Geometry/route/decision
checks read frozen parameter tables. Gate examples are explicitly synthetic.
"""
from pathlib import Path
import ast, csv, hashlib, json, math, copy
import numpy as np
from gate_logic import decide, CONFIG

ROOT=Path(__file__).resolve().parent
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
checks={};details={}
def require(name,condition):
    checks[name]=bool(condition)
    if not condition:raise AssertionError(name)

required=['M0_SCIENTIFIC_CONTRACT.md','M0_DOMAIN_ROI_GUARD_CONTRACT.json','M0_BASE_WIND_CONTRACT.json','M0_SOURCE_CONTRACT.json','M0_UAV_ROUTE_CONTRACT.json','M0_PERTURBATION_CONTRACT.json','M0_RUNLIST_PREVIEW.csv','M0_RESOURCE_ESTIMATE.md']
require('eight_required_deliverables',all((ROOT/p).is_file() for p in required))
D=load('M0_DOMAIN_ROI_GUARD_CONTRACT.json');B=load('M0_BASE_WIND_CONTRACT.json');S=load('M0_SOURCE_CONTRACT.json');R=load('M0_UAV_ROUTE_CONTRACT.json');P=load('M0_PERTURBATION_CONTRACT.json');A=load('M0_STATIC_FIELD_AUDIT.json');I=load('M0_INFERENCE_CONTRACT.json')
lo=np.array(D['simulation_domain_m']['min']);hi=np.array(D['simulation_domain_m']['max']);rlo=np.array(D['analysis_roi_m']['min']);rhi=np.array(D['analysis_roi_m']['max']);h=D['grid_cell_m'];n=np.rint((hi-lo)/h).astype(int)
outlo=lo+h;outhi=hi-h
require('grid_dimensions',list(n)==D['grid_dimensions_xyz'] and math.prod(n)==D['total_cells'])
guards=np.array([rlo[0]-outlo[0],outhi[0]-rhi[0],rlo[1]-outlo[1],outhi[1]-rhi[1],rlo[2]-outlo[2],outhi[2]-rhi[2]])
require('true_ROI_guard_all6',np.array_equal(guards,list(D['guard_to_effective_outlet_m'].values())) and np.min(guards)==6.75)
pts=np.array([s['xyz_m'] for s in S['candidate_sources']]);clear=np.min(np.concatenate([pts-outlo,outhi-pts],axis=1))
require('both_sources_same_height_interior_support',np.all(pts>rlo) and np.all(pts<rhi) and pts[0,2]==pts[1,2]==5 and clear==S['minimum_clearance_to_effective_outlet_m']==10.75 and np.linalg.norm(pts[1]-pts[0])==2)
require('every_baseline_every_intervention_all_sides',D['qualification']['required_baseline_runs']==8 and D['qualification']['all_4_per_source_must_pass'] and 'All 32' in D['intervention_support_rule'] and D['qualification']['removed_filaments_allowed']==0)

x,y,z=[np.arange(a+h/2,b,h) for a,b in zip(lo,hi)]
free=((z[:,None,None]>outlo[2])&(z[:,None,None]<outhi[2])&(y[None,:,None]>outlo[1])&(y[None,:,None]<outhi[1])&(x[None,None,:]>outlo[0])&(x[None,None,:]<outhi[0]))
roi=((z[:,None,None]>rlo[2])&(z[:,None,None]<rhi[2])&(y[None,:,None]>rlo[1])&(y[None,:,None]<rhi[1])&(x[None,None,:]>rlo[0])&(x[None,None,:]<rhi[0]))
require('fixed_RMSE_volume_counts',int(free.sum())==A['global_free_voxels']==3534776 and int(roi.sum())==A['roi_voxels']==163840)
def compact(q):
    q=np.asarray(q,dtype=np.float64);u=np.zeros_like(q);ix=np.abs(q)<1.;u[ix]=np.exp(1-np.reciprocal(1-q[ix]**2));return u
# Preserve the contracted bump evaluation order at float32 quantization ties.
# Independence is supplied by full-potential differentiation and separate geometry/gate algebra.
base=np.zeros((n[2],n[1],n[0],3),dtype=np.float32)
base[...,0]=(0.08+0.04*np.tanh((z-5)/1.5))[:,None,None];base[...,2]=.005
ind={};max_stats_diff=0.;ind_shear={}
for arm in P['arms']:
    f=base.copy()
    if arm in ['A_on','A_off']:
        cy=P['pair_A']['centres_m'][arm][1];gain=P['pair_A']['streamfunction_gain_m2_s']
        psi=compact((z-5)/3)[:,None,None]*compact((y-cy)/2)[None,:,None]*compact((x-6)/6)[None,None,:]
        gy=np.gradient(psi,h,axis=1);gx=np.gradient(psi,h,axis=2)
        f[...,0]=base[...,0].astype(float)+gain*gy;f[...,1]=-gain*gx
        del psi,gy,gx
    elif arm=='B_shear':
        f[...,0]=base[...,0].astype(float)+(-.04*np.tanh((z-5)/1.5)*compact((z-5)/3))[:,None,None]
    elif arm=='B_speed':
        f[...,0]=base[...,0].astype(float)+(P['pair_B']['K_B_m_s']*compact((z-5)/3))[:,None,None]
    delta=f.astype(float)-base.astype(float)
    norm2=np.sum(delta*delta,axis=3)
    ff=f.astype(float)
    div=((ff[1:-1,1:-1,2:,0]-ff[1:-1,1:-1,:-2,0])+(ff[1:-1,2:,1:-1,1]-ff[1:-1,:-2,1:-1,1])+(ff[2:,1:-1,1:-1,2]-ff[:-2,1:-1,1:-1,2]))/(2*h)
    ind[arm]={'simulation_free_rmse_m_s':float(np.sqrt(norm2[free].mean())),'ROI_rmse_m_s':float(np.sqrt(norm2[roi].mean())),'max_div_s_inv':float(abs(div).max()),'RMS_div_s_inv':float(np.sqrt((div*div).mean())),'support_voxels':int((norm2>0).sum())}
    require('physical_'+arm,np.isfinite(f).all() and f[...,0].min()>=.02 and np.sqrt(np.sum(ff*ff,axis=3)).max()<=.20 and np.sqrt(norm2).max()<=.0500001 and abs(div).max()<=1e-6 and np.sqrt((div*div).mean())<=1e-7)
    for name,vol in [('simulation_free_rmse_m_s','simulation_free'),('ROI_rmse_m_s','analysis_roi')]:
        max_stats_diff=max(max_stats_diff,abs(ind[arm][name]-A['statistics'][arm][vol]['vector_rmse_m_s']))
    require('independent_support_'+arm,ind[arm]['support_voxels']==A['statistics'][arm]['perturbed_voxel_count'])
    if arm in ['U0','B_shear','B_speed']:
        k=int(np.flatnonzero(z<5)[-1]);ind_shear[arm]=float((ff[k+1,0,0,0]-ff[k,0,0,0])/h)
    del f,ff,delta,div,norm2
require('independent_full_potential_RMSE',max_stats_diff<=1e-10)
for name,pair in P['only_two_pairs'].items():
    for vol in ['simulation_free_rmse_m_s','ROI_rmse_m_s']:
        a,b=[ind[p][vol] for p in pair];diff=abs(a-b)
        require('matched_'+name+'_'+vol,diff<=P['RMSE']['absolute_pair_mismatch_max_m_s'] and diff/max(a,b)<=P['RMSE']['relative_pair_mismatch_max'])
require('same_A_support_volume',ind['A_on']['support_voxels']==ind['A_off']['support_voxels'])
require('B_shear_removed_speed_shear_preserved',abs(ind_shear['B_shear']/ind_shear['U0'])<=.05 and .95<=ind_shear['B_speed']/ind_shear['U0']<=1.05)
require('expected_wind_hashes_consistent',A['expected_modern_wind_sha256']==P['expected_modern_wind_sha256'] and B['native_wind_recipe']['expected_field_sha256']==P['expected_modern_wind_sha256']['U0'])
details['independent_field_metrics']=ind;details['independent_RMSE_max_difference_m_s']=max_stats_diff

v=np.array(R['waypoints_xyz_m']);schedule=R['segment_schedule'];path=np.linalg.norm(np.diff(v,axis=0),axis=1);route=rows('M0_UAV_ROUTE_POINTS.csv')
require('route_has_no_source_or_wind_input',R['input_allowlist']==['analysis ROI extents','fixed horizontal insets 4 m in x and 5 m in y','row spacing 1 m','ROI middle altitude','times 20..120 s','fixed speed and acceleration limits and dwell'])
tree=ast.parse((ROOT/'static_design_math.py').read_text(encoding='utf-8'));func=next(f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name=='route_points')
referenced={node.id for node in ast.walk(func) if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load)}
require('route_function_source_blind_signature',len(func.args.args)==0 and not referenced.intersection({'sources','S','U0','ARMS','wind','plume','source_id','candidate_sources','true_source'}))
require('continuous_route_clearance',np.all(v-.25>=rlo) and np.all(v+.25<=rhi) and np.all(v[:,2]==(rlo[2]+rhi[2])/2) and len(v)==14 and math.isclose(float(path.sum()),90))
cursor=20.;kinetic_samples_max_diff=0.
for j,seg in enumerate(schedule):
    dur=seg['end_s']-seg['start_s'];ramp=seg['ramp_s'];speed=seg['peak_speed_m_s'];acc=seg['acceleration_m_s2'];L=seg['length_m']
    require('segment_'+str(j),abs(seg['start_s']-cursor)<1e-10 and np.array_equal(seg['from_xyz_m'],v[j]) and np.array_equal(seg['to_xyz_m'],v[j+1]) and abs(L-path[j])<1e-10 and abs(speed-acc*ramp)<1e-10 and abs(speed*(dur-ramp)-L)<1e-10 and dur>=2*ramp-1e-10 and speed<=1.2 and acc<=1)
    cursor=seg['end_s']+seg['dwell_after_s']
require('route_timeline',abs(cursor-120)<1e-10 and [float(q['time_s']) for q in route]==list(np.arange(20,121,2)))
for q in route:
    t=float(q['time_s']);point=v[-1].copy();vel=np.zeros(3);accel=np.zeros(3)
    for seg in schedule:
        if seg['start_s']<=t<seg['end_s']:
            tau=t-seg['start_s'];dur=seg['end_s']-seg['start_s'];rr=seg['ramp_s'];a=seg['acceleration_m_s2'];vv=seg['peak_speed_m_s'];direction=(np.array(seg['to_xyz_m'])-np.array(seg['from_xyz_m']))/seg['length_m']
            # Integrate the clipped acceleration/ramp durations, independently of route writer cases.
            t1=min(tau,rr);t2=min(max(tau-rr,0),max(dur-2*rr,0));t3=max(tau-(dur-rr),0)
            dist=.5*a*t1*t1+vv*t2+vv*t3-.5*a*t3*t3
            point=np.array(seg['from_xyz_m'])+direction*dist;vel=direction*min(a*tau,vv,a*(dur-tau));accel=direction*(a if tau<rr else (-a if tau>dur-rr else 0));break
        if seg['end_s']<=t<seg['end_s']+seg['dwell_after_s']:point=np.array(seg['to_xyz_m']);break
    actual=np.array([float(q[k]) for k in ['x_m','y_m','z_m','vx_m_s','vy_m_s','vz_m_s','ax_m_s2','ay_m_s2','az_m_s2']]);target=np.concatenate([point,vel,accel]);kinetic_samples_max_diff=max(kinetic_samples_max_diff,float(abs(actual-target).max()))
require('route_samples_independent_integral',kinetic_samples_max_diff<1e-10 and sha(ROOT/'M0_UAV_ROUTE_POINTS.csv')==R['sample_points_sha256'])
details['route_sample_max_absolute_difference']=kinetic_samples_max_diff

runlist=rows('M0_RUNLIST_PREVIEW.csv');expected={(a,s,r) for a in P['arms'] for s in ['S0','S1'] for r in [1,2,3,4]}
require('40_fixed_unique_run_preview',len(runlist)==40 and len({q['run_id'] for q in runlist})==40 and {(q['wind_arm'],q['source_id'],int(q['realization'])) for q in runlist}==expected)
require('8_then32_no_execution_authorization',all(q['wind_arm']=='U0' for q in runlist[:8]) and all(q['wind_arm']!='U0' for q in runlist[8:]) and all(q['launch_authorized']=='False' for q in runlist))
require('one_RNG_one_clock_all_winds',all(int(q['master_seed'])==S['rng']['master_seeds'][int(q['realization'])-1] and float(q['sim_time_s'])==140 and float(q['dt_s'])==.1 and q['expected_wind_sha256']==P['expected_modern_wind_sha256'][q['wind_arm']] for q in runlist))
require('exact_two_pairs_no_oracle_BMA',len(P['only_two_pairs'])==2 and set(I['WRONG_MODEL_BMA']['models'])==set(P['arms'])-{'U0'} and I['WRONG_MODEL_BMA']['U0_excluded'])
require('LORO_no_query_seed_in_templates',I['folds']['training_count_per_source_wind']==3 and 'both candidate' in I['folds']['held_out'] and I['folds']['independent_seed_blocks']==4)

# Safety-semantic examples. These are fabricated scores solely to check the decision gate.
ok={k:True for k in CONFIG['prerequisites']}
def make_data():
    return {p:[{'source':s,'realization':r,'D_F_first':.1,'D_F_second':.1,'D_Y_first':.1,'D_Y_second':.1,'brier':{f:{'oracle':.04,'first':.04,'second':.04} for f in CONFIG['families']}} for s in ['S0','S1'] for r in range(1,5)] for p in ['A','B']}
def signal(d,source=None,family=None,sign=1):
    for q in d['A']:
        if source is not None and q['source']!=source:continue
        if q['realization']==4:continue
        worse='first' if sign==1 else 'second'
        q['D_F_'+worse]=.4;q['D_Y_'+worse]=.4
        for f in CONFIG['families'] if family is None else [family]:q['brier'][f][worse]=.36
    return d
synthetic={}
def example(name,data,flags,nruns,expected_verdict):
    result=decide(flags,nruns,data);require('synthetic_gate_'+name,result['verdict']==expected_verdict);synthetic[name]=result['verdict']
example('qualified_null',make_data(),ok,40,'M0_STOP')
positive=signal(make_data());example('one_pair_both_sources_families',positive,ok,40,'M0_PASS')
example('negative_direction_preregistered',signal(make_data(),sign=-1),ok,40,'M0_PASS')
example('single_source_only',signal(make_data(),source='S0'),ok,40,'M0_PARTIAL_HOLD')
example('single_family_only',signal(make_data(),family='HIT_FORWARD'),ok,40,'M0_PARTIAL_HOLD')
split=signal(make_data(),source='S0');signal(split,source='S1',sign=-1);example('source_direction_split',split,ok,40,'M0_PARTIAL_HOLD')
broken=copy.deepcopy(positive)
for q in broken['A']:q['D_Y_first']=q['D_Y_second']
example('no_sensor_chain',broken,ok,40,'M0_PARTIAL_HOLD')
rescue=copy.deepcopy(positive)
for q in rescue['A']:
    for f in CONFIG['families']:q['brier'][f]={'oracle':.36,'first':.36,'second':.04}
example('rescue_only_no_harm',rescue,ok,40,'M0_PARTIAL_HOLD')
bad=copy.deepcopy(ok);bad['baseline_support_all8']=False;example('failed_support_even_if_signal',positive,bad,40,'M0_PREREQUISITE_HOLD')
unknown=copy.deepcopy(ok);unknown.pop('RNG_alignment');example('unknown_RNG_even_if_signal',positive,unknown,40,'M0_PREREQUISITE_HOLD')
example('insufficient_runs_even_if_signal',positive,ok,39,'M0_PREREQUISITE_HOLD')
disjoint=signal(make_data())
for q in disjoint['A']:
    if q['realization']==1:q['D_F_first']=.1
    if q['realization']==4:q['D_F_first']=.4;q['D_Y_first']=.4
example('different_metric_seed_sets_cannot_pass',disjoint,ok,40,'M0_PARTIAL_HOLD')
details['synthetic_gate_examples_NOT_simulation_results']=synthetic

native_expected={'MathUtils.hpp':S['runtime']['MathUtils.hpp_sha256'],'PointSource.hpp':S['runtime']['PointSource.hpp_sha256']}
for name,val in native_expected.items():require('native_source_sha_'+name,sha(ROOT/'provenance'/name)==val)
parent_rows=rows('M0_PARENT_INPUTS_SHA256.csv')
for q in parent_rows:
    basename=Path(q['path']).name;p=ROOT/'provenance'/basename
    if q['role']=='frozen historical decision':p=ROOT/'provenance'/('W0C_'+basename)
    require('provenance_'+basename,p.is_file() and sha(p)==q['sha256'])
hist=load('provenance/W0C_STAGE0_V2_DECISION.json');prov=load('M0_DESIGN_PROVENANCE.json')
require('preserved_W0C_HOLD',prov['W0C_verdict']=='W0C_STAGE0_NO_CLEAN_BASE_HOLD' and 'W0C_STAGE0_NO_CLEAN_BASE_HOLD' in json.dumps(hist))
oldzip=ROOT/'provenance/W0C_STAGE0_NO_CLEAN_BASE_HOLD_20261007.zip'
require('historical_portable_archive_unchanged',sha(oldzip)==prov['historical_archive_sha256'])
require('no_generated_simulation_assets',not list(ROOT.rglob('*.csv_gaden')) and not list(ROOT.rglob('*OccupancyGrid3D*')) and not list(ROOT.rglob('*.launch.py')) and all(prov[k]==0 for k in ['new_GADEN_runs','new_OpenFOAM_runs','new_PMFS_runs','new_wind_files','new_occupancy_files']))
for name in ['build_design.py','static_design_math.py','gate_logic.py']:
    names={node.id for node in ast.walk(ast.parse((ROOT/name).read_text(encoding='utf-8'))) if isinstance(node,ast.Name)}
    require('no_launcher_dependency_'+name,not names.intersection({'subprocess','Popen','ROS','roslaunch','ssh'}))

report={'status':'STATIC_DESIGN_CHECKS_PASS','scientific_verdict':'NOT_TESTED','execution_authorized':False,'GADEN_runs':0,'OpenFOAM_runs':0,'PMFS_runs':0,'checks':checks,'details':details,'pending_runtime_gates':CONFIG['prerequisites'],'limitations':['Independent static algebra does not prove stochastic containment or actual native-decoder parity.','Synthetic decision checks are not experimental evidence.','Source observation, on/off mass relevance, paired RNG and resource behaviour await explicitly authorized execution.']}
target=ROOT/'M0_STATIC_DESIGN_VERIFICATION.json'
if (ROOT/'M0_R0_FREEZE.json').exists():
    old=load(target.name);require('frozen_verification_reproducible',old==report)
else:target.write_bytes((json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
print(json.dumps({'status':report['status'],'checks_passed':len(checks),'independent_RMSE_max_difference_m_s':max_stats_diff,'new_GADEN_runs':0,'scientific_verdict':'NOT_TESTED'},indent=2))
