"""Fixed two-pass on-demand G2/G3 evaluation. No truth or rank access."""
import hashlib,json,subprocess,time
from pathlib import Path
root=Path('/mnt/hgfs/workspace/P3T_D0_GAUSSIAN_OUTPUT_20261001');root.mkdir(exist_ok=False)
bank=Path('/mnt/hgfs/workspace/P3T_D0_CENTERS_20261001')
inputs=Path('/mnt/hgfs/workspace/PMFS3D_R1_AUDIT_20261001/replay_inputs')
binary=Path('/mnt/hgfs/workspace/P3T_D0_GAUSSIAN_BUILD_20261001/oracle_forward')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((bank/'CENTER_SHA256.json').read_text())
for row in frozen:assert sha(bank/row['path'])==row['sha256'],'center bank changed'
runtime=[]
for repeat in ['repeat1','repeat2']:
 for case in ['House01_seed0_off_off','House01_seed1_off_off','House02_seed0_off_off','House02_seed1_off_off']:
  for arm,transport in [('g2','oracle2d'),('g3','oracle3d')]:
   dest=root/repeat/case/arm;t=time.perf_counter()
   timefile=root/(repeat+'_'+case+'_'+arm+'_time.txt')
   subprocess.run(['/usr/bin/time','-v','-o',str(timefile),str(binary),str(inputs/case),str(inputs/case/'config.csv'),arm,str(dest),str(bank/case/transport)],check=True)
   runtime.append(dict(repeat=repeat,case=case,arm=arm,wall_seconds=time.perf_counter()-t,time_output=timefile.read_text()))
   print('GAUSSIAN_COMPLETE',repeat,case,arm,runtime[-1]['wall_seconds'],flush=True)
   (root/'RUNTIME.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n')
pairs=[]
for p in sorted((root/'repeat1').rglob('*')):
 if p.is_file():
  rel=p.relative_to(root/'repeat1');q=root/'repeat2'/rel;h=sha(p);other=sha(q)
  pairs.append(dict(path=str(rel),sha256=h,repeat2_sha256=other,match=h==other))
assert len(list((root/'repeat2').rglob('*.f32')))==len(list((root/'repeat1').rglob('*.f32')))
assert all(row['match'] for row in pairs),'repeat not byte-identical'
(root/'DETERMINISTIC_REPEAT.json').write_text(json.dumps(dict(pass_=True,files=len(pairs),pairs=pairs),indent=2,sort_keys=True)+'\n')
print('DETERMINISTIC_REPEAT_PASS',len(pairs),flush=True)
