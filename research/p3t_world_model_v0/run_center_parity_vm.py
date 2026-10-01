"""Export exact R1 centers; compare all map/score bytes before Gaussian evaluation."""
import hashlib,json,subprocess,time
from pathlib import Path
out=Path('/mnt/hgfs/workspace/P3T_D0_CENTERS_20261001');out.mkdir(exist_ok=False)
ref=Path('/mnt/hgfs/workspace/PMFS3D_R1_SCIENTIFIC_20261001/repeat1')
inputs=Path('/mnt/hgfs/workspace/PMFS3D_R1_AUDIT_20261001/replay_inputs')
binary=Path('/mnt/hgfs/workspace/P3T_D0_EXPORT_BUILD_20261001/oracle_forward')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[];traj=[]
for case in ['House01_seed0_off_off','House01_seed1_off_off','House02_seed0_off_off','House02_seed1_off_off']:
 for arm in ['oracle2d','oracle3d']:
  dest=out/case/arm;t=time.perf_counter()
  subprocess.run([str(binary),str(inputs/case),str(inputs/case/'config.csv'),arm,str(dest)],check=True)
  pairs=[]
  for p in sorted((dest/'maps').glob('*.f32'))+[dest/'candidate_log_scores.csv']:
   rp=ref/case/arm/p.relative_to(dest);h=sha(p);rh=sha(rp)
   pairs.append({'file':str(p.relative_to(out)),'sha256':h,'r1_sha256':rh,'match':h==rh})
  assert all(r['match'] for r in pairs),'R1 parity failure'
  records.append({'case':case,'arm':arm,'files':pairs,'runtime_seconds':time.perf_counter()-t})
  for p in sorted((dest/'trajectories').glob('*.trajbin')):traj.append({'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p)})
  print('PARITY_PASS',case,arm,flush=True)
(out/'P0_TRAJECTORY_PARITY.json').write_text(json.dumps({'pass':True,'records':records,'trajectory_files':len(traj),'trajectory_bytes':sum(r['bytes'] for r in traj),'new_gaden':0},indent=2,sort_keys=True)+'\n')
(out/'CENTER_SHA256.json').write_text(json.dumps(traj,indent=2,sort_keys=True)+'\n')
