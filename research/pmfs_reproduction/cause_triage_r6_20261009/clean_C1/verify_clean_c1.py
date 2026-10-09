"""Verify shipped C1 samples/time axis; optionally every frame in a local raw bank.
python verify_clean_c1.py [--bank /path/to/one_realization_C1]
Standard library only. Reads data, never launches a program or writes the bank.
"""
from pathlib import Path
import argparse,csv,hashlib,json,struct,zlib
parser=argparse.ArgumentParser();parser.add_argument('--bank');args=parser.parse_args()
p=Path(__file__).resolve().parent
q=json.loads((p/'CLEAN_C1_QUALIFICATION.json').read_text())
geometry=json.loads((p/'PRE_GENERATION_QUALIFICATION.json').read_text())
with (p/'ALL_FRAME_SHA256_AND_TIME.csv').open() as f:rows=list(csv.DictReader(f))
assert len(rows)==q['frames']==1803 and [int(r['frame']) for r in rows]==list(range(1803))
times=[float(r['save_call_internal_time_s']) for r in rows];winds=[int(r['wind_index']) for r in rows]
assert all(b>a for a,b in zip(times,times[1:])) and all(b>=a for a,b in zip(winds,winds[1:]))
assert set(winds)==set(range(11)) and winds[-1]==10
assert abs(times[500]-q['frame_500_save_call_time_s'])<1e-9 and abs(times[-1]-q['physical_save_call_time_last_s'])<1e-9
assert not q['actual_cadence_exact_half_second']
files=sorted(Path(args.bank).glob('iteration_*'),key=lambda f:int(f.name.split('_')[1])) if args.bank else sorted((p/'sample_frames').glob('iteration_*'))
if args.bank:assert len(files)==len(rows)
for f in files:
    index=int(f.name.split('_')[1]);r=rows[index];data=f.read_bytes()
    assert hashlib.sha256(data).hexdigest()==r['sha256'],f.name
    assert data.startswith(b'GADEN_RESULT\0') and data[13]==1
    raw=zlib.decompress(data[22:]);assert struct.unpack_from('<II',raw)==(3,0)
    assert struct.unpack_from('<3i',raw,8)==tuple(geometry['grid_dimensions'])
    assert all(abs(a-b)<1e-6 for a,b in zip(struct.unpack_from('<3f',raw,20),geometry['grid_minimum']))
    offset=56+struct.unpack_from('<Q',raw,48)[0]
    source=struct.unpack_from('<3f',raw,offset);gas=struct.unpack_from('<i',raw,offset+12)[0];wind=struct.unpack_from('<i',raw,offset+24)[0]
    assert all(abs(a-b)<1e-6 for a,b in zip(source,[0,-1,.2])) and gas==10 and wind==int(r['wind_index'])
parameters=json.loads((p/'PARAMETER_BINDING_PRISTINE.json').read_text())
assert parameters['temperature']==298 and parameters['pressure']==1 and parameters['allow_looping'] is False
assert json.loads((p/'GENERATION_RESULT.json').read_text())['generation_executions']==1
lock=json.loads((p/'PRISTINE_CORE_DEPENDENCY_LOCK.json').read_text())
assert lock[0]['commit']=='1a20e35cd5f174ae9675a2ae3c796137a05c4ee5'
math_source=(p/'pristine_MathUtils.hpp').read_text(encoding='utf-8')
assert 'configuredSeed' not in math_source and 'static thread_local std::mt19937 engine;' in math_source
print(json.dumps(dict(verdict='C1_SAMPLE_AND_TIME_AXIS_VERIFIED',frames_in_registry=len(rows),raw_frames_checked=len(files),
    wind_loop=False,source_gas_PASS=True,official_core_dependency_PASS=True,
    physical_save_call_time_frame500_s=times[500],native_player_equals_physical_clock='HOLD')))
