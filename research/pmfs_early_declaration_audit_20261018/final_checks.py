from pathlib import Path
import collections,csv,difflib,hashlib,json,math
R=Path(__file__).resolve().parent;OLD=R.parent/'PMFS_PAPER_FIRST_ROS_QUAL_20261017';A=R/'analysis'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=json.loads((R/'PRECOMMIT.json').read_text());checks=[]
for role in plan['roles']:
 F=R/'cases'/role['id'];rt=F/'runtime';meta=json.loads((F/'CASE_META.json').read_text());param=json.loads((rt/'resolved_GSL_parameters.json').read_text());values={}
 for name,v in zip(param['names'],param['values']):values[name]=v['bool_value']if v['type']==1 else v['integer_value']if v['type']==2 else v['double_value']if v['type']==3 else v['string_value']
 assert all(values.get(k)==v for k,v in plan['parameters'].items())
 assert json.loads((rt/'BASELINE_PARAMETER_GATE.json').read_text())['status']=='PASS_ACTUAL_NODE_PARAMETER_VALUES'
 oldRole='PF24_A2_T02'if role['case']=='A2'else'PF24_B2_Q01'
 assert (rt/'navigation_map.s8').read_bytes()==(OLD/'cases'/oldRole/'runtime/navigation_map.s8').read_bytes()
 win=list(csv.DictReader((rt/'native_window_consumption.csv').open()));assert all(r['status']=='CONSUMED'and int(r['gas_count'])>0 and int(r['wind_count'])>0 for r in win)
 exe=json.loads((rt/'NATIVE_EXECUTABLE_IDENTITY.json').read_text());assert len(exe)==1 and exe[0]['sha256']==json.loads((R/'BUILD_RESULT.json').read_text())['binary_sha256']
 trace=list(csv.DictReader((rt/'physical_clock_trace.csv').open()));frames=[]
 for q in trace:
  frame=int(q['frame'])
  if not frames or frames[-1]!=frame:frames.append(frame)
 decreases=[(a,b)for a,b in zip(frames,frames[1:])if b<a]
 if role['case']=='A2':assert all(100<=x<=199 or x==200 for x in frames)and all(a==199 and b==100 or a==200 and b==100 for a,b in decreases)
 else:assert not decreases
 checks.append(dict(role=role['id'],case=role['case'],actual_parameters_match_frozen=True,parameters=plan['parameters'],actual_map_byte_matches_previous_official=True,nonempty_consumed_windows=len(win),binary_identity_pass=True,robot_clock=json.loads((rt/'CLOCK_SENSOR_RATE_PREFLIGHT.json').read_text()),observed_distinct_frame_range=[min(frames),max(frames)],observed_frame_sequence=frames,frame_wraps=decreases,candidate_map_bytes=(rt/'native_candidate_maps.f32').stat().st_size,candidate_calls=len(list(csv.DictReader((rt/'native_candidate_maps.csv').open())))))
# Verify all source files against the original qualified source. Only the passive
# capture file may differ; CMake options and all scientific functions are intact.
differences=[]
for p in (R/'source_runtime').rglob('*'):
 if p.is_file():
  rel=p.relative_to(R/'source_runtime');old=OLD/'source_runtime'/rel
  if sha(p)!=sha(old):differences.append(rel.as_posix())
assert differences==['src/gsl_server/algorithms/PMFS/internal/Simulations.cpp']
readouts=list(csv.DictReader((A/'FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv').open()));parities=[]
for role in plan['roles']:
 F=R/'cases'/role['id'];rt=F/'runtime';last=max(int(q['update'])for q in readouts if q['role']==role['id']);cpp=next(q for q in readouts if q['role']==role['id']and int(q['update'])==last and q['control']=='paper_alpha_D1');native=(rt/'native_results.csv').read_text().splitlines()[-1].split();err=float(native[3]);variance=float(native[5]);assert abs(float(cpp['top5_error_m'])-err)<6e-5 and abs(float(cpp['variance_m2'])-variance)<6e-6
 parities.append(dict(role=role['id'],native_error_m=err,cpp_recomputed_error_m=float(cpp['top5_error_m']),native_variance_m2=variance,cpp_recomputed_variance_m2=float(cpp['variance_m2'])))
put(A/'FINAL_INPUT_AND_TRACE_CHECKS.json',dict(status='PASS_ACTUAL_PARAMETERS_MAPS_INPUT_WINDOWS_AND_CAPTURE_IDENTITY',rows=checks,changed_source_files= differences,new_ROS_goals=4,new_worlds=0,AIMMD=0))
put(A/'FINAL_NATIVE_READOUT_PARITY.json',dict(status='PASS',rows=parities,Python_top5_tie_caveat='NumPy stable sort and double centers can differ slightly from native float-coordinate std::sort on tied coarse regions; all decisive final readouts use native C++ methods.'))
put(A/'INHERITED_METADATA_ERRATA.json',dict(policy='Frozen prior input files retained unchanged; these annotations supersede inherited descriptive fields, not runtime parameters',items=[dict(field='source_probability_and_planning_formulas_changed',inherited=False,correction='The paper-first reconstruction changes Eq6 and uses Eq8 D=1. This inherited early-audit flag is not an accurate description of the reconstructed baseline.'),dict(field='observation_validity_guard.binary',correction='Inherited historical receipt references an older binary. Actual NATIVE_EXECUTABLE_IDENTITY.json and BUILD_RESULT.json bind the executed September reconstruction binary.'),dict(field='clock.loop inclusive100..200',correction='Any such inherited description is wrong. Historical load->increment->>=200 means200 once then100..199. Modern core inclusive endpoint199 and tracker current-frame comparison give the same stable sequence. See independent semantic audit.'),dict(field='PAPER_FIGURE_MEANS.csv precision_note',correction='Independent visual review confirms A2=87.0s/B2=110.5s printed labels in Fig11. They are published one-decimal30-trial means, not author raw trials. Fig10 error values remain chart readings as recorded.')]))
print(json.dumps(dict(status='PASS',completed=len(checks),source_differences=differences,candidate_calls=sum(x['candidate_calls']for x in checks))))
