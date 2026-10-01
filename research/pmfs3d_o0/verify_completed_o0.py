"""Read-only verification and small evidence export. Never invokes simulation."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

ap=argparse.ArgumentParser()
ap.add_argument('--repo-root',type=Path,required=True)
ap.add_argument('--work-root',type=Path,required=True)
a=ap.parse_args(); root=a.repo_root; work=a.work_root
out=root/'evidence/pmfs3d_o0_projected2d_20261001'
script=root/'research/pmfs3d_o0/pmfs3d_o0_projected2d_gate.py'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('gate',script)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
original=subprocess.check_output(['git','show','a8270ec1d7959259b8bbfd34d2b32b3cdbeb39e4:research/pmfs3d_o0/pmfs3d_o0_projected2d_gate.py'],cwd=root,text=True)
def functions(text):
    return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(text).body if isinstance(node,ast.FunctionDef)}
before=functions(original); after=functions(script.read_text())
for name in ('profile','affinity','evaluate'):
    assert before[name]==after[name], name
bank=root/'evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank'
first=m.evaluate(bank,work/'projected2d_runs')
second=m.evaluate(bank,work/'projected2d_runs')
serial=lambda obj:json.dumps(obj,indent=2,sort_keys=True)+'\n'
assert serial(first)==serial(second)
result=json.loads((out/'O0_RESULT.json').read_text())
assert all(result[k]==first[k] for k in first)
manifest=json.loads((work/'projected2d_wind/projection_manifest.json').read_text())
assert len(manifest['records'])==11
for row in manifest['records']:
    assert digest(Path(row['input']))==row['input_sha256']
    assert digest(Path(row['output']))==row['output_sha256']
    assert row['max_abs_w']==0 and row['uv_source_slice_preserved']
raw=[]
for i,name in enumerate(('S1_A','S1_B','S2_A','S2_B')):
    run=work/'projected2d_runs'/name
    preservation=json.loads((run/'RAW_PRESERVATION.json').read_text())
    retained=Path(preservation['retained'])
    assert len(list(retained.glob('iteration_*')))==566
    for row in preservation['files']:
        file=retained/row['path']
        assert file.stat().st_size==row['bytes'] and digest(file)==row['sha256']
    assert digest(run/'concentration.npy')==result['generated_projected_runs'][i]['cube_sha256']
    assert digest(run/'generation.log')==result['generated_projected_runs'][i]['generation_log_sha256']
    assert digest(run/'extract.log')==result['generated_projected_runs'][i]['extract_log_sha256']
    exported=out/'projected_candidates'/name; exported.mkdir(parents=True,exist_ok=True)
    for file in run.iterdir():
        if file.is_file(): shutil.copyfile(file,exported/file.name)
    raw.append({'run':name,'retained':str(retained),'files':len(preservation['files']),
                'iteration_files':566,'bytes':preservation['total_bytes'],
                'generation_completion_markers':(run/'generation.log').read_text().count('Filament simulator finished correctly!')})
verification={'decision':'O0_COMPLETED_EVIDENCE_VERIFIED',
              'same_frozen_profile_affinity_evaluate_ast':True,
              'evaluation_repeat_byte_identical':True,'repeat_sha256':hashlib.sha256(serial(first).encode()).hexdigest(),
              'recomputed_result_exactly_matches_saved':True,'projection_files_hash_verified':11,
              'successful_gaden_runs':4,'simulation_reruns':0,'raw_retention':raw,
              'all_original_wind_hashes_unchanged':True}
(out/'POST_RUN_VERIFICATION.json').write_text(serial(verification))
(out/'O0_SCORE_REPEAT.json').write_text(serial(first))
print(serial(verification))
