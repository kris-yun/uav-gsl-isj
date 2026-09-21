"""Integrity and sensor metadata only. Does not read source truth."""
import ast, csv, gzip, hashlib, importlib.util, json, math, sys
from pathlib import Path
import yaml
from export_mipo_patch import R2, OVERLAY, RUNTIME, sha, write, rows

out=Path(sys.argv[1]);m=json.loads((out/'manifest.json').read_text())
assert 'QUERY_EXPORT_COMPLETE' in (out/'logs/export.log').read_text()
assert sha(out/'anchors.csv')==m['anchor_sha256_before_query']
for p,h in m['runtime_hashes'].items():assert sha(p)==h,(p,'runtime drift')

tree=ast.parse((OVERLAY/'vgr_sim_node.py').read_text())
defaults={}
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='declare_parameter' and len(n.args)>=2:
        try:
            name=ast.literal_eval(n.args[0]);value=ast.literal_eval(n.args[1])
            if name.startswith('sensor_'):defaults[name]=value
        except (ValueError,TypeError):pass
mapping={'sensor_gain':'gain','sensor_baseline_ppm':'baseline','sensor_tau_rise_s':'tau_rise_s',
    'sensor_tau_recovery_s':'tau_recovery_s','sensor_dead_time_s':'dead_time_s',
    'sensor_noise_std_ppm':'noise_std_ppm','sensor_drift_rate_ppm_s':'drift_rate_ppm_s',
    'sensor_saturation_min_ppm':'saturation_min_ppm','sensor_saturation_max_ppm':'saturation_max_ppm',
    'sensor_initial_state_ppm':'initial_state_ppm','sensor_initial_input_ppm':'initial_input_ppm'}
sys.path.insert(0,str(OVERLAY));from sensor_model import SensorModel
sensor={}
for c in m['cases']:
    run=R2/'native'/(c['case_id']+'_off_off');resolved=[]
    for p in (run/'resolved_runtime').glob('launch_params_*'):
        doc=yaml.safe_load(p.read_text())
        for node in doc.values():
            params=node.get('ros__parameters',{})
            if 'sensor_model_mode' in params:
                resolved.append((p,{k:v for k,v in params.items() if k.startswith('sensor_')}))
    assert len(resolved)==1
    p,params=resolved[0];values={**defaults,**params}
    model=SensorModel(mode=values['sensor_model_mode'],seed=c['seed'],**{v:values[k] for k,v in mapping.items()})
    sensor[c['case_id']]=dict(model=model.manifest(),resolved_parameter_file_sha256=sha(p),resolved_sensor_parameters=params)
    for f in ('sim_pose_trace.csv','sensor_trace.csv','wind_trace.csv'):
        c.setdefault('baseline_trace_sha256',{})[f]=sha(run/f)
    # Time-mapping integrity only: do not inspect concentrations, direction, or localization metrics.
    trace=rows(run/'sensor_trace.csv');usable=max(1,c['max_iteration']-1)
    assert all(int(r['iteration'])==((7919*(c['seed']+1))%usable+int(r['step']))%usable for r in trace)
    assert all(abs(float(r['t_sim_s'])-.2*int(r['step']))<1e-6 for r in trace)
    c['time_mapping_integrity']='PASS'

write(out/'sensor_model.json',dict(pmfs_input='SensorModel.process(raw_gaden_ppm, 0.2), not direct raw concentration',
    gas_present_threshold_ppm=.1,source_runtime_git_sha=RUNTIME,
    source_files={str(OVERLAY/f):sha(OVERLAY/f) for f in ('sensor_model.py','vgr_sim_node.py','sim_timebase.py')},
    source_git_note='External frozen runtime overlay; bound by file SHA256 and R2 runtime Git SHA, not claimed tracked at a separate Git blob.',
    cases=sensor,patch_sensor_ppm='not exported: no defined pre-anchor sensor trajectory/state per counterfactual spatial point'))
audits={}
for p in sorted((out/'raw').glob('*.csv.gz')):
    with gzip.open(p,'rt',newline='') as f:r=list(csv.DictReader(f))
    assert len(r)==7840
    keys=[(v['sample_index'],v['dx_m'],v['dy_m']) for v in r];assert len(set(keys))==len(keys)
    times=[float(v['query_sim_time_s']) for v in r];assert all(a<=b for a,b in zip(times,times[1:]))
    assert all(v['occupancy'] in ('0','1','2','OUT_OF_BOUNDS') for v in r)
    assert all(int(v['free'])==int(v['occupancy']=='0') for v in r)
    for v in r:
        for k in ('raw_gaden_concentration_ppm','wind_x_mps','wind_y_mps','wind_z_mps'):
            assert v[k]=='NA' or math.isfinite(float(v[k]))
        if v['backend_valid']=='1':assert all(v[k]!='NA' for k in ('raw_gaden_concentration_ppm','wind_x_mps','wind_y_mps','wind_z_mps'))
    for dx in ('-0.6','-0.4','-0.2','0.0','0.2','0.4','0.6'):
        for dy in ('-0.6','-0.4','-0.2','0.0','0.2','0.4','0.6'):
            q=[v for v in r if v['dx_m']==dx and v['dy_m']==dy]
            assert len(q)==160
            assert [int(v['sample_index']) for v in q]==list(range(160))
            assert all(abs(float(v['rel_time_s'])-.2*i)<1e-6 for i,v in enumerate(q))
    audits[p.name]=dict(rows=len(r),duplicate_keys=0,time_monotonic=True,
        occupancy_counts={k:sum(v['occupancy']==k for v in r) for k in sorted(set(v['occupancy'] for v in r))},
        backend_na_rows=sum(v['backend_valid']=='0' for v in r),compressed_bytes=p.stat().st_size,sha256=sha(p),integrity='PASS')
assert len(audits)==m['valid_anchors']
m['raw_files']=audits;m['integrity']='PASS';m['total_rows']=sum(x['rows'] for x in audits.values())
m['total_raw_compressed_bytes']=sum(x['compressed_bytes'] for x in audits.values())
m['checksum_convention']='SHA256SUMS.json hashes every other exported file, excluding itself to avoid self-reference.'
write(out/'manifest.json',m)
write(out/'integrity_audit.json',dict(status='PASS',valid_anchors=m['valid_anchors'],invalid_anchors=m['invalid_anchors'],files=audits))
print('INTEGRITY_PASS',m['total_rows'],m['total_raw_compressed_bytes'])
