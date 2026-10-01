"""Compact evidence manifest and review packaging. Does not modify experiment assets."""
import hashlib,json,subprocess,tarfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[2];e=root/'evidence/p3t_d0_gaussian_support_20261001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tarfile.open(e/'point_controls.tar.gz','w:gz') as t:t.add(e/'point_controls',arcname='point_controls')
for name in ['DETERMINISTIC_REPEAT.json','RUNTIME.json','INDEPENDENT_QUERY_AUDIT.json']:(e/name).write_bytes((e/'gaussian_outputs'/name).read_bytes())
archive=Path(r'C:\GADEN_P3T_D0_ARCHIVE\20261001\P3T_D0_CENTERS_20261001.tar.zst')
assert archive.stat().st_size==913053466
assert sha(archive)=='13948d43b4a88b68ea9161292a062ed2bec59a6461ed7101d87bd65ed962064c'
(e/'FULL_CENTER_ARCHIVE.json').write_text(json.dumps(dict(host_path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),vm_original_preserved=True,deleted_raw_files=0,original_uncompressed_center_bytes=1856043320,vm_path='/mnt/hgfs/workspace/P3T_D0_CENTERS_20261001.tar.zst'),indent=2,sort_keys=True)+'\n',encoding='utf-8')
(e/'REVIEW_README.md').write_text('''# P3T-D0 review

Read P3T_D0_DECISION.md, P3T_D0_RESULT.json and INDEPENDENT_D0_AUDIT.json first. Decision STOP, no D1. Four-arm table is fully reported.

point_controls.tar.gz: all frozen R1 P2/P3 maps and scores. gaussian_outputs.tar.gz: all G2/G3 maps, continuous means/maxima/nonzero fractions, scores, diagnostics, repeat1/repeat2 and timing. P3T_D0_TRUTH_CENTER_AND_OCCUPANCY.tar.gz: eight true-leaf center trajectories and original two House occupancy grids. physical_provenance/provenance.tar.gz: frozen source/config/header copies. CENTER_SHA256.json and FULL_CENTER_ARCHIVE.json locate the separately retained 913 MB full bank. It is intentionally omitted from compact review.

All concentration values are ppm; coordinates meters; sigma centimeters. trajbin: 200 frames, each uint32 little-endian count then count packed records (3 float32 xyz, 1 float64 age_seconds). No padding or object IDs; order preserves per-frame active list. Hit maps little-endian float32, indexed by cell_index in corresponding measured_hit_probability.csv. Original occupancy text uses z planes, x rows, y columns.

Source code under research/p3t_world_model_v0; isolated build helper under research/pmfs3d_r1. Small measured inputs plus Native configs retained under inputs/. SHA256SUMS covers all compact evidence files except itself. No simulator or live ROS required to recompute scores from maps. No new GADEN, training, H03, confirmation or closed loop.
''',encoding='utf-8')
files=[p for p in sorted(e.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt' and not any(x in p.relative_to(e).parts for x in ['sources','gaussian_outputs','point_controls'])]
(e/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(e).as_posix()+'\n' for p in files),encoding='utf-8')
print('COMPACT_EVIDENCE_FILES',len(files),'BYTES',sum(p.stat().st_size for p in files))
