"""Restore actual synchronized concentration/windows, after native parity gate.

No interpolation, no propagation, no test-based sensor/action/window selection.
The decoder and C++ readout are accepted only after frozen historical native
concentration values have independently matched. Real sensor dynamics and UAV
flight remain unqualified; this is ideal native-sampled concentration research.
"""
from pathlib import Path
import csv, json, sys, time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gsl_discrimination.data import SynchronousBlock,DataQualification
from gaden_executor.reader import NativeQuery,decode_frame,NativeWorldExecutor
from recover_assets import ROOT,OUT,PROTO,OCC,run_path,sha,write,geometry_receipt

def points_for_probes(probes):
    result=[]
    for p in probes:
        for ix in range(int(p['native_x0']),int(p['native_x1_exclusive'])):
            for iy in range(int(p['native_y0']),int(p['native_y1_exclusive'])):
                result.append([np.float32(-7.55)+(np.float32(ix)+np.float32(.5))*np.float32(.1),
                               np.float32(-7.88)+(np.float32(iy)+np.float32(.5))*np.float32(.1),np.float32(.2)])
    return np.array(result,dtype=np.float32)

def main():
    started=time.time()
    if (OUT/'R1_EXTRACTION_RESULT.json').exists():raise RuntimeError('output already frozen')
    proto=json.loads(PROTO.read_text());input_result=json.loads((OUT/'R0_INPUT_RESULT.json').read_text())
    assert input_result['all_frames_match'] and input_result['sources_and_pools_legal']
    query=NativeQuery(OCC,ROOT/'native/native_query.dll')
    with (ROOT/'evidence/discovery/ocb_r2/metadata/E1_HOUSE_PROBE_CONTRACTS.tsv').open(newline='') as f:
        probes=sorted([r for r in csv.DictReader(f,delimiter='\t') if r['house']=='House01'],key=lambda r:int(r['probe_rank']))
    pair=[probes[i-1] for i in proto['pair_original_probe_ranks']]
    pair_points=points_for_probes(pair)
    assert all(r['legal_free'] for r in geometry_receipt(pair_points))
    # Validate the port against all 30 historic probe pools, all ten known times,
    # in TRAIN worlds only. DEV numerical responses remain unopened here.
    all_points=points_for_probes(probes)
    # Some historical probes may contain invalid cells; explicit report/stop,
    # never coerce a missing/invalid receiver into a zero concentration.
    legal=geometry_receipt(all_points)
    eligible=[k for k in range(30) if all(r['legal_free'] for r in legal[k*4:(k+1)*4])]
    regression=[]
    native_iters=[92,175,265,365,465,565,665,765,865,965]
    for run in proto['authorized_runs']:
        if not run.endswith(('r01','r02')):continue
        old=np.load(ROOT/'local_assets/ocb_x00/raw'/(run+'.pooled.npy'),allow_pickle=False)
        for j,index in enumerate(native_iters):
            frame=decode_frame(run_path(run)/('iteration_'+str(index)))
            for k in eligible:
                got=query.query(frame,all_points[k*4:(k+1)*4]).mean(dtype=np.float64)
                expected=float(old[j,k]);err=abs(float(got)-expected)
                regression.append({'run':run,'iteration':index,'probe_rank':k+1,'expected_ppm':expected,
                                   'actual_ppm':float(got),'absolute_error':err,
                                   'pass':err<=2e-5*max(1.,abs(expected))})
    result={'comparisons':len(regression),'nonzero_comparisons':sum(r['expected_ppm']>0 for r in regression),
            'max_absolute_error_ppm':max(r['absolute_error'] for r in regression),
            'all_pass':all(r['pass'] for r in regression),'tolerance':'2e-5 * max(1,abs(reference)); cross-compiler float32',
            'eligible_probe_ranks':[k+1 for k in eligible],
            'invalid_historical_pool_ranks':[k+1 for k in range(30) if k not in eligible],
            'readout_port_not_original_GCC_binary':True,'rows':regression}
    write('READOUT_NATIVE_REGRESSION.json',result)
    if not result['all_pass'] or result['nonzero_comparisons']<10:
        raise RuntimeError('native readout parity not established; no M1 fit')
    # Original U/V/W split-double files and saved native interleaved wind must
    # match numerically; local readout then uses only queried pool locations.
    wind_checks=[]
    first=run_path(proto['authorized_runs'][0])
    for wi in range(11):
        native=(first/'wind'/('wind_iteration_'+str(wi))).read_bytes()
        import struct
        assert struct.unpack_from('<ii',native)==(3,0)
        n=int(np.prod(query.dims))
        vec=np.frombuffer(native,dtype='<f4',offset=8).reshape(n,3)
        for c,axis in enumerate('UVW'):
            source=OCC.parent/'wind_simulations/1,3-2,4_fast'/f'1,3-2,4_fast_{wi}.csv_{axis}'
            b=source.read_bytes();assert struct.unpack_from('<i',b)[0]==999
            v=np.frombuffer(b,dtype='<f8',offset=4).astype(np.float32)
            ok=np.array_equal(v,vec[:,c]);wind_checks.append({'state':wi,'axis':axis,'source_sha256':sha(source),'exact_float32_match':ok})
    write('LOCAL_WIND_REGRESSION.json',{'all_pass':all(r['exact_float32_match'] for r in wind_checks),'checks':wind_checks,
          'policy_input':'only synchronous local vectors, never full arrays'})
    if not all(r['exact_float32_match'] for r in wind_checks):raise RuntimeError('wind layout not established')
    blocks=[]
    for run in proto['authorized_runs']:
        p=run_path(run)
        with (p/'RECORD_TIMELINE.tsv').open(newline='') as f:timeline=list(csv.DictReader(f,delimiter='\t'))
        indices=[i for i,r in enumerate(timeline) if 50<=float(r['internal_simulation_time_s'])<=70]
        executor=NativeWorldExecutor(p,query,timeline)
        got=executor.observe(indices,pair_points)
        values=got['values'].reshape(len(indices),2,4).mean(axis=2,dtype=np.float64)
        winds=got['local_wind_mps'].reshape(len(indices),2,4,3).mean(axis=2,dtype=np.float64)
        qualification=DataQualification(synchronous_spatial=True,physical_clock=True,continuous_window=True,
             local_wind=True,independent_realizations=True,alternative_sources=True,source_occupancy_validated=True,
             # No fake claim of a physically calibrated PID instrument.
             sensor_response_calibrated=False,native_samples_only=True,
             scope='native_saved_frames_ideal_four_cell_concentration_readout',
             limitations=('no measured PID bandwidth or rotor feedback','coarse native temporal sampling only',
                         'two source heights differ','known-source discovery, not deployment without calibration bank'))
        positions=np.array([[float(x['center_x_m']),float(x['center_y_m']),.2] for x in pair])
        block=SynchronousBlock(values,got['times_s'],positions,('pool12','pool17'),qualification,
             run+':native_50_70',run,'ppm',winds,metadata={'source_labels_in_evaluator_only':True,
             'interpolated':False,'readout':'float64 mean of four original float32 native point samples',
             'readout_verified_by':'READOUT_NATIVE_REGRESSION.json','hardware_sensor':False,
             'sampling_profile':'archive_native_coarse_v1','native_record_indices':[int(timeline[i]['record_index']) for i in indices]})
        target=OUT/'blocks'/(run+'.npz');block.save_npz(target)
        blocks.append({'run_id':run,'path':str(target.relative_to(OUT)),'sha256':sha(target),
                       'split':'train' if run.endswith(('r01','r02')) else 'dev',
                       'source_id':'B' if '_s2x_' in run else 'A','n_samples':len(indices),
                       'first_time_s':float(got['times_s'][0]),'last_time_s':float(got['times_s'][-1])})
        print('EXTRACTED',run,len(indices),flush=True)
    write('R1_EXTRACTION_RESULT.json',{'status':'PASS_NATIVE_SAVED_WINDOW_READOUT_FOR_IDEAL_SIMULATION',
          'blocks':blocks,'readout_regression_pass':True,'wind_regression_pass':True,
          'physical_hardware_sensor_qualification':False,'active_UAV_qualification':False,
          'original_fast_filter_profile_qualification':False,'duration_s':time.time()-started,
          'new_propagation_steps':0,'new_ROS':0})

if __name__=='__main__':main()
