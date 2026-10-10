from common import *
import gzip,tarfile,hashlib,csv
code=r'''
import tarfile,bisect,csv,hashlib,shutil,subprocess
assert json.loads((t/'remaining_QUERY_LEDGER.json').read_text())['status'].startswith('PASS')
include=['frozen_contract.json','PRE_QUERY_OBSERVATION_CONTRACT.json','FROZEN_RECEPTOR_SCHEDULE.csv','FROZEN_INPUT.csv','FROZEN_METADATA.json',
 'pristine_MathUtils.hpp','include/gaden/internal/MathUtils.hpp','RNG_LIBRARY_BUILD_RESULT.json','RNG_LIBRARY_BUILD_COMMANDS.json','RNG_LIBRARY_LINK_COMMAND.json',
 'rng_library_build.log','rng_library_build_link_failure.log','rng_library_link_fix.log',
 'query_native.cpp','query_build.log','query_build_first_missing_include.log','QUERY_BUILD_COMMAND.json','QUERY_BUILD_RESULT.json',
 'ORIGINAL_NATIVE_QUERY.csv','original_query.log','SMOKE_QUALIFICATION.json',
 'smoke_GENERATION_LEDGER.json','remaining_GENERATION_LEDGER.json','smoke_QUERY_LEDGER.json','remaining_QUERY_LEDGER.json',
 'smoke_worker.stdout','smoke_worker.stderr','remaining_worker.stdout','remaining_worker.stderr',
 'smoke_query_worker.stdout','smoke_query_worker.stderr','remaining_query_worker.stdout','remaining_query_worker.stderr']
include += [p.relative_to(t).as_posix() for p in (t/'realizations').rglob('*') if p.is_file() and '/bank/' not in p.as_posix()]
selected=[]
for root in sorted((t/'realizations').iterdir()):
 lineage=list(csv.DictReader((root/'QUERY_PHYSICAL_LINEAGE.csv').open()))
 for frame in sorted({int(r['selected_frame']) for r in lineage}):
  name=(root/'bank'/('iteration_'+str(frame))).relative_to(t).as_posix();include.append(name);selected.append(name)
include=list(dict.fromkeys(include));assert len(selected)==8*49
protected=[]
old=Path('/home/zyc/pmfs_b4_native_validation_20261009')
for path in [old/'B4_generation_RESOLVED.yaml',old/'derived_B4/OccupancyGrid3D.csv',old/'PHYSICAL_FRAME_TIME.csv',
             Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/src/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp')]:
 protected.append(dict(path=str(path),SHA256=hashlib.sha256(path.read_bytes()).hexdigest()))
q=dict(status='ALL_EIGHT_CAPTURED_SERIAL_NO_RETRY',selected_query_frames=len(selected),all_generated_frames=8*1803,
      full_banks_retained_on_original_VM=True,full_banks_not_needed_for_review_queries=True,
      complete_snapshot_time_and_SHA_tables_included=True,
      task_disk_bytes=sum(p.stat().st_size for p in t.rglob('*') if p.is_file()),home_free_bytes=shutil.disk_usage(t).free,
      protected_hashes=protected,source_blind_score_not_yet_computed=True,
      generation_total_wall_s=sum(json.loads(p.read_text())['generation_wall_s'] for p in (t/'realizations').glob('*/GENERATION_QUALIFICATION.json')),
      query_total_wall_s=sum(json.loads(p.read_text())['query_wall_s'] for p in (t/'realizations').glob('*/QUERY_QUALIFICATION.json')))
(t/'EIGHT_REFERENCE_CAPTURE_SUMMARY.json').write_text(json.dumps(q,indent=2));include.append('EIGHT_REFERENCE_CAPTURE_SUMMARY.json')
archive=t/'M2_RAW_REFERENCE_QUERY_EVIDENCE.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz') as a:
 for name in include:a.add(t/name,arcname=name,recursive=False)
q.update(archive_bytes=archive.stat().st_size,archive_SHA256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=len(include));print(json.dumps(q,indent=2))
'''
result=json.loads(run('from pathlib import Path\nimport json\nt=Path('+repr(REMOTE)+')\n'+code,'COLLECT_EIGHT_REFERENCE_RESULTS',90))
c=json.loads(CONNECTION.read_text(encoding='utf-8'));local=W/'M2_RAW_REFERENCE_QUERY_EVIDENCE.tar.gz'
args=['scp','-q','-i',c['key'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
      '-o','UserKnownHostsFile='+c['known_hosts'],c['target']+':'+REMOTE+'/M2_RAW_REFERENCE_QUERY_EVIDENCE.tar.gz',str(local)]
r=subprocess.run(args,capture_output=True,timeout=120);assert r.returncode==0,r.stderr
assert hashlib.sha256(local.read_bytes()).hexdigest()==result['archive_SHA256']
destination=OUT/'native_reference_evidence';assert not destination.exists();destination.mkdir()
with tarfile.open(local) as a:
    for item in a.getmembers():assert (destination/item.name).resolve().is_relative_to(destination.resolve()) and item.isfile()
    a.extractall(destination)
(OUT/'EIGHT_REFERENCE_CAPTURE_SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
