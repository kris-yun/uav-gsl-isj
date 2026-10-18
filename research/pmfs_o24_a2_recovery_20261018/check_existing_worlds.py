from pathlib import Path
import csv,hashlib,json,shutil,time
R=Path(__file__).resolve().parent;PROJECT=R.parents[1];start=time.monotonic();proof=[]
for case,world in [('A2','NATIVE_PMFS_WIND_RECOVERY_20261014'),('B2','NATIVE_PMFS_FULL20_20261014')]:
 root=PROJECT/'workspace'/world/'cases'/case;manifest=root/'ALL_FRAME_SHA256_AND_TIME.csv';a=list(csv.DictReader(manifest.open()));total=0
 for row in a:
  p=root/'one_realization'/('iteration_'+row['frame']);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];total+=len(b)
 proof.append(dict(case=case,world=str(root),frames=len(a),bytes_checked=total,manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),original_author_raw_experiment=False))
 dst=R/'world_provenance'/case;dst.mkdir(parents=True,exist_ok=True)
 for name in ['CASE_META.json','WORLD_QA.json','ALL_FRAME_SHA256_AND_TIME.csv','PHYSICAL_FRAME_TIME.csv','generation.yaml','WIND_GENERATION_GATE.json']:
  if (root/name).exists():shutil.copyfile(root/name,dst/name)
(R/'WORLD_INPUT_GATE.json').write_text(json.dumps(dict(status='PASS_BOTH_EXISTING_WORLD_ALL_FRAME_SHA256',rows=proof,wall_s=time.monotonic()-start,new_worlds=0),indent=2))
print(json.dumps(dict(status='PASS_BOTH_EXISTING_WORLD_ALL_FRAME_SHA256',frames=sum(r['frames']for r in proof),wall_s=time.monotonic()-start)))
