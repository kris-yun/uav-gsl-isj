"""Independent checks of stored boundary fields/weights. No dynamics or rebuild."""
from pathlib import Path
import json,math,hashlib,time
import numpy as np
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011'
SHARE=Path('D:/ZYC/A-gas/workspace/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011')
def main():
    start=time.monotonic();q=json.loads((OUT/'L1_WIND_AND_GEOMETRY_QUALIFICATION.json').read_text());g=q['geometry'];nx,ny,nz=g['dims']
    cells=np.fromfile(SHARE/'geometry_states.u8',dtype=np.uint8);ids=np.flatnonzero(cells==0)
    assert len(ids)==g['Nfree']
    xyz=np.column_stack([ids%nx,ids//nx%ny,ids//(nx*ny)])
    B=np.memmap(SHARE/'flow_faces.f32',dtype='<f4',mode='r',shape=(24,len(ids),6))
    results=[];owners=[];values=[]
    for d,(axis,lim) in enumerate(zip(['x','y','z'],[nx,ny,nz])):
        for side,level in [('low',0),('high',lim-1)]:
            pick=np.flatnonzero(xyz[:,d]==level);face=2*d+(side=='high')
            v=np.asarray(B[:,pick,face]);results.append({'axis':axis,'side':side,'free_OOB_faces':len(pick),'max_abs_velocity_m_s_per_unit_mode':float(np.max(np.abs(v))),'nonzero_mode_faces_above_1e_7':int(np.count_nonzero(np.abs(v)>1e-7)),'required_native_air_boundary':'zero normal flux underblockedOOB gas boundary'})
            owners.append(np.column_stack([ids[pick],np.full(len(pick),d),np.full(len(pick),side=='high')]).astype('<i4'));values.append(v.astype('<f4'))
    np.save(OUT/'L1_OOB_FACE_OWNERS.npy',np.concatenate(owners));np.save(OUT/'L1_OOB_FACE_VELOCITIES.npy',np.concatenate(values,axis=1))
    receptor=np.array([-.9,.15,-.2]);lo=np.array(g['min']);h=g['h'];ix=np.floor((receptor-lo)/h).astype(int);cell=ix[0]+nx*ix[1]+nx*ny*ix[2]
    rn=int(np.flatnonzero(ids==cell)[0]);frac=(receptor-(lo+ix*h))/h
    H=np.stack([(1-frac[d])*B[:,rn,2*d]+frac[d]*B[:,rn,2*d+1] for d in [0,1]])
    np.save(OUT/'L1_LOCAL_WIND_OBSERVATION_H.npy',H)
    singular=np.linalg.svd(H,compute_uv=False);rank=int(np.sum(singular>1e-10))
    f32_divergence=[]
    for m in range(24):
        f=np.asarray(B[m],dtype=np.float64)
        f32_divergence.append(float(np.max(np.abs(np.sum(f[:,1::2]-f[:,::2],axis=1)/h))))
    lw=np.array([r['log_importance_weight'] for r in q['wind_refs']]);a=lw-lw.max();w=np.exp(a);w/=w.sum();ess=float(1/(w@w))
    record={
      'qualification':'INVALID_BOUNDARY_CONTRACT / FAIL_FINITE_REFERENCE_IMPORTANCE',
      'OOB_boundary_details':results,'total_free_OOB_faces':sum(x['free_OOB_faces'] for x in results),
      'OOB_normal_flux_zero':all(x['max_abs_velocity_m_s_per_unit_mode']<1e-7 for x in results),
      'source_evidence':{'file':'pinned gaden_core/src/RunningSimulation.cpp','StepTowards_block_lines':[256,267],'Outlet_lines':[269,270],'Environment_at_index_OOB_lines':[47,51],'wind_provider':'newposition-aware interpolation doesnotalter originalStepTowards'},
      'wind_probability_weights':w.tolist(),'log_weight_gap':float(lw[0]-lw[1]),'log10_weight_ratio':float((lw[0]-lw[1])/math.log(10)),'ESS':ess,'ESS_over_K':ess/2,'registered_threshold':.8,'ESS_gate_pass':ess/2>=.8,
      'two_references_are_not_full447_qualification_even_if_ESS_passed':True,
      'source_level_failure':'OOB airflow open but nativegasblocked/sliding. Divergencepassdoesnotclose boundarypass.',
      'statistical_failure_scope':'conditional sampler/hyperparameter coverage inadequate withK2; neither posteriorwindlaw itself nor realworld sourceidentifiability falsified',
      'local_wind_linear_observation_rank':rank,'local_wind_observation_singular_values':singular.tolist(),'unobserved_coefficient_dimensions_given_fixed_isotropic_OU_hyperparameters':24-rank,
      'rank_scope':'V1 finitefield basis, allwindatonehorizontalpoint; gasmeasurements mayprovideadditional information. Not a theorem of actual B4 source nonidentifiability.',
      'saved_float32_basis_max_divergence_per_s':max(f32_divergence),'saved_float32_divergence_gate_pass':max(f32_divergence)<=1e-5,
      'gas_forwards_started':0,'gas_forwards_completed':0,'native_goals':0,'field_or_path_regeneration':False,'active_wall_s':time.monotonic()-start,
    }
    (OUT/'L1_INDEPENDENT_BOUNDARY_AND_ESS_FAIL.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    # Fail-closed dependency gate fixture, not an actualnativeconsumer.
    rejected=[]
    for name in ['boundary','finite_reference']:
        gate = record['OOB_normal_flux_zero'] if name=='boundary' else record['ESS_gate_pass']
        assert gate is False
        rejected.append({'gate':name,'dependent_gas_or_goal_allowed':False})
    (OUT/'L1_DEPENDENT_EXECUTION_REJECTION.json').write_text(json.dumps({'fixture_only':True,'rejected':rejected,'actualforwards':0,'actualgoals':0},indent=2)+'\n',encoding='utf8')
    print(json.dumps({'total_free_OOB_faces':record['total_free_OOB_faces'],'max_abs_OOB_normal_velocity_per_unit_mode':max(x['max_abs_velocity_m_s_per_unit_mode'] for x in results),'ESS':ess,'log10_weight_ratio':record['log10_weight_ratio'],'gas_calls':0}))

if __name__=='__main__':main()
