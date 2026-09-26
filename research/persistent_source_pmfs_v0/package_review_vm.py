#!/usr/bin/env python3
import hashlib, shutil, zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[2]
stage=Path('/home/zyc/PERSISTENT_SOURCE_PMFS_R1_REVIEW_20260926')
archive=Path('/home/zyc/PERSISTENT_SOURCE_PMFS_R1_REVIEW_20260926.zip')
assert not stage.exists() and not archive.exists(), 'refuse package overwrite'
first=Path('/home/zyc/persistent_source_pmfs_r1_20260926')
repeat=Path('/home/zyc/persistent_source_pmfs_r1_repeat_20260926')
assert (first/'truth_evaluation.json').is_file() and (first/'DECISION.md').is_file()
assert (first/'candidate_summary.csv').read_bytes()==(repeat/'candidate_summary.csv').read_bytes()
stage.mkdir()
shutil.copytree(first,stage/'result')
shutil.copytree(repeat,stage/'deterministic_repeat')
shutil.copytree('/home/zyc/persistent_source_r1_source_blind_20260926',stage/'source_blind_inputs')
shutil.copytree(root/'research/persistent_source_pmfs_v0',stage/'execution_code')
(stage/'binary').mkdir()
shutil.copyfile('/home/zyc/persistent_source_pmfs_build_20260926/persistent_source_r1_replay',stage/'binary/persistent_source_r1_replay')
shutil.copyfile(root/'ros2_package/CMakeLists.txt',stage/'execution_code/CMakeLists.txt')
shutil.copyfile('/home/zyc/persistent_source_build_20260926.log',stage/'build.log')
shutil.copyfile('/home/zyc/persistent_source_run_20260926.log',stage/'source_blind_execution.log')
shutil.copyfile('/home/zyc/persistent_source_truth_20260926.json',stage/'frozen_historical_truth.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in stage.rglob('*') if p.is_file())
(stage/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(stage).as_posix()}\n' for p in files))
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file(): z.write(p,p.relative_to(stage).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(f'archive={archive}\nbytes={archive.stat().st_size}\nsha256={sha(archive)}')
