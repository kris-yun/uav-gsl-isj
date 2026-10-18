from pathlib import Path
import csv, hashlib, json, math, re, subprocess, sys
from datetime import datetime, timezone
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
WS = ROOT.parent
QUAL = WS / 'PMFS_PAPER_FIRST_ROS_QUAL_20261017'
OFF = QUAL / 'official_exact'
CONFIG = OFF / 'Environment_config/PMFS'
CACHE = WS / 'CLP16/source/reference_package/actual_runtime'
PAPER = WS / 'PMFS_OFFICIAL_REPRO_AUDIT_20261016/PAPER_RECORD/PMFS_TRO_2024_USER_ORIGINAL.pdf'
inventory = {}

def read(path):
    path = Path(path)
    data = path.read_bytes()
    inventory[str(path)] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return data

def js(path):
    return json.loads(read(path))

def lines(path):
    return read(path).decode('utf-8-sig').splitlines()

def write(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def yaml_scalar(path, key):
    txt = read(path).decode('utf-8-sig')
    m = re.search(r'^'+re.escape(key)+r':\s*([^#\n]+)', txt, re.M)
    assert m, (path,key)
    return json.loads(m.group(1).strip())

lock = js(QUAL/'SOURCE_LOCK.json')
source_verification = []
for entry in lock['files']:
    p = OFF / entry['path']
    data = read(p)
    oid = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    valid = hashlib.sha256(data).hexdigest() == entry['sha256'] and oid == entry['git_blob_oid']
    assert valid, p
    source_verification.append(dict(path=entry['path'], sha256=entry['sha256'], git_blob_oid=oid, passed=valid))

maps=[]
for case, run in [('A2','PF24_A2_T02'), ('B2','PF24_B2_Q01')]:
    rt = QUAL/'cases'/run/'runtime'
    sim = CONFIG/'scenarios'/case[0]/'simulations'/f'{case}.yaml'
    mapyaml = CONFIG/'scenarios'/case[0]/'_occupancy.yaml'
    src=[float(yaml_scalar(sim,'source_'+v)) for v in 'xyz']
    meta=js(rt/'NAVIGATION_MAP_METADATA.json')
    raw=read(rt/'navigation_map.s8')
    pgm=CONFIG/'scenarios'/case[0]/'_occupancy.pgm'
    read(pgm)
    image=Image.open(pgm)
    w,h=image.size
    assert [w,h] == [meta['width'],meta['height']]
    expected=bytes(0 if v >229 else 100 if v <26 else 255 for y in range(h) for v in [image.getpixel((x,h-1-y)) for x in range(w)])
    assert expected==raw
    origin=yaml_scalar(mapyaml,'origin')
    nominal=float(yaml_scalar(mapyaml,'resolution'))
    assert origin[:2] == [meta['origin_x'],meta['origin_y']]
    i=math.floor((src[0]-origin[0])/meta['resolution'])
    j=math.floor((src[1]-origin[1])/meta['resolution'])
    pixel=[i,h-1-j]
    posterior_path=rt/'native_posterior_updates.csv'
    read(posterior_path)
    with posterior_path.open(newline='') as f:
        support=[r for r in csv.DictReader(f) if r['update']=='1']
    nearest=min(support, key=lambda r:math.hypot(float(r['x_m'])-src[0],float(r['y_m'])-src[1]))
    cell=meta['resolution']*25
    coarse=[math.floor((src[0]-origin[0])/cell),math.floor((src[1]-origin[1])/cell)]
    truth_in_support=any([int(r['col']),int(r['row'])]==coarse for r in support)
    distance=math.hypot(float(nearest['x_m'])-src[0],float(nearest['y_m'])-src[1])
    row=dict(case=case,run=run,official_source_xyz=src,origin_xy=origin[:2],
             nominal_resolution_m=nominal,runtime_float_resolution_m=meta['resolution'],
             image_size_wh=[w,h],full_map_byte_parity=True,source_map_index_xy=[i,j],
             source_image_pixel_col_row=pixel,source_image_value=image.getpixel(tuple(pixel)),
             source_nav_occupancy=raw[i+j*w],native_coarse_size_m=cell,coarse_source_col_row=coarse,
             source_coarse_cell_in_support=truth_in_support,support_count=len(support),
             nearest_legal_center={k:float(nearest[k]) if k.endswith('_m') else int(nearest[k]) for k in ['col','row','x_m','y_m']},
             nearest_legal_center_distance_m=distance)
    if case=='B2':
        occ=WS/'NATIVE_PMFS_FULL20_20261014/derived/5d9684e340a6/OccupancyGrid3D.csv'
        data=lines(occ)
        minimum=list(map(float,data[0].split()[1:]))
        dims=list(map(int,data[2].split()[1:]))
        step=float(data[3].split()[1])
        nx,ny,nz=dims
        # Direct physical line addressing: z layers separated by ';'; x lines; y tokens.
        assert len(data[4:]) == nz*(nx+1)
        for z in range(nz):
            assert data[4+z*(nx+1)+nx].strip()==';'
            assert all(len(data[4+z*(nx+1)+x].split())==ny for x in range(nx))
        xyz=[math.floor((v-o)/step) for v,o in zip(src,minimum)]
        x,y,z=xyz
        line0=4+z*(nx+1)+x
        state=int(data[line0].split()[y])
        row['three_dimensional']=dict(path=str(occ),minimum_xyz=minimum,dimensions_xyz=dims,step_m=step,
             serialization='outer z; each line constant x; each token y; semicolon after every z layer',
             source_index_xyz=xyz,source_physical_line_1based=line0+1,source_token_1based=y+1,
             source_state=state,source_state_semantics='Free=0',
             source_z_interval=[minimum[2]+z*step,minimum[2]+(z+1)*step],
             vertical_column=[int(data[4+k*(nx+1)+x].split()[y]) for k in range(nz)],
             nav_y_origin_minus_3D_y_origin_m=origin[1]-minimum[1])
        assert state==0
    maps.append(row)

env_cpp=CACHE/'gaden_core/src/Environment.cpp'
env_hpp=CACHE/'gaden_core/include/gaden/Environment.hpp'
env_text=read(env_cpp).decode()
env_header=read(env_hpp).decode()
assert 'New line with constant x_idx and all the y_idx values' in env_text
assert re.search(r'for \(int height.*dimensions.z',env_text)
assert 'Free = 0' in env_header

def params(path):
    data=js(path)
    type_field={1:'bool_value',2:'integer_value',3:'double_value',4:'string_value',5:'byte_array_value',6:'bool_array_value',7:'integer_array_value',8:'double_array_value',9:'string_array_value'}
    return {k:v[type_field[v['type']]] for k,v in zip(data['names'],data['values']) if v['type'] in type_field}

clock=[]
for case,run in [('A2','PF24_A2_T02'),('B2','PF24_B2_Q01')]:
    rt=QUAL/'cases'/run/'runtime'
    gsl=params(rt/'resolved_GSL_parameters.json')
    basic=params(rt/'preflight_basic_sim_parameters.json')
    pid=params(rt/'preflight_PioneerP3DX_PID_parameters.json')
    wind=params(rt/'preflight_PioneerP3DX_Anemometer_parameters.json')
    player=params(rt/'preflight_gaden_player_parameters.json')
    rates=js(rt/'CLOCK_SENSOR_RATE_PREFLIGHT.json')
    assert gsl['use_sim_time'] is False and basic['speed']==5.0
    assert pid['use_sim_time'] is True and wind['use_sim_time'] is True
    assert player.get('use_sim_time',False) is False
    clock.append(dict(case=case,gsl={k:gsl.get(k) for k in ['use_sim_time','stop_and_measure_time','scale','useWindGroundTruth','sourceDiscriminationPower']},
        basic_sim={k:basic.get(k) for k in ['use_sim_time','speed','deltaTime']},
        sensors=dict(PID_use_sim_time=pid['use_sim_time'],anemometer_use_sim_time=wind['use_sim_time']),
        gaden_player={k:player.get(k) for k in ['use_sim_time','player_freq','initial_iteration','allow_looping','loop_from_iteration','loop_to_iteration']},
        recorded_preflight_rates=rates))

snippets=[]
def excerpt(path, start, end, scope):
    text=lines(path)
    snippets.append(dict(path=str(path),line_start=start,line_end=end,scope=scope,text='\n'.join(text[start-1:end])))

excerpt(env_cpp,125,170,'cached GADEN core parser; format evidence, not proof of 2024 dependency provenance')
excerpt(env_cpp,185,205,'cached GADEN core CSV writer')
excerpt(env_hpp,13,22,'cached GADEN state definitions')
excerpt(CONFIG/'launch/main_simbot_launch.py',43,68,'locked Sep18 official PMFS clock and scale')
excerpt(CONFIG/'launch/main_simbot_launch.py',128,139,'locked Sep18 BasicSim speed')
excerpt(CACHE/'basic_sim/src/BasicSim.cpp',25,63,'cached runtime robot clock equation')
excerpt(CACHE/'sensor_clock_source_audit/historical2024_simulation_player.cpp',117,143,'cached historical player wall-clock file loading and exclusive loop end')
excerpt(CACHE/'sensor_clock_source_audit/historical2024_fake_gas_sensor.cpp',72,83,'cached historical PID rate loop')
excerpt(CACHE/'sensor_clock_source_audit/historical2024_fake_anemometer.cpp',88,98,'cached historical anemometer rate loop')
excerpt(QUAL/'source_runtime/src/gsl_server/algorithms/Common/Algorithm.cpp',42,57,'actual PMFS startTime')
excerpt(QUAL/'source_runtime/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp',117,130,'actual result search_t')
excerpt(CACHE/'gaden_core/src/PlaybackSimulation.cpp',98,106,'current core advances post-load and resets only when currentIteration > inclusive endpoint')
excerpt(CACHE/'public_clock_player/simulation_player.cpp',393,408,'trace frame tests old/current frame against inclusive endpoint after Scene AdvanceTimestep')

player_receipt=js(WS/'PMFS_OFFICIAL_REPRO_AUDIT_20261016/paper_baseline_2024/PUBLIC_CLOCK_PLAYER_BUILD_RECEIPT.json')
player_bytes=read(CACHE/'public_clock_player/simulation_player.cpp')
cached_player_matches_build=hashlib.sha256(player_bytes).hexdigest()==player_receipt['source_sha256']
assert cached_player_matches_build
# A finite enumeration of the already-read branch logic, not a physical simulation.
historical=[]; frame=200
for _ in range(303):
    historical.append(frame)
    frame+=1
    if frame>=200: frame=100
modern=[]; next_load=200; tracker=200
for k in range(303):
    loaded=next_load
    next_load+=1
    if next_load>199: next_load=100
    if k>0:
        if tracker>=199: tracker=100
        else: tracker+=1
    assert tracker==loaded
    modern.append(loaded)
assert historical==modern
trace_checks=[]
for case_dir in [QUAL/'cases/PF24_A2_T02',ROOT/'cases/EA18_A2_R01',ROOT/'cases/EA18_A2_R02']:
    trace=case_dir/'runtime/physical_clock_trace.csv'
    read(trace)
    with trace.open(newline='') as f: rows=list(csv.DictReader(f))
    errors=[]
    for r in rows:
        elapsed=(int(r['receipt_ros_ns'])-int(r['anchor_ros_ns']))/1e9
        advances=math.floor((elapsed+1e-8)/0.5)
        expected_frame=200 if advances==0 else 100+(advances-1)%100
        if int(r['frame'])!=expected_frame:
            errors.append(dict(elapsed_s=elapsed,frame=int(r['frame']),expected_frame=expected_frame))
    transitions=[dict(previous=int(a['frame']),next=int(b['frame']),at_receipt_ros_ns=b['receipt_ros_ns']) for a,b in zip(rows,rows[1:]) if int(a['frame'])==199 and int(b['frame'])==100]
    assert not errors, errors[:3]
    trace_checks.append(dict(path=str(trace),rows=len(rows),observed_frames=sorted({int(r['frame'])for r in rows}),
            mismatches=errors,observed_199_to_100_count=len(transitions),transitions=transitions))
write('PLAYBACK_LOOP_ORDER_REVIEW.json',dict(
   official_yaml_end=200,official_historical_endpoint='exclusive after load then increment',
   adapter_parameter_end=199,adapter_core_endpoint='inclusive after load then increment',
   stable_loaded_sequence='initial 200 once, then repeat 100..199 inclusive',
   cached_player_source_sha_matches_build_receipt=cached_player_matches_build,
   finite_branch_enumeration_frames=len(historical),same_loaded_sequence=True,trace_checks=trace_checks,
   metadata_text_error='CASE_META.loop_equivalence_requirement says inclusive frame100..200; the code and effective cycle are initial200 once then100..199.',
   limitation='A trace with no 199->100 transition confirms only its observed elapsed-time range. Branch enumeration is source logic evidence, not a new runtime test or proof of the author paper runtime.'
))

from pypdf import PdfReader
read(PAPER)
reader=PdfReader(str(PAPER))
paper_pages=[]
for pdf_page in [12,13]:
    txt=reader.pages[pdf_page-1].extract_text()
    (OUT/f'final_paper_page_{pdf_page:02d}.txt').write_text(txt,encoding='utf-8')
    paper_pages.append(dict(pdf_page=pdf_page,printed_page=3550+pdf_page))
renderdir=OUT/'renders';renderdir.mkdir(exist_ok=True)
poppler=Path(r'C:\Users\50176\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
cmd=[str(poppler),'-f','12','-l','12','-scale-to','1600','-png','-singlefile',str(PAPER),str(renderdir/'final_paper_p12')]
result=subprocess.run(cmd,capture_output=True,text=True)
assert result.returncode==0,result.stderr
write('RENDER_COMMAND.json',dict(argv=cmd,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))

peer=js(ROOT/'analysis/OFFICIAL_SOURCE_MAP_AUDIT.json')
for actual, original in zip(maps,peer):
    assert actual['source_nav_occupancy']==original['fine_source_occupancy']
    assert abs(actual['nearest_legal_center_distance_m']-original['nearest_legal_coarse_distance_m'])<1e-12
read(ROOT/'analysis/CLOCK_ALIGNMENT_AUDIT.json')
write('INDEPENDENT_MAP_CLOCK_REVIEW.json',dict(
    created_utc=datetime.now(timezone.utc).isoformat(),scope='host-only read-only inspection of existing assets; no VM/build/ROS/simulation',
    verdict='CONFIRM_MAP_SERIALIZATION_AND_INHERITED_MULTI_CLOCK_WITH_LIMITS',
    official_commit=lock['commit'],official_tree=lock['tree'],official_files_verified=len(source_verification),
    map_results=maps,clock_results=clock,paper_pages=paper_pages,
    limitations=[
      'The 3D CSV is a locally generated world, not an author-published original experimental trajectory. Cached GADEN parser/writer confirm serialization, not a proof of the exact 2024 dependency commit.',
      'Final paper Fig12 explicitly concerns B2 3D airflow; it does not say the 2D source cell was excluded, nor quantify exclusion as the cause of current errors.',
      'Nearest legal source support is about 0.2483m away; support exclusion alone does not establish the cause of 4.366m declaration error.',
      'Mixed clocks are present in locked official launch. Paper does not pin exact runtime clock semantics or 30 trial seeds. Do not scale reported search time by five and call it a reproduction.',
      'Fig11 explicitly prints A2=87.0s and B2=110.5s (one decimal place). These are published 30-trial means, not available raw trial times. No runtime clock equivalence has been established.',
      'A2 endpoint parameter translation200->199 is justified by historical exclusive vs current core inclusive order; CASE_META wording inclusive100..200 is misleading. See PLAYBACK_LOOP_ORDER_REVIEW.json for actual trace coverage.',
      'This independent review adds no experimental repetitions and does not qualify S2 or prove the 2024 paper was exactly reproduced.'
    ]))
write('OFFICIAL_BLOB_VERIFICATION.json',source_verification)
write('SOURCE_EXCERPTS.json',snippets)
write('INPUT_SHA256.json',inventory)
print(json.dumps(dict(verdict='CONFIRM_WITH_LIMITS',official_files=len(source_verification),map_results=maps,clock_summary=[dict(case=c['case'],gsl=c['gsl'],speed=c['basic_sim']['speed'])for c in clock]),ensure_ascii=False))
